from __future__ import (
    absolute_import,
    unicode_literals,
)

import sys
import six
import json
import os
import glob
import shutil
import ftplib
import unittest
import contextlib
import warnings
import isatools.isatab

from . import utils
from .abstract_test_isa import AbstractTestIsa
import nmrml2isa.parsing



class TestMtblsStudy(AbstractTestIsa):

    @classmethod
    def setUpClass(cls):
        cls.config_dir = utils.download_configuration_files()
        cls.out_dir = os.path.join(utils.TESTDIR, 'run')
        os.makedirs(cls.out_dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out_dir)

    @classmethod
    def get_concerned_studies(cls):
        study_exts = six.BytesIO()

        with contextlib.closing(ftplib.FTP("ftp.ebi.ac.uk")) as ebi_ftp:
            ebi_ftp.login()
            ebi_ftp.cwd("/pub/databases/metabolights/study_file_extensions")
            ebi_ftp.retrbinary("RETR ml_file_extension.json", study_exts.write)

        stats = json.loads(study_exts.getvalue().decode('utf-8'))
        return [s['id'] for s in stats if '.nmrML' in s['extensions']]

    @classmethod
    def register_tests(cls):
        cls.studies = cls.get_concerned_studies()
        for study_id in cls.studies:
            cls.add_test(study_id)

    @classmethod
    def add_test(cls, study_id):
        utils.download_mtbls_study(study_id)

        def _test_study_without_metadata(self):
            self.files_dir = utils.download_mtbls_study(study_id)
            nmrml2isa.parsing.convert(self.files_dir, self.out_dir, study_id,
                                      quiet=True)
            self.assertIsaWasExported(study_id)
            self.assertIsaIsValid(study_id)

        def _test_study_with_inline_metadata(self):
            usermeta = '{"study": {"title": "Awesome Study"}}'
            self.files_dir = utils.download_mtbls_study(study_id)
            nmrml2isa.parsing.convert(self.files_dir, self.out_dir, study_id,
                                      usermeta=usermeta, quiet=True)
            self.assertIsaWasExported(study_id)
            self.assertIsaIsValid(study_id)
            with open(os.path.join(self.out_dir, study_id, 'i_Investigation.txt')) as i_file:
                self.assertIn('Awesome Study', i_file.read())

        def _test_study_with_xlsx_metadata(self):
            usermeta = os.path.join(utils.TESTDIR, "data", "usermeta.xlsx")
            self.files_dir = utils.download_mtbls_study(study_id)
            nmrml2isa.parsing.convert(self.files_dir, self.out_dir, study_id,
                                      usermeta=usermeta, quiet=True)
            self.assertIsaWasExported(study_id)
            self.assertIsaIsValid(study_id)
            with open(os.path.join(self.out_dir, study_id, 'i_Investigation.txt')) as i_file:
                self.assertIn("The best extraction you've ever seen", i_file.read())

        def _test_study_with_json_metadata(self):
            usermeta = os.path.join(utils.TESTDIR, "data", "usermeta.json")
            self.files_dir = utils.download_mtbls_study(study_id)
            nmrml2isa.parsing.convert(self.files_dir, self.out_dir, study_id,
                                      usermeta=usermeta, quiet=True)
            self.assertIsaWasExported(study_id)
            self.assertIsaIsValid(study_id)
            with open(os.path.join(self.out_dir, study_id, 'i_Investigation.txt')) as i_file:
                self.assertIn('Martin Larralde, Tom Lawson, Reza Salek', i_file.read())

        setattr(cls, "test_{}_without_metadata".format(study_id).lower(), _test_study_without_metadata)
        setattr(cls, "test_{}_with_inline_metadata".format(study_id).lower(), _test_study_with_inline_metadata)
        setattr(cls, "test_{}_with_xlsx_metadata".format(study_id).lower(), _test_study_with_xlsx_metadata)
        setattr(cls, "test_{}_with_json_metadata".format(study_id).lower(), _test_study_with_json_metadata)




def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    TestMtblsStudy.register_tests()
    suite.addTests(loader.loadTestsFromTestCase(TestMtblsStudy))
    return suite

def setUpModule():
    warnings.simplefilter('ignore')

def tearDownModule():
    warnings.simplefilter(warnings.defaultaction)
