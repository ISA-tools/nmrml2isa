import os
import sys
import glob
import argparse
import textwrap
import warnings
import json
import owllib.ontology

try:
    import progressbar as pb
    PB_AVAILABLE = True
except ImportError:
    PB_AVAILABLE = False

import nmrml2isa.isa as isa
import nmrml2isa.nmrml as nmrml


SUPPORTED_ANALYSIS_TYPES = ('MS')

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
               args.verbose)





def full_parse(in_dir, out_dir, study_identifer, verbose=False):
    """ Parses every study from *in_dir* and then creates ISA files.

    A new folder is created in the out directory bearing the name of
    the study identifier. 

    :param str in_dir:              path to directory containing studies
    :param str out_dir:          path to out directory
    :param str study_identifier: name of the study (directory to create)
    """

    # get mzML file in the example_files folder
    nmrml_path = os.path.join(in_dir, "*.nmrML")
    
    if verbose:
        print(nmrml_path)

    
    nmrml_files = [mw for mw in glob.glob(nmrml_path)][:10]
    nmrml_files.sort()

    metalist = []
    if nmrml_files:

        print('Loading ontology...')
        owl = owllib.ontology.Ontology()
        owl.load(location="http://nmrml.org/cv/v1.0.rc1/nmrCV.owl")

        # get meta information for all files
        if not verbose:
            pbar = pb.ProgressBar(widgets=['Parsing: ',
                                           pb.Counter(), '/', str(len(nmrml_files)), 
                                           pb.Bar(marker="█", left=" |", right="| "),
                                           pb.AdaptiveETA()])
            for i in pbar(nmrml_files):
                metalist.append(nmrml.nmrMLmeta(i, owl).meta)

        else:
            for i in nmrml_files:
                print("Parsing nmrML file: {}".format(i))
                meta = nmrml.nmrMLmeta(i, owl).meta

                metalist.append(meta)


        # update isa-tab file
        if metalist:
            if verbose:
                print("Parse nmrML meta information into ISA-Tab structure")
            isa_tab_create = isa.ISA_Tab(metalist, out_dir, study_identifer)
        else:
            if verbose:
                print("No files were created.")
    
    else:
        warnings.warn("No files were found in directory."), UserWarning
        #print("No files were found.")    


if __name__ == '__main__':
    run()