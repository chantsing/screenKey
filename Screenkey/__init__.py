try:
    from collections.abc import MutableMapping
except ImportError:
    # for python<3.3
    from collections import MutableMapping

# Setup gettext
import os.path
import gettext

MODULE_DIR = os.path.join(os.path.dirname(__file__))
gettext.install('screenkey', os.path.join(MODULE_DIR, 'locale'))


# Screenkey version
APP_NAME = "Screenkey"
APP_DESC = _("Screencast your keys")
APP_URL = 'https://www.thregr.org/~wavexx/software/screenkey/'
VERSION = '1.5'

SLOP_URL = 'https://github.com/naelstrof/slop'
ERROR_URL = 'https://www.thregr.org/~wavexx/software/screenkey/#troubleshooting'


# CLI/Interface options
POSITIONS = {
    'top': _('Top'),
    'center': _('Center'),
    'bottom': _('Bottom'),
    'fixed': _('Fixed'),
}

FONT_SIZES = {
    'large': _('Large'),
    'medium': _('Medium'),
    'small': _('Small'),
}

KEY_MODES = {
    'composed': _('Composed'),
    'translated': _('Translated'),
    'keysyms': _('Keysyms'),
    'raw': _('Raw'),
}

BAK_MODES = {
    'normal': _('Normal'),
    'baked': _('Baked'),
    'full': _('Full'),
}

MODS_MODES = {
    'normal': _('Normal'),
    'emacs': _('Emacs'),
    'mac': _('Mac'),
    'win': _('Windows'),
    'tux': _('Linux'),
}

class Options(MutableMapping):
    def __init__(self, *args, **kw):
        self.__dict__['_store'] = dict(*args, **kw)

    def __getitem__(self, key):
        return self._store[key]
    
    def __setitem__(self, key, value):
        self._store[key] = value
    
    def __delitem__(self, key):
        del self._store[key]

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __getattr__(self, key):
        return self._store[key]

    def __setattr__(self, key, value):
        self._store[key] = value

    def __delattr__(self, key):
        del self._store[key]
