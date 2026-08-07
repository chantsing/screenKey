# "screenkey" is distributed under GNU GPLv3+, WITHOUT ANY WARRANTY.
# Copyright(c) 2010-2012: Pablo Seminario <pabluk@gmail.com>
# Copyright(c) 2015-2016: wave++ "Yuri D'Elia" <wavexx@thregr.org>
# Copyright(c) 2019-2020: Yuto Tokunaga <yuntan.sub1@gmail.com>

from . import inputlistener
from .inputlistener import InputListener, InputType

from gi.repository import GLib

from collections import namedtuple
from datetime import datetime

# Key replacement data:
#
# bk_stop: stops backspace processing in baked mode, but not full mode
#          these keys generally move the caret, and are also padded with a thin space
# silent:  always stops backspace processing (baked/full mode)
#          these keys generally do not emit output in the text and cannot be processed
# spaced:  strong spacing is required around the symbol

ReplData = namedtuple('ReplData', ['value', 'font', 'suffix'])
KeyRepl  = namedtuple('KeyRepl',  ['bk_stop', 'silent', 'spaced', 'repl'])
KeyData  = namedtuple('KeyData',  ['stamp', 'is_ctrl', 'bk_stop', 'silent', 'spaced', 'markup'])
ButtonData = namedtuple('ButtonData',  ['stamp', 'btn', 'pressed'])

REPLACE_SYMS = {
    # Regular keys
    'Escape':       KeyRepl(True,  True,  True,  _('Esc')),
    'Tab':          KeyRepl(True,  False, False, _('↹')),
    'ISO_Left_Tab': KeyRepl(True,  False, False, _('↹')),
    'Return':       KeyRepl(True,  False, False, _('⏎')),
    'space':        KeyRepl(False, False, False, _('␣')),
    'BackSpace':    KeyRepl(True,  True,  False, _('⌫')),
    'Caps_Lock':    KeyRepl(True,  True,  True,  _('Caps')),
    'F1':           KeyRepl(True,  True,  True,  _('F1')),
    'F2':           KeyRepl(True,  True,  True,  _('F2')),
    'F3':           KeyRepl(True,  True,  True,  _('F3')),
    'F4':           KeyRepl(True,  True,  True,  _('F4')),
    'F5':           KeyRepl(True,  True,  True,  _('F5')),
    'F6':           KeyRepl(True,  True,  True,  _('F6')),
    'F7':           KeyRepl(True,  True,  True,  _('F7')),
    'F8':           KeyRepl(True,  True,  True,  _('F8')),
    'F9':           KeyRepl(True,  True,  True,  _('F9')),
    'F10':          KeyRepl(True,  True,  True,  _('F10')),
    'F11':          KeyRepl(True,  True,  True,  _('F11')),
    'F12':          KeyRepl(True,  True,  True,  _('F12')),
    'Up':           KeyRepl(True,  True,  False, _('↑')),
    'Left':         KeyRepl(True,  True,  False, _('←')),
    'Right':        KeyRepl(True,  True,  False, _('→')),
    'Down':         KeyRepl(True,  True,  False, _('↓')),
    'Prior':        KeyRepl(True,  True,  True,  _('PgUp')),
    'Next':         KeyRepl(True,  True,  True,  _('PgDn')),
    'Home':         KeyRepl(True,  True,  True,  _('Home')),
    'End':          KeyRepl(True,  True,  True,  _('End')),
    'Insert':       KeyRepl(False, True,  True,  _('Ins')),
    'Delete':       KeyRepl(True,  False, True,  _('Del')),
    'KP_End':       KeyRepl(False, False, True,  _('1ᴷᴾ')),
    'KP_Down':      KeyRepl(False, False, True,  _('2ᴷᴾ')),
    'KP_Next':      KeyRepl(False, False, True,  _('3ᴷᴾ')),
    'KP_Left':      KeyRepl(False, False, True,  _('4ᴷᴾ')),
    'KP_Begin':     KeyRepl(False, False, True,  _('5ᴷᴾ')),
    'KP_Right':     KeyRepl(False, False, True,  _('6ᴷᴾ')),
    'KP_Home':      KeyRepl(False, False, True,  _('7ᴷᴾ')),
    'KP_Up':        KeyRepl(False, False, True,  _('8ᴷᴾ')),
    'KP_Prior':     KeyRepl(False, False, True,  _('9ᴷᴾ')),
    'KP_Insert':    KeyRepl(False, False, True,  _('0ᴷᴾ')),
    'KP_Delete':    KeyRepl(False, False, True,  _('(.)')),
    'KP_Add':       KeyRepl(False, False, True,  _('(+)')),
    'KP_Subtract':  KeyRepl(False, False, True,  _('(-)')),
    'KP_Multiply':  KeyRepl(False, False, True,  _('(*)')),
    'KP_Divide':    KeyRepl(False, False, True,  _('(/)')),
    'KP_Enter':     KeyRepl(True,  False, False, _('⏎')),
    'KP_1':         KeyRepl(False, False, True,  _('1ᴷᴾ')),
    'KP_2':         KeyRepl(False, False, True,  _('2ᴷᴾ')),
    'KP_3':         KeyRepl(False, False, True,  _('3ᴷᴾ')),
    'KP_4':         KeyRepl(False, False, True,  _('4ᴷᴾ')),
    'KP_5':         KeyRepl(False, False, True,  _('5ᴷᴾ')),
    'KP_6':         KeyRepl(False, False, True,  _('6ᴷᴾ')),
    'KP_7':         KeyRepl(False, False, True,  _('7ᴷᴾ')),
    'KP_8':         KeyRepl(False, False, True,  _('8ᴷᴾ')),
    'KP_9':         KeyRepl(False, False, True,  _('9ᴷᴾ')),
    'KP_0':         KeyRepl(False, False, True,  _('0ᴷᴾ')),
    'Num_Lock':     KeyRepl(False, True,  True,  _('NumLck')),
    'Scroll_Lock':  KeyRepl(False, True,  True,  _('ScrLck')),
    'Pause':        KeyRepl(False, True,  True,  _('Pause')),
    'Break':        KeyRepl(False, True,  True,  _('Break')),
    'Print':        KeyRepl(False, True,  True,  _('Print')),
    'Multi_key':    KeyRepl(False, True,  True,  _('Compose')),

    # Multimedia keys
    'XF86AudioMute':         KeyRepl(True, True, True, [ReplData(_('\uf026'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf026'),    'FontAwesome',         None),
                                                        ReplData(_('Mute'),      None,                  None)]),
    'XF86AudioMicMute':      KeyRepl(True, True, True, [ReplData(_('\uf131'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf131'),    'FontAwesome',         None),
                                                        ReplData(_('Rec'),       None,                  None)]),
    'XF86AudioRaiseVolume':  KeyRepl(True, True, True, [ReplData(_('\uf028'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf028'),    'FontAwesome',         None),
                                                        ReplData(_('Vol'),       None,                  '+')]),
    'XF86AudioLowerVolume':  KeyRepl(True, True, True, [ReplData(_('\uf027'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf027'),    'FontAwesome',         None),
                                                        ReplData(_('Vol'),       None,                  '-')]),
    'XF86AudioPrev':         KeyRepl(True, True, True, [ReplData(_('\uf048'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf048'),    'FontAwesome',         None),
                                                        ReplData(_('Prev'),      None,                  None)]),
    'XF86AudioNext':         KeyRepl(True, True, True, [ReplData(_('\uf051'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf051'),    'FontAwesome',         None),
                                                        ReplData(_('Next'),      None,                  None)]),
    'XF86AudioPlay':         KeyRepl(True, True, True, [ReplData(_('\uf04b'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf04b'),    'FontAwesome',         None),
                                                        ReplData(_('▶'),         None,                  None)]),
    'XF86AudioStop':         KeyRepl(True, True, True, [ReplData(_('\uf04d'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf04d'),    'FontAwesome',         None),
                                                        ReplData(_('⬛'),         None,                  None)]),
    'XF86Eject':             KeyRepl(True, True, True, [ReplData(_('\uf052'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf052'),    'FontAwesome',         None),
                                                        ReplData(_('Eject'),     None,                  None)]),
    'XF86MonBrightnessDown': KeyRepl(True, True, True, [ReplData(_('\uf185'),    'Font Awesome 5 Free', '-'),
                                                        ReplData(_('\uf185'),    'FontAwesome',         '-'),
                                                        ReplData(_('Bright'),    None,                  '-')]),
    'XF86MonBrightnessUp':   KeyRepl(True, True, True, [ReplData(_('\uf185'),    'Font Awesome 5 Free', '+'),
                                                        ReplData(_('\uf185'),    'FontAwesome',         '+'),
                                                        ReplData(_('Bright'),    None,                  '+')]),
    'XF86Display':           KeyRepl(True, True, True, [ReplData(_('\uf108'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf108'),    'FontAwesome',         None),
                                                        ReplData(_('Display'),   None,                  None)]),
    'XF86WLAN':              KeyRepl(True, True, True, [ReplData(_('\uf1eb'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf1eb'),    'FontAwesome',         None),
                                                        ReplData(_('WLAN'),      None,                  None)]),
    'XF86Search':            KeyRepl(True, True, True, [ReplData(_('\uf002'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf002'),    'FontAwesome',         None),
                                                        ReplData(_('Search'),    None,                  None)]),
    'XF86Bluetooth':         KeyRepl(True, True, True, [ReplData(_('\uf294'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf294'),    'FontAwesome',         None),
                                                        ReplData(_('Bluetooth'), None,                  None)]),
    'XF86Tools':             KeyRepl(True, True, True, [ReplData(_('\uf7d9'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('🛠'),        None,                  None)]),
    'XF86Favorites':         KeyRepl(True, True, True, [ReplData(_('\uf005'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf005'),    'FontAwesome',         None),
                                                        ReplData(_('🟊'),        None,                  None)]),
    'XF86HomePage':          KeyRepl(True, True, True, [ReplData(_('\uf015'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf015'),    'FontAwesome',         None),
                                                        ReplData(_('⌂'),        None,                  None)]),
    'XF86Mail':              KeyRepl(True, True, True, [ReplData(_('\uf0e0'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf0e0'),    'FontAwesome',         None),
                                                        ReplData(_('📧'),        None,                  None)]),
    'XF86Calculator':        KeyRepl(True, True, True, [ReplData(_('\uf1ec'),    'Font Awesome 5 Free', None),
                                                        ReplData(_('\uf1ec'),    'FontAwesome',         None),
                                                        ReplData(_('🖩'),         None,                  None)]),
}

WHITESPACE_SYMS = {'Tab', 'ISO_Left_Tab', 'Return', 'space', 'KP_Enter'}

MODS_SYMS = {
    'shift':  {'Shift_L', 'Shift_R'},
    'ctrl':   {'Control_L', 'Control_R'},
    'alt':    {'Alt_L', 'Alt_R', 'Meta_L', 'Meta_R'},
    'super':  {'Super_L', 'Super_R'},
    'hyper':  {'Hyper_L', 'Hyper_R'},
    'alt_gr': {'ISO_Level3_Shift'},
}

REPLACE_MODS = {
    'shift':  {'normal': _('Shift+'), 'emacs': 'S-', 'mac': _('⇧+')},
    'ctrl':   {'normal': _('Ctrl+'),  'emacs': 'C-', 'mac': _('⌘+')},
    'alt':    {'normal': _('Alt+'),   'emacs': 'M-', 'mac': _('⌥+')},
    'super':  {'normal': _('Super+'), 'emacs': 's-',
               'win': [ReplData(_('\uf17a'), 'Font Awesome 5 Free', '+'),
                       ReplData(_('\uf17a'), 'FontAwesome',         '+'),
                       ReplData(_('Win'),    None,                  '+')],
               'tux': [ReplData(_('\uf17c'), 'Font Awesome 5 Free', '+'),
                       ReplData(_('\uf17c'), 'FontAwesome',         '+'),
                       ReplData(_('Super'),  None,                  '+')]},
    'hyper':  {'normal': _('Hyper+'), 'emacs': 'H-'},
    'alt_gr': {'normal': _('AltGr+'), 'emacs': 'AltGr-'},
}


def keysym_to_mod(keysym):
    for k, v in MODS_SYMS.items():
        if keysym in v:
            return k
    return None


class LabelManager:
    def __init__(self, label_listener, image_listener, logger, key_mode,
                 bak_mode, mods_mode, mods_only, multiline, vis_shift,
                 vis_space, recent_thr, compr_cnt, ignore, pango_ctx,
                 enabled):
        self.key_mode = key_mode
        self.bak_mode = bak_mode
        self.mods_mode = mods_mode
        self.logger = logger
        self.label_listener = label_listener
        self.image_listener = image_listener
        self.data = []
        self.enabled = enabled
        self.mods_only = mods_only
        self.multiline = multiline
        self.vis_shift = vis_shift
        self.vis_space = vis_space
        self.recent_thr = recent_thr
        self.compr_cnt = compr_cnt
        self.ignore = ignore
        self.kl = None
        self.font_families = {x.get_name() for x in pango_ctx.list_families()}
        self.update_replacement_map()


    def __del__(self):
        self.stop()


    def start(self):
        self.stop()
        compose = (self.key_mode == 'composed')
        translate = (self.key_mode in ['composed', 'translated'])
        self.kl = InputListener(self.event_handler,
                                InputType.keyboard | InputType.button,
                                compose, translate)
        self.kl.start()
        self.logger.debug("Thread started.")


    def stop(self):
        if self.kl:
            self.kl.stop()
            self.logger.debug("Thread stopped.")
            self.kl.join()
            self.kl = None


    def clear(self):
        self.data = []


    def get_repl_markup(self, repl):
        if type(repl) != list:
            repl = [repl]
        for c in repl:
            # no replacement data
            if type(c) != ReplData:
                return GLib.markup_escape_text(c)

            # plain suffix
            if c.suffix is None:
                sfx = ''
            else:
                sfx = GLib.markup_escape_text(c.suffix)

            if c.font is None:
                # regular font
                return GLib.markup_escape_text(c.value) + sfx;
            elif c.font in self.font_families:
                # custom symbol
                return '<span font_family="' + c.font + '" font_weight="regular">' + \
                    GLib.markup_escape_text(c.value) + '</span>' + sfx;


    def update_replacement_map(self):
        self.replace_syms = {}
        for k, v in REPLACE_SYMS.items():
            markup = self.get_repl_markup(v.repl)
            self.replace_syms[k] = KeyRepl(v.bk_stop, v.silent, v.spaced, markup)

        self.replace_mods = {}
        for k, v in REPLACE_MODS.items():
            data = v.get(self.mods_mode, v['normal'])
            self.replace_mods[k] = self.get_repl_markup(data)


    def update_text(self, synthetic=False):
        markup = ""
        recent = False
        stamp = datetime.now()
        repeats = 0
        for i, key in enumerate(self.data):
            if i != 0:
                last = self.data[i - 1]

                # compress repeats
                if self.compr_cnt and key.markup == last.markup:
                    repeats += 1
                    if repeats < self.compr_cnt:
                        pass
                    elif i == len(self.data) - 1 or key.markup != self.data[i + 1].markup:
                        if not recent and (stamp - key.stamp).total_seconds() < self.recent_thr:
                            markup += '<u>'
                            recent = True
                        markup += '<sub><small>…{}×</small></sub>'.format(repeats + 1)
                        if len(key.markup) and key.markup[-1] == '\n':
                            markup += '\n'
                        continue
                    else:
                        continue

                # character block spacing
                if len(last.markup) and last.markup[-1] == '\n':
                    pass
                elif key.is_ctrl or last.is_ctrl or key.spaced or last.spaced:
                    markup += ' '
                elif key.bk_stop or last.bk_stop or repeats > self.compr_cnt:
                    markup += '<span font_family="sans">\u2009</span>'
                if key.markup != last.markup:
                    repeats = 0

            key_markup = key.markup
            if type(key_markup) is bytes:
                key_markup = key_markup.decode()
            if not recent and (stamp - key.stamp).total_seconds() < self.recent_thr:
                recent = True
                key_markup = '<u>' + key_markup

            # disable ligatures
            if len(key.markup) == 1 and 0x0300 <= ord(key.markup) <= 0x036F:
                # workaround for pango not handling ZWNJ correctly for combining marks
                markup += '\u180e' + key_markup + '\u200a'
            elif len(key_markup):
                markup += '\u200c' + key_markup

        if len(markup) and markup[-1] == '\n':
            markup = markup.rstrip('\n')
            if not self.vis_space and not self.data[-1].is_ctrl:
                # always show some return symbol at the last line
                markup += self.replace_syms['Return'].repl
        if recent:
            markup += '</u>'
        self.logger.debug("Label updated: %s." % repr(markup))
        self.label_listener(markup, synthetic)


    def queue_update(self):
        self.update_text(True)


    def event_handler(self, event):
        if event is None:
            self.logger.debug("inputlistener failure: {}".format(str(self.kl.error)))
            self.label_listener(None, None)
            return

        if isinstance(event, inputlistener.KeyData):
            self.key_press(event)
        elif isinstance(event, inputlistener.ButtonData):
            self.btn_press(event)
        else:
            self.logger.error("unhandled event type {}".format(type(event)))


    def key_press(self, event):
        if event.symbol is None:
            # TODO: Investigate what causes this to happen.
            # I caught it once in pdb, but in this function, not in inputlistener,
            # and KeyData doesn't contain enough info.
            return
        symbol = event.symbol.decode()

        if self.enabled:
            for mod, button_id in zip(['ctrl', 'alt', 'shift'], range(8, 11)):
                if symbol in MODS_SYMS[mod]:
                    self.image_listener(ButtonData(
                        datetime.now(), button_id, event.pressed
                    ))

        if event.pressed == False:
            self.logger.debug("Key released {:5}(ks): {}".format(event.keysym, symbol))
            return
        if symbol in self.ignore:
            self.logger.debug("Key ignored  {:5}(ks): {}".format(event.keysym, symbol))
            return
        if event.filtered:
            self.logger.debug("Key filtered {:5}(ks): {}".format(event.keysym, symbol))
        else:
            state = "repeated" if event.repeated else "pressed"
            string = repr(event.string)
            self.logger.debug("Key {:8} {:5}(ks): {} ({}, mask: {:08b})".format
                              (state, event.keysym, string, symbol, event.mods_mask))

        # Stealth enable/disable handling
        for mod in ['shift', 'ctrl', 'alt']:
            if not event.repeated and event.modifiers[mod] \
               and symbol in MODS_SYMS[mod]:
                self.enabled = not self.enabled
                state = 'enabled' if self.enabled else 'disabled'
                if not self.enabled:
                    self.image_listener(None)
                self.logger.info("{mod}+{mod} detected: screenkey {state}".format(
                    mod=mod.capitalize(), state=state))
        if not self.enabled:
            return False

        # keep the window alive as the user is composing
        mod_pressed = keysym_to_mod(symbol) is not None
        update = len(self.data) and (event.filtered or mod_pressed)

        if not event.filtered:
            if self.key_mode in ['translated', 'composed']:
                update |= self.key_normal_mode(event)
            elif self.key_mode == 'raw':
                update |= self.key_raw_mode(event)
            else:
                update |= self.key_keysyms_mode(event)
        if update:
            self.update_text()


    def key_normal_mode(self, event):
        self.logger.debug("key_normal_mode")
        # Visible modifiers
        mod = ''
        for cap in ['ctrl', 'alt', 'super', 'hyper']:
            if event.modifiers[cap]:
                mod = mod + self.replace_mods[cap]

        # Backspace handling
        symbol = event.symbol.decode()
        if symbol == 'BackSpace' and not self.mods_only and \
           mod == '' and not event.modifiers['shift']:
            key_repl = self.replace_syms.get(symbol)
            if self.bak_mode == 'normal':
                self.data.append(KeyData(datetime.now(), False, *key_repl))
                return True
            else:
                if not len(self.data):
                    pop = False
                else:
                    last = self.data[-1]
                    if last.is_ctrl:
                        pop = False
                    elif self.bak_mode == 'baked':
                        pop = not last.bk_stop
                    else:
                        pop = not last.silent
                if pop:
                    self.data.pop()
                else:
                    self.data.append(KeyData(datetime.now(), False, *key_repl))
                return True

        # Regular keys
        key_repl = self.replace_syms.get(symbol)
        replaced = key_repl is not None
        if key_repl is None:
            if keysym_to_mod(symbol):
                return False
            else:
                repl = event.string or symbol
                markup = GLib.markup_escape_text(repl)
                key_repl = KeyRepl(False, False, len(repl) > 1, markup)

        if event.modifiers['shift'] and \
           (replaced or (mod != '' and \
                         self.vis_shift and \
                         self.mods_mode != 'emacs')):
            # add back shift for translated keys
            mod = mod + self.replace_mods['shift']

        # Whitespace handling
        if not self.vis_space and mod == '' and symbol in WHITESPACE_SYMS:
            if symbol not in ['Return', 'KP_Enter']:
                repl = event.string
            elif self.multiline:
                repl = ''
            else:
                repl = key_repl.repl
            key_repl = KeyRepl(key_repl.bk_stop, key_repl.silent, key_repl.spaced, repl)

        # Multiline
        if symbol in ['Return', 'KP_Enter'] and self.multiline == True:
            key_repl = KeyRepl(key_repl.bk_stop, key_repl.silent,
                               key_repl.spaced, key_repl.repl + '\n')

        if mod == '':
            if not self.mods_only:
                repl = key_repl.repl

                # switches
                if symbol in ['Caps_Lock', 'Num_Lock']:
                    state = event.modifiers[symbol.lower()]
                    repl += '(%s)' % (_('off') if state else _('on'))

                self.data.append(KeyData(datetime.now(), False, key_repl.bk_stop,
                                         key_repl.silent, key_repl.spaced, repl))
                return True
        else:
            if self.mods_mode == 'emacs' or key_repl.repl[0] != mod[-1]:
                repl = mod + key_repl.repl
            else:
                repl = mod + '‟' + key_repl.repl + '”'
            self.data.append(KeyData(datetime.now(), True, key_repl.bk_stop,
                                     key_repl.silent, key_repl.spaced, repl))
            return True

        return False


    def key_raw_mode(self, event):
        # modifiers
        mod = ''
        for cap in REPLACE_MODS.keys():
            if event.modifiers[cap]:
                mod = mod + self.replace_mods[cap]

        # keycaps
        symbol = event.symbol.decode()
        key_repl = self.replace_syms.get(symbol)
        if key_repl is None:
            if keysym_to_mod(symbol):
                return False
            else:
                repl = event.string.upper() if event.string else symbol
                markup = GLib.markup_escape_text(repl)
                key_repl = KeyRepl(False, False, len(repl) > 1, markup)

        if mod == '':
            repl = key_repl.repl

            # switches
            if symbol in ['Caps_Lock', 'Num_Lock']:
                state = event.modifiers[symbol.lower()]
                repl += '(%s)' % (_('off') if state else _('on'))

            self.data.append(KeyData(datetime.now(), False, key_repl.bk_stop,
                                     key_repl.silent, key_repl.spaced, repl))
        else:
            if self.mods_mode == 'emacs' or key_repl.repl[0] != mod[-1]:
                repl = mod + key_repl.repl
            else:
                repl = mod + '‟' + key_repl.repl + '”'
            self.data.append(KeyData(datetime.now(), True, key_repl.bk_stop,
                                     key_repl.silent, key_repl.spaced, repl))
        return True


    def key_keysyms_mode(self, event):
        symbol = event.symbol.decode()
        if symbol in REPLACE_SYMS:
            value = symbol
        else:
            value = event.string or symbol
        self.data.append(KeyData(datetime.now(), True, True, True, True, value))
        return True

    # callback for mouse button presses
    def btn_press(self, event):
        if not self.enabled:
            return False
        if event.pressed:
            action = "pressed"
        else:
            action = "released"
        self.logger.debug("Mouse button %d %s" % (event.btn, action))

        # possible event.btn values:
        # 1 = LMB, 2 = MMB (wheel click), 3 = RMB, 4/5 = wheel up/down,
        # 6/7 = wheel left/right, 8+ extra buttons (e. g. thumb buttons)
        if event.btn > 7:
            # image_listener can only handle common buttons, redirect thumb buttons etc. to label
            if not event.pressed:
                return False
            # what we refer to as "Mouse 4" has an internal value of 8,
            # so we subtract 4 from the btn value
            markup = GLib.markup_escape_text("M{}".format(event.btn - 4))

            # show as label, treated the same as keyboard button presses
            self.data.append(KeyData(datetime.now(), False, True,
                         True, True, markup))
            self.update_text()
        else:
            # show event in image
            self.image_listener(
                ButtonData(datetime.now(), event.btn, event.pressed)
            )
