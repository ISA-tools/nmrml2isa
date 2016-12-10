from __future__ import (
    absolute_import,
    print_function,
)

import six
import os
import sys
import glob
import ftplib
import contextlib
import tempfile
import subprocess
import shutil
import atexit
import multiprocessing
import multiprocessing.pool


TESTDIR = os.path.dirname(os.path.abspath(__file__))
MAINDIR = os.path.dirname(TESTDIR)

IN_CI = os.environ.get('CI', '').lower() == "true"


if IN_CI:
    config_directory = os.path.join(os.environ.get("HOME"), "MetaboLightsConfig")
    studies_directory = os.path.join(os.environ.get("HOME"), "MetaboLightsStudies")
    examples_directory = os.path.join(os.environ.get("HOME"), "nmrML")
else:
    config_directory = tempfile.mkdtemp()
    studies_directory = tempfile.mkdtemp()
    examples_directory = tempfile.mkdtemp()

def vprint(*args, **kwargs):
    if '-v' in sys.argv or '--verbose' in sys.argv:
        print(*args, **kwargs)

def _download_mtbls_file(args):
    file, directory = args
    with contextlib.closing(six.moves.http_client.HTTPConnection("ftp.ebi.ac.uk")) as ebi_http:
        ebi_http.connect()
        ebi_http.request("GET", file)
        response = ebi_http.getresponse()
        with open(os.path.join(directory, os.path.basename(file)), 'wb') as dest_file:
            dest_file.write(response.read())

def download_mtbls_study(study_id, dl_directory=None):

    STUDY_DIR = "/pub/databases/metabolights/studies/public/{}".format(study_id)
    dl_directory = dl_directory or os.path.join(studies_directory, study_id)

    # do not download mtbls files again if found
    # already in cache directory (for Travis-CI only)
    #cls.vprint("\ndownloading {} files to {} ... ".format(study_id, dl_directory), end="")
    vprint("\ndownloading {} files to {} ... ".format(study_id, dl_directory), end="")
    if glob.glob(os.path.join(studies_directory, study_id, "*.[n|N][m|M][r|R][m|M][l|L]")):
        #cls.vprint("skip")
        vprint("skip")
        return dl_directory

    if not os.path.exists(dl_directory):
        os.mkdir(dl_directory)
    with contextlib.closing(ftplib.FTP("ftp.ebi.ac.uk")) as ebi_ftp:
        ebi_ftp.login()
        ebi_ftp.cwd(STUDY_DIR)
        files_list = [os.path.join(STUDY_DIR, study_file) for study_file in ebi_ftp.nlst() if study_file != "audit"]
    #cls.vprint("ok")

    pool = multiprocessing.pool.Pool(multiprocessing.cpu_count()*8)
    #pool.map(cls._download_mtbls_file, [(f, dl_directory) for f in files_list])
    pool.map(_download_mtbls_file, [(f, dl_directory) for f in files_list])
    vprint("ok")

    return dl_directory

def download_configuration_files(dl_directory=None):

    CONFIG_DIR = "/pub/databases/metabolights/submissionTool/configurations/"
    dl_directory = dl_directory or config_directory #cls.config_directory

    # do not download config files again if found
    # already in cache directory (for Travis-CI only)
    #cls.vprint("\ndownloading MetaboLights configuration files to {} ...".format(dl_directory), end="")
    vprint("\ndownloading MetaboLights configuration files to {} ...".format(dl_directory), end="")
    if IN_CI:
        if glob.glob(os.path.join(dl_directory, "*.xml")): # skip if configs are in cache
            #cls.vprint("skip")
            vprint("skip")
            return dl_directory

    with contextlib.closing(ftplib.FTP("ftp.ebi.ac.uk")) as ebi_ftp:
        ebi_ftp.login()
        ebi_ftp.cwd(CONFIG_DIR)
        MTBLS_CONFIG_DIR = next(x for x in ebi_ftp.nlst() if x.startswith("MetaboLightsConfig"))
        ebi_ftp.cwd(MTBLS_CONFIG_DIR)
        for config_file in ebi_ftp.nlst():
            if not os.path.isfile(os.path.join(dl_directory, config_file)):
                with open(os.path.join(dl_directory, config_file), 'wb') as dest_file:
                    ebi_ftp.retrbinary("RETR {}".format(config_file), dest_file.write)
    #cls.vprint("ok")
    vprint("ok")

    return dl_directory

def download_nmrml_repository(dl_directory=None):

    NMRML_URL = "https://github.com/nmrML/nmrML"
    dl_directory = dl_directory or examples_directory

    vprint("\ndownloading nmrML/nmrML repository to {} ...".format(dl_directory))
    if IN_CI:
        if os.path.isdir(os.path.join(dl_directory, 'examples')):
            vprint("skip")
            return dl_directory

    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    subprocess.call(["git", "clone", NMRML_URL, dl_directory, "--depth", "1"] +  (['-q'] if not verbose else []))

    return dl_directory

def cleanUp():
    if not IN_CI:
        shutil.rmtree(config_directory)
        shutil.rmtree(studies_directory)
        shutil.rmtree(examples_directory)

atexit.register(cleanUp)
