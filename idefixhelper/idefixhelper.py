import ast
from pathlib import Path
from types import SimpleNamespace
import re

from IPython.display import Markdown
import numpy as np

def ev(value):
    "parse a string value as python number/list or keeps it as string."
    try:
        res = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        res = value
    return res

def parse_ini(fname, i=0):
    """parses the a `idefix.ini` file and returns a namespace with the settings.
    If `fname` is a list of strings, it will be used instead of reading a file
    """
    if isinstance(fname, (Path, str)):
        text = Path(fname).read_text().split('\n')
    elif isinstance(fname, list):
        text = fname
    else:
        raise ValueError('fname needs to be a file path or list of line-strings!')

    data = SimpleNamespace()
    while i < len(text):
        line = text[i].strip()
        i += 1
        if line == '':
            continue
        if line.startswith('['):
            section_name = line.strip('[]').replace('.', '_').replace('-', '_').replace(' ', '_')
            section = SimpleNamespace()
            setattr(data, section_name, section)
        else:
            name = line.split()[0].replace('.', '_').replace('-', '_')
            string = line[len(name):].strip()

            # convert to value(s)
            ls = re.sub('\s+', ' ', string).split(' ')
            res = [ev(l) for l in ls]
            if len(res) == 1:
                res = res[0]
            
            setattr(section, name, res)
    return data


def parse_definitions(fname):
    "parses a idefix `definitions.hpp` file (or list of strings), returns contents as namespace"
    
    if isinstance(fname, (Path, str)):
        text = Path(fname).read_text().split('\n')
    elif isinstance(fname, list):
        text = fname
    else:
        raise ValueError('fname needs to be a file path or list of line-strings!')

    # clean up empty lines and whitespace
    text = [line.strip() for line in text if line.strip()!='']
    
    data = SimpleNamespace()

    for line in text:
        # we ignore lines that don't start with #define       
        if not line.startswith('#define'):
            continue
        
        split = line.split()[1:]
        if len(split) == 1:
            setattr(data, split[0], True)
        elif len(split) == 2:
            setattr(data, split[0], ev(split[1]))
        else:
            setattr(data, split[0], ev(split[1:]))
                
    return data


def parse_idefixlog(fname):
    """parse a idefix log file for settings and definitions"""
    
    text = Path(fname).read_text().split('\n')
    i = 0
    ########## Parse idefix.ini part ########
    while not text[i].strip().startswith('Input Parameters using input file'):    
        i += 1
    ini_filename = text[i].split()[-1].replace(':', '')
    # found start
    i += 2
    subtext = []
    while not text[i].strip().startswith(77 * '-'):
        subtext += [text[i].strip()]
        i += 1

    config = parse_ini(subtext)
    config.ini_filename = ini_filename
    
    ######## parse  other lines ########
    while not ('Input: DIMENSIONS=' in text[i]):
        i+= 1
    config.DIMENSIONS = text[i].strip('.').split('=')[-1]

    while not ('Input: COMPONENTS=' in text[i]):
        i+= 1
    config.COMPONENTS = text[i].strip('.').split('=')[-1]

    while not ('Gravity: G=' in text[i]):
        i+= 1
    config.G = ev(text[i].split('=')[-1])


    ######### return the data ###########
    return config


def parse_setup(fname):
    """
    Reads the setup file and breaks it up into functions to look up
    source code.
    """
    if isinstance(fname, (Path, str)):
        text = Path(fname).read_text().split('\n')
    elif isinstance(fname, list):
        text = fname
    else:
        raise ValueError('fname needs to be a file path or list of line-strings!')
    
    i = 0
    functions = SimpleNamespace()
    
    while i < len(text):
        # scan to next function
        while (i < len(text)) and (not text[i].strip().startswith('void ')):
            i += 1
            
        # get name of function
        fct_name = ''.join(text[i].strip().split()[1:]).split('(')[0]
        subtext = [text[i]]
        i += 1
        # collect the text of the function
        while (i < len(text)) and (not text[i].strip().startswith('void ')):
            subtext += [text[i]]
            i += 1

        # store it
        setattr(functions, fct_name, '\n'.join(subtext))
    
    return functions


def syntax_highlight(fcts):
    keys = [v for v in fcts.__dir__() if not v.startswith('_')]
    output = SimpleNamespace()
    for k in keys:
        setattr(output, k, Markdown('```cpp\n' + getattr(fcts, k) + '\n```'))
    return  output


def read_setup(dirname, highlight=True):
    dirname = Path(dirname)

    assert dirname.is_dir(), 'dirname must be a directory'

    setup_file = dirname / 'setup.cpp'
    ini_file = dirname / 'idefix.ini'
    def_file = dirname / 'definitions.hpp'

    setup = SimpleNamespace()

    if setup_file.is_file():
        print(f'reading {setup_file.name}')
        if highlight:
            setup.functions = syntax_highlight(parse_setup(setup_file))
        else:
            setup.functions = parse_setup(setup_file)

    if ini_file.is_file():
        print(f'reading {ini_file.name}')
        setup.ini = parse_ini(ini_file)

    if def_file.is_file():
        print(f'reading {def_file.name}')
        setup.defs = parse_definitions(def_file)

    return setup