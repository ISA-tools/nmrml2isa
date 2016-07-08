# coding: utf-8
from __future__ import print_function


import sys
import os
import glob
import argparse
import textwrap
import warnings
import json
from datetime import datetime
import pronto
import multiprocessing
import multiprocessing.pool
from functools import partial

try:
    import progressbar as pb
    PB_AVAILABLE = True
except ImportError:
    PB_AVAILABLE = False

import nmrml2isa.isa as isa
import nmrml2isa.nmrml as nmrml


def parse_task(owl, f, verbose):
    if verbose:
        print('[{}] Started  parsing : {}'.format(datetime.now().time().strftime('%H:%M:%S'), f))
    else:
        print('\r[{}] Started  parsing : {}'.format(datetime.now().time().strftime('%H:%M:%S'), os.path.basename(f)), end='')
    n = nmrml.nmrMLmeta(f, owl).meta
    if verbose:
        print('[{}] Finished parsing : {}'.format(datetime.now().time().strftime('%H:%M:%S'), f))
    return n

def run():
    """ Runs **mzml2isa** from the command line"""
    p = argparse.ArgumentParser(prog='nmrml2isa',
                            formatter_class=argparse.RawDescriptionHelpFormatter,
                            description='''Extract meta information from nmrML files and create ISA-tab structure''',
                            )

    p.add_argument('-i', dest='in_dir', help='in folder containing mzML files', required=True)
    p.add_argument('-o', dest='out_dir', help='out folder, new directory will be created here', required=True)
    p.add_argument('-s', dest='study_name', help='study identifier name', required=True)
    #p.add_argument('-n', dest='split', help='do NOT split assay files based on polarity', action='store_false', default=True)
    p.add_argument('-v', dest='verbose', help='print more output', action='store_true', default=False)
    p.add_argument('-c', dest='process_count', help='number of processes to spawn (default: nbr of cpu * 4)',
                         action='store', default=None)

    args = p.parse_args()

    if not PB_AVAILABLE:
        setattr(args, 'verbose', True)

    if args.verbose:
        print("{} in directory: {}".format(os.linesep, args.in_dir))
        print("out directory: {}".format(os.path.join(args.out_dir, args.study_name)))
        print("Sample identifier name:{}{}".format(args.study_name, os.linesep))

    full_parse(args.in_dir, args.out_dir, args.study_name,
               #args.usermeta if args.usermeta else {},
               #args.split,
               args.verbose, args.process_count)




def full_parse(in_dir, out_dir, study_identifer, verbose=False, process_count=None):
    """ Parses every study from *in_dir* and then creates ISA files.

    A new folder is created in the out directory bearing the name of
    the study identifier.

    :param str in_dir:              path to directory containing studies
    :param str out_dir:          path to out directory
    :param str study_identifier: name of the study (directory to create)
    """

    print(''.join(['\r'*(not verbose),
            '[{}] Starting nmrml2isa'.format(datetime.now().time().strftime('%H:%M:%S')),
            30*' ']), end='\n'*(verbose)
        )

    # get mzML file in the example_files folder
    nmrml_path = os.path.join(in_dir, "*.nmrML")

    nmrml_files = [mw for mw in glob.glob(nmrml_path)]
    nmrml_files.sort()

    print(''.join(['\r'*(not verbose),
            '[{}] Creating multiproccessing Pool'.format(datetime.now().time().strftime('%H:%M:%S')),
            30*' ']), end='\n'*(verbose)
        )

    pool = multiprocessing.pool.Pool(process_count or multiprocessing.cpu_count()*4)

    metalist = []
    if nmrml_files:

        print(''.join(['\r'*(not verbose),
            '[{}] Loading ontology'.format(datetime.now().time().strftime('%H:%M:%S')),
            30*' ']), end='\n'*(verbose)
        )
        try:
            owl = pronto.Ontology("http://nmrml.org/cv/v1.0.rc1/nmrCV.owl")
        except:
            owl = pronto.Ontology(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nmrCV.owl'))


        # get meta information for all files
        #task = partial(parse_task, owl)
        metalist = pool.starmap(parse_task, ((owl, x, verbose) for x in nmrml_files))

        pool.close()


        #if not verbose:
        #    pbar = pb.ProgressBar(widgets=['Parsing: ',
        #                                   pb.Counter(), '/', str(len(nmrml_files)),
        #                                   pb.Bar(marker="█", left=" |", right="| "),
        #                                   pb.AdaptiveETA()])
        #    for i in pbar(nmrml_files):
        #        metalist.append(nmrml.nmrMLmeta(i, owl).meta)

        #else:
        #    for i in nmrml_files:
        #        print("Parsing nmrML file: {}".format(i))
        #        meta = nmrml.nmrMLmeta(i, owl).meta
        #
        #    metalist.append(meta)



        # update isa-tab file
        if metalist:
            print(''.join(['\r'*(not verbose),
            '[{}] Writing ISA-Tab files'.format(datetime.now().time().strftime('%H:%M:%S')),
            ' '*30]), end='\n'*verbose)
            isa_tab_create = isa.ISA_Tab(out_dir, study_identifer).write(metalist)

            print(''.join(['\r'*(not verbose),
            '[{}] Finished writing ISA-Tab files'.format(datetime.now().time().strftime('%H:%M:%S'), out_dir),
            ' '*30]), end='\n')

        else:
            if verbose:
                warnings.warn("No starts were created.", UserWarning)
        pool.join()

    else:
        warnings.warn("No files were found in directory.", UserWarning)
        #print("No files were found.")





if __name__ == '__main__':
    run()
