# Screenkey: persist self.data (LabelManager keystroke buffer) to local file.
#
# This module is a standalone patch. It does NOT modify any existing
# source files; instead, at import-time it monkey-patches the
# ``LabelManager`` class so that every mutation of ``self.data`` (the
# in-memory list of KeyData / ButtonData items) is also written to a
# JSON Lines log on disk.
#
# The patch is safe to load more than once (idempotent).  The output
# path can be overridden by the ``SCREENKEY_DATA_FILE`` environment
# variable; otherwise it defaults to::
#
#     $XDG_DATA_HOME/screenkey/keystrokes-<startup-ts>.jsonl
#
# File format (JSON Lines, one JSON record per line):
#   {"ts": <iso8601>, "type": "init"}
#   {"ts": ...,         "type": "append",  "index": 3,
#    "stamp": ..., "is_ctrl": false, "bk_stop": false,
#    "silent": false,  "spaced": false,  "markup": "a"}
#   {"ts": ...,         "type": "pop",     "count": 1}
#   {"ts": ...,         "type": "clear"}
#   {"ts": ...,         "type": "screen",  "synthetic": false,
#    "markup": "<u>hi</u>",  "text": "hi"}     # screen snapshot (deduped)
#
# The "screen" record is the compromise format:
#   * ``markup`` is the exact Pango markup string shown on screen (lossless)
#   * ``text``    is the human-readable plain text (tags + invisible
#                 separators stripped) -- safe to ``jq -r '.text'``
# Consecutive identical snapshots are collapsed to avoid one row per
# keystroke; a snapshot is only emitted when the on-screen text changes.
#

from __future__ import annotations

import json
import os
import re
import threading
from datetime import datetime, timezone
from typing import Optional

try:
    from gi.repository import GLib as _GLib
except Exception:  # pragma: no cover - non-GTK environments (e.g. local tests)
    _GLib = None

try:
    from gi.repository import Pango as _Pango
except Exception:  # pragma: no cover - non-GTK environments (e.g. local tests)
    _Pango = None

from .labelmanager import LabelManager, KeyData


# ---------------------------------------------------------------------------
# Pango markup -> plain text
# ---------------------------------------------------------------------------

# Invisible separators inserted by LabelManager.update_text() to disable
# ligatures and to fine-tune spacing.  They must be stripped when producing
# a human-readable text view, otherwise the output is full of zero-width
# noise.
_INVISIBLE_CHARS = (
    "\u200b"  # ZERO WIDTH SPACE
    "\u200c"  # ZERO WIDTH NON-JOINER  (used heavily by screenkey)
    "\u200d"  # ZERO WIDTH JOINER
    "\u200a"  # HAIR SPACE
    "\u2009"  # THIN SPACE
    "\u180e"  # MONGOLIAN VOWEL SEPARATOR (used as ZWNJ workaround)
    "\ufeff"  # ZERO WIDTH NO-BREAK SPACE
)

# Fallback regex used when Pango is unavailable: strips any ``<tag ...>``
# fragment.  Pango markup is simple enough that this works in practice, but
# the Pango-based parser is always preferred when available because it
# correctly handles entity escapes (&amp;, &lt;, &#1234;, ...).
_TAG_RE = re.compile(r"<[^>]+>")


def _markup_to_text(markup: Optional[str]) -> str:
    """Convert a Pango markup string to plain readable text.

    Falls back to a regex-based stripper when Pango is unavailable (e.g.
    during local non-GTK testing).  Never raises.
    """
    if not markup:
        return ""
    if isinstance(markup, bytes):
        try:
            markup = markup.decode("utf-8")
        except Exception:
            return ""

    text = markup
    if _Pango is not None:
        try:
            ok, _attr, parsed, _accel = _Pango.parse_markup(markup, -1, "\0")
            if ok:
                text = parsed
        except Exception:
            pass  # fall through to regex

    # Always strip the invisible separators screenkey inserts, regardless
    # of which parser produced ``text``.  Do this last so it also cleans
    # up any stray characters left by the regex fallback.
    if text:
        for ch in _INVISIBLE_CHARS:
            if ch in text:
                text = text.replace(ch, "")
        # If Pango was unavailable, also strip remaining tags
        if _Pango is None and "<" in text:
            text = _TAG_RE.sub("", text)
        # Unescape common XML entities (regex fallback path only, but
        # cheap to run unconditionally)
        if "&" in text:
            text = (text.replace("&amp;", "&")
                        .replace("&lt;", "<")
                        .replace("&gt;", ">")
                        .replace("&quot;", '"')
                        .replace("&apos;", "'"))
    return text


# ---------------------------------------------------------------------------
# Output path resolution
# ---------------------------------------------------------------------------

def _get_user_data_dir() -> str:
    """Return the XDG data dir, matching GLib.get_user_data_dir() semantics.

    Falls back to a pure ``os.environ`` implementation when GI/GLib is
    unavailable (e.g. during local non-GTK testing).
    """
    if _GLib is not None:
        return _GLib.get_user_data_dir()
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return xdg
    return os.path.expanduser("~/.local/share")


def _default_output_path() -> str:
    base = _get_user_data_dir()
    dir_ = os.path.join(base, "screenkey")
    os.makedirs(dir_, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return os.path.join(dir_, f"keystrokes-{ts}.jsonl")


def _resolve_output_path() -> Optional[str]:
    env_val = os.environ.get("SCREENKEY_DATA_FILE")
    if env_val == "":  # explicitly disabled
        return None
    if env_val:
        parent = os.path.dirname(os.path.abspath(env_val))
        if parent:
            os.makedirs(parent, exist_ok=True)
        return env_val
    try:
        return _default_output_path()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# File writer (thread-safe)
# ---------------------------------------------------------------------------

class _DataFileWriter:
    def __init__(self, path: str, logger=None):
        self._path = path
        self._logger = logger
        # RLock is required because close() holds the lock while it calls
        # _emit() which also needs the same lock (would deadlock with a
        # plain non-reentrant Lock).
        self._lock = threading.RLock()
        self._fh = open(path, "a", encoding="utf-8", buffering=1)  # line-buffered
        # Last screen snapshot, used for deduplication.  We compare both
        # ``markup`` (raw) and ``text`` (parsed) so that a change which
        # only affects invisible separators still counts as "unchanged"
        # from the user's perspective.
        self._last_screen_markup = None
        # opening banner
        self._emit({"type": "init", "path_hint": path})

    @property
    def path(self) -> str:
        return self._path

    def _emit(self, record: dict) -> None:
        record = {"ts": datetime.now(timezone.utc).isoformat(), **record}
        with self._lock:
            self._fh.write(json.dumps(record, ensure_ascii=False))
            self._fh.write("\n")
            self._fh.flush()

    # ---- record helpers ------------------------------------------------

    def append_item(self, index: int, item: KeyData) -> None:
        try:
            stamp_iso = item.stamp.isoformat() if hasattr(item.stamp, "isoformat") else str(item.stamp)
            markup = item.markup
            if isinstance(markup, bytes):
                markup = markup.decode("utf-8", errors="replace")
            self._emit({
                "type": "append",
                "index": index,
                "stamp": stamp_iso,
                "is_ctrl": bool(item.is_ctrl),
                "bk_stop": bool(item.bk_stop),
                "silent": bool(item.silent),
                "spaced": bool(item.spaced),
                "markup": markup,
            })
        except Exception as exc:  # never crash screenkey because of logging
            if self._logger is not None:
                self._logger.debug("persist patch: failed to write append record: %s", exc)

    def pop_items(self, count: int) -> None:
        if count <= 0:
            return
        self._emit({"type": "pop", "count": int(count)})

    def clear(self) -> None:
        self._emit({"type": "clear"})
        # After a clear the on-screen text will become empty; reset the
        # dedup baseline so the next (possibly also empty) snapshot is
        # still emitted as a real transition.
        self._last_screen_markup = None

    def screen_snapshot(self, markup, synthetic: bool = False) -> None:
        """Emit a deduped on-screen snapshot record.

        Consecutive calls with the same ``markup`` are collapsed.  The
        record always contains both ``markup`` (lossless Pango source)
        and ``text`` (human-readable, tags + invisible separators
        stripped).
        """
        try:
            if isinstance(markup, bytes):
                markup = markup.decode("utf-8", errors="replace")
            # Deduplicate against the previous snapshot.  We compare on
            # the raw markup string: that catches both genuine content
            # changes and Pango tag changes (e.g. the <u> underline that
            # marks recent keystrokes).
            if markup == self._last_screen_markup:
                return
            text = _markup_to_text(markup)
            self._emit({
                "type": "screen",
                "synthetic": bool(synthetic),
                "markup": markup if markup is not None else "",
                "text": text,
            })
            self._last_screen_markup = markup
        except Exception as exc:  # never crash screenkey because of logging
            if self._logger is not None:
                self._logger.debug("persist patch: failed to write screen snapshot: %s", exc)

    def close(self) -> None:
        try:
            with self._lock:
                if not self._fh.closed:
                    self._emit({"type": "shutdown"})
                    self._fh.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Monkey-patch installation (idempotent)
# ---------------------------------------------------------------------------

_PATCH_ATTR = "_persist_data_patch_applied"
_WRITER_ATTR = "_persist_data_writer"
_LASTLEN_ATTR = "_persist_last_len"
_LOGGER_ATTR = "_persist_logger"


def _iso_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def install(logger=None) -> bool:
    """Apply the persistence patch to ``LabelManager``.

    Returns True if the patch was applied during this call, False if it
    was already active.
    """
    if getattr(LabelManager, _PATCH_ATTR, False):
        return False

    # ------------------------------------------------------------------
    # Save the original methods
    # ------------------------------------------------------------------
    orig_init = LabelManager.__init__
    orig_clear = LabelManager.clear
    orig_update_text = LabelManager.update_text
    orig_del = LabelManager.__del__ if hasattr(LabelManager, "__del__") else None

    # ------------------------------------------------------------------
    # Patched __init__
    #   - resolve output path and create a writer
    #   - initialise the length-tracking state
    # ------------------------------------------------------------------
    def patched_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)

        # Pull logger from instance (if provided via kwargs or arg);
        # ``logger`` is always passed positionally or via kwarg.
        inst_logger = getattr(self, "logger", logger)
        setattr(self, _LOGGER_ATTR, inst_logger)

        out_path = _resolve_output_path()
        if out_path is not None:
            try:
                writer = _DataFileWriter(out_path, inst_logger)
            except Exception as exc:
                if inst_logger is not None:
                    inst_logger.debug("persist patch: cannot open %s for writing: %s",
                                      out_path, exc)
                writer = None
        else:
            writer = None

        setattr(self, _WRITER_ATTR, writer)
        setattr(self, _LASTLEN_ATTR, len(self.data))

        if writer is not None and inst_logger is not None:
            inst_logger.info("persist patch: keystroke data will be saved to %s",
                             writer.path)

    # ------------------------------------------------------------------
    # Patched clear()
    #   - emit a "clear" record, then reset the length counter
    # ------------------------------------------------------------------
    def patched_clear(self, *args, **kwargs):
        writer = getattr(self, _WRITER_ATTR, None)
        if writer is not None:
            writer.clear()
        setattr(self, _LASTLEN_ATTR, 0)
        return orig_clear(self, *args, **kwargs)

    # ------------------------------------------------------------------
    # Patched update_text()
    #   - called *after* self.data has already been mutated, so we diff
    #     the current length vs the previously remembered length and
    #     emit append / pop records accordingly
    #   - we also temporarily wrap ``self.label_listener`` so that the
    #     markup string produced by the original update_text() is captured
    #     and written as a deduped "screen" snapshot record
    # ------------------------------------------------------------------
    def patched_update_text(self, *args, **kwargs):
        writer = getattr(self, _WRITER_ATTR, None)
        if writer is not None:
            last_len = getattr(self, _LASTLEN_ATTR, 0)
            cur_len = len(self.data)

            if cur_len > last_len:
                # append case: only new items (data is only appended at the end)
                for i in range(last_len, cur_len):
                    writer.append_item(i, self.data[i])
            elif cur_len < last_len:
                # pop case: LabelManager.baked/full backspace only pops from
                # the tail, never truncates the middle.
                writer.pop_items(last_len - cur_len)

            setattr(self, _LASTLEN_ATTR, cur_len)

            # Wrap label_listener so we can intercept the markup that
            # orig_update_text() will pass to it.  update_text() calls
            # label_listener synchronously, so it is safe to swap and
            # restore around the single orig call below.
            orig_listener = self.label_listener
            def capturing_listener(markup, synthetic):
                try:
                    writer.screen_snapshot(markup, synthetic)
                except Exception:
                    pass  # never let logging break the UI update
                return orig_listener(markup, synthetic)
            self.label_listener = capturing_listener
            try:
                return orig_update_text(self, *args, **kwargs)
            finally:
                self.label_listener = orig_listener

        return orig_update_text(self, *args, **kwargs)

    # ------------------------------------------------------------------
    # Patched __del__ to ensure file is flushed/closed
    # ------------------------------------------------------------------
    def patched_del(self):
        writer = getattr(self, _WRITER_ATTR, None)
        if writer is not None:
            writer.close()
            setattr(self, _WRITER_ATTR, None)
        if orig_del is not None:
            try:
                orig_del(self)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Install the patches on the class
    # ------------------------------------------------------------------
    LabelManager.__init__ = patched_init
    LabelManager.clear = patched_clear
    LabelManager.update_text = patched_update_text
    LabelManager.__del__ = patched_del
    setattr(LabelManager, _PATCH_ATTR, True)

    return True
