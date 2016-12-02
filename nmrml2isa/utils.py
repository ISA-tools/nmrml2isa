# coding: utf-8
from __future__ import (
    print_function,
    absolute_import,
    unicode_literals,
)

import six
import string
import os
import functools
import tarfile
import collections

from . import __version__, __author__, __email__

NMR_CV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nmrCV.owl')

# GET BEST AVAILABLE XML PARSER
try:
    from lxml import etree
except ImportError:
    try:
        from xml.etree import cElementTree as etree
    except ImportError:
        from xml.etree import ElementTree as etree


## VERSION AGNOSTIC UTILS
class PermissiveFormatter(string.Formatter):
    """A formatter that replace wrong and missing key with a blank."""
    def __init__(self, missing='', bad_fmt=''):
        self.missing, self.bad_fmt=missing, bad_fmt

    def get_field(self, field_name, args, kwargs):
        # Handle a key not found
        try:
            val=super(PermissiveFormatter, self).get_field(field_name, args, kwargs)
        except (KeyError, AttributeError, IndexError, TypeError):
            val=None,field_name
        return val

    def format_field(self, value, spec):
        # handle an invalid format
        if value==None:
            return self.missing
        try:
            return super(PermissiveFormatter, self).format_field(value, spec)
        except ValueError:
            if self.bad_fmt is not None:
                return self.bad_fmt
            else:
                raise

class _TarFile(tarfile.TarFile):
    """A TarFile proxy with a setable name
    """

    def __init__(self, name, buffered_reader):
        self.name = name
        self.BufferedReader = buffered_reader

    def __getattr__(self, attr):
        if attr=="name":
            return self.name
        return getattr(self.BufferedReader, attr)

class ChainMap(collections.Mapping):
    """A quick backport of collections.ChainMap
    """

    def __init__(self, *maps):
        self.maps = list(maps)

    def __getitem__(self, key):
        for mapping in self.maps:
            try:
                return mapping[key]
            except KeyError:
                pass
        return self.__missing__(key)

    @staticmethod
    def __missing__(key):
        raise KeyError(key)

    def __iter__(self):
        return itertools.chain(*self.mappings)

    def __len__(self):
        return sum(len(x) for x in self.mappings)


def compr_extract(compr_pth):
    """Extract tar.gz or .zip files into Python objects

    Arguments:
        compr_path (str): the path to the compressed file

    Returns:
        tarfile.TarFile: if the file is a gzipped tar file
        zipfile.ZipFile: if the file is a zipped file
    """

    filend = ('.nmrml')
    if zipfile.is_zipfile(compr_pth):
        comp = zipfile.ZipFile(compr_pth)
        cfiles = [comp.open(f) for f in comp.namelist() if f.lower().endswith(filend)]
        filelist = [f.filename for f in comp.filelist]
    else:
        comp = tarfile.open(compr_pth, 'r:*')
        cfiles = [_TarFile(m.name, comp.extractfile(m)) for m in comp.getmembers() if m.name.lower().endswith(filend)]
        filelist = [f for f in comp.getnames()]

    # And add these file names as additional attribute the compression tar or zip objects
    for cf in cfiles:
        cf.filelist = filelist

    return cfiles


def star_args(func):
    """Unpack arguments if they come packed
    """
    @functools.wraps(func)
    def new_func(*args):
        if len(args)==1:
            return func(*args[0])
        else:
            return func(*args)
    return new_func

