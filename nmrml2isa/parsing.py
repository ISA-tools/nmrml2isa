# coding: utf-8
"""
Content
-----------------------------------------------------------------------------
This module exposes basic API of nmrl2isa, either being called from command
line interface with arguments parsing via **main** function, or from another
Python program via the **convert** function which works the same.

About
-----------------------------------------------------------------------------
The nmrml2isa parser was created by Martin Larralde (ENS Cachan, FR) in June
2016 during an internship at the EBI Cambridge.

License
-----------------------------------------------------------------------------
GNU General Public License version 3.0 (GPLv3)
"""
from __future__ import (
    print_function,
    absolute_import,
    unicode_literals,
)

import io
import os
import sys
import six
import glob
import argparse
import textwrap
import warnings
import json
import tarfile
import zipfile
import multiprocessing
import multiprocessing.pool
import pronto
import functools

try:
    import progressbar
except ImportError:
    progressbar = None

from . import (
    __author__,
    __version__,
    __name__,
    __license__,
)
from .isa   import ISA_Tab
from .nmrml  import nmrMLmeta
from .usermeta import UserMetaLoader
from .utils import (
    compr_extract,
    star_args,
    NMR_CV_PATH
)


@star_args
def _parse_file(filepath, ontology, pbar=None, verbose=False):
    """Parse a single file using a cache ontology and a metadata extractor

    Arguments:
        filepath (str): path to the nmrML file to parse
        ontology (pronto.Ontology): the cached ontology to use (nmr CV)
        pbar (progressbar.ProgressBar, optional): a progressbar
            to display progresses onto [default: None]

    Returns:
        dict: a dictionary containing the extracted metadata
    """
    meta = nmrMLmeta(filepath, ontology).meta
    if pbar is not None:
        pbar.update(pbar.value + 1)
    elif verbose:
        print("Finished parsing: {}".format(filepath))
    return meta

def convert(in_path, out_path, study_identifier, **kwargs):
    """ Parses a study from given *in_path* and then creates an ISA file.

    A new folder is created in the out directory bearing the name of
    the study identifier.

    Arguments:
        in_path (str): path to the directory or archive containing nmrML files
        out_path (str): path to the output directory (new directories will be
            created here)
        study_identifier (str): study identifier (e.g. MTBLSxxx)

    Keyword Arguments:
        usermeta (str, optional): the path to a json file, a xlsx file or
            directly a json formatted string containing user-defined
            metadata [default: None]
        jobs (int, optional): the number of jobs to use [default: 1]
        template_directory (str, optional): the path to a directory
            containing custom templates to use when importing ISA tab
            [default: None]
        verbose (bool): display more output [default: True]
        quiet (bool): do not display any output [default: False]
    """
    quiet = kwargs.get('quiet', False)
    verbose = kwargs.get('verbose', not quiet)
    jobs = kwargs.get('jobs', 1)
    template_directory = kwargs.get('template_directory', None)


    # load the nmr controlled vocabulary
    NMR_CV = pronto.Ontology(NMR_CV_PATH, False)

    # open user metadata file if any
    meta_loader = UserMetaLoader(kwargs.get('usermeta', None))

    # get nmrML file in given folder (case unsensitive)
    if os.path.isdir(in_path):
        compr = False
        nmrml_files = glob.glob(os.path.join(in_path, "*.[n|N][m|M][r|R][m|M][l|L]"))
    elif tarfile.is_tarfile(in_path) or zipfile.is_zipfile(in_path):
        compr = True
        nmrml_files = compr_extract(in_path)
    else:
        raise SystemError("Couldn't recognise format of "
                          "{} as a source of nmrML files".format(in_dir))

    if nmrml_files:
        if not (verbose or quiet) and progressbar is not None:
            pbar = progressbar.ProgressBar(
                min_value = 0, max_value = len(nmrml_files),
                widgets=['Parsing {:8}: '.format(study_identifier),
                           progressbar.SimpleProgress(),
                           progressbar.Bar(marker=["#","█"][six.PY3], left=" |", right="| "),
                           progressbar.ETA()]
                )
            pbar.start()
        else:
            pbar = None

        if jobs > 1:
            pool = multiprocessing.pool.ThreadPool(jobs)
            metalist = pool.map(_parse_file, [(nmrml_file, NMR_CV, pbar) for nmrml_file in sorted(nmrml_files)])
        else:
            metalist = [_parse_file([nmrml_file, NMR_CV, pbar, verbose]) for nmrml_file in sorted(nmrml_files)]

        if metalist:
            if verbose:
                print("Dumping nmrML meta information into ISA-Tab structure")
            isa_tab = ISA_Tab(out_path, study_identifier, usermeta=meta_loader.usermeta, template_directory=template_directory)
            isa_tab.write(metalist)

    else:
        warnings.warn("No files were found in {}.".format(in_path))

def main(argv=None):
    """Run **nmrml2isa** from the command line

    Arguments
        argv (list, optional): the list of arguments to run nmrml2isa
            with (if None, then sys.argv is used) [default: None]
    """
    p = argparse.ArgumentParser(prog=__name__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''Extract meta information from nmrML files and create ISA-tab structure''',
        usage='nmrml2isa -i IN_PATH -o OUT_PATH -s STUDY_ID [options]',
    )

    p.add_argument('-i', dest='in_path', help='input folder or archive containing nmrML files', required=True)
    p.add_argument('-o', dest='out_path', help='out folder (a new directory will be created here)', required=True)
    p.add_argument('-s', dest='study_id', help='study identifier (e.g. MTBLSxxx)', required=True)
    p.add_argument('-m', dest='usermeta', help='additional user provided metadata (JSON or XLSX format)', default=None, required=False)#, type=json.loads)
    p.add_argument('-j', dest='jobs', help='launch different processes for parsing', action='store', required=False, default=1, type=int)
    p.add_argument('-W', dest='wrng_ctrl', help='warning control (with python default behaviour)', action='store', default='once', required=False, choices=['ignore', 'always', 'error', 'default', 'module', 'once'])
    p.add_argument('-t', dest='template_dir', help='directory containing default template files', action='store', default=None)
    p.add_argument('--version', action='version', version='nmrml2isa {}'.format(__version__))
    p.add_argument('-v', dest='verbose', help="show more output (default if progressbar2 is not installed)", action='store_true', default=False)
    p.add_argument('-q', dest='quiet', help="do not show any output", action='store_true', default=False)


    args = p.parse_args(argv or sys.argv[1:])


    if not progressbar:
        setattr(args, 'verbose', True)

    if args.verbose:
        print("{} input path: {}".format(os.linesep, args.in_path))
        print("output path: {}".format(os.path.join(args.out_path, args.study_id)))
        print("Sample identifier:{}{}".format(args.study_id, os.linesep))

    with warnings.catch_warnings():
        warnings.filterwarnings(args.wrng_ctrl)
        convert(args.in_path, args.out_path, args.study_id,
           usermeta=args.usermeta, verbose=args.verbose,
           jobs=args.jobs, template_directory=args.template_dir,
           quiet=args.quiet,
        )



#### DEPRECATED

@functools.wraps(main)
def run(*args, **kwargs):
    warnings.warn("nmrml2isa.parsing.run is deprecated, use "
                  "nmrml2isa.parsing.main instead", DeprecationWarning)
    main(*args, **kwargs)

@functools.wraps(convert)
def full_parse(*args, **kwargs):
    warnings.warn("nmrml2isa.parsing.full_parse is deprecated, use "
                  "nmrml2isa.parsing.convert instead", DeprecationWarning)
    convert(*args, **kwargs)


if __name__ == '__main__':
    main()


