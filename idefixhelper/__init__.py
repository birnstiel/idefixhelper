from importlib import metadata as _md
from .idefixhelper import parse_ini
from .idefixhelper import parse_idefixlog
from .idefixhelper import parse_definitions
from .idefixhelper import parse_setup
from .idefixhelper import read_setup
from .writable_dump import WritableDumpDataset

__name__ = "idefixhelper"
__version__ = _md.version("idefixhelper")

__all__ = [
    'parse_ini',
    'parse_idefixlog',
    'parse_definitions',
    'parse_setup',
    'read_setup',
    'WritableDumpDataset',
]
