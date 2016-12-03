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
import isatools.isatab

from . import utils
import nmrml2isa.parsing



class TestMtblsStudy(unittest.TestCase):

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
            nmrml2isa.parsing.convert(self.files_dir, self.out_dir, study_id)
            self.assertIsaWasExported(study_id)
            self.assertIsaIsValid(study_id)

        def _test_study_with_inline_metadata(self):
            usermeta = '{"study": {"title": "Awesome Study"}}'
            self.files_dir = utils.download_mtbls_study(study_id)
            nmrml2isa.parsing.convert(self.files_dir, self.out_dir, study_id, usermeta=usermeta)
            self.assertIsaWasExported(study_id)
            self.assertIsaIsValid(study_id)
            with open(os.path.join(self.out_dir, study_id, 'i_Investigation.txt')) as i_file:
                self.assertIn('Awesome Study', i_file.read())

        setattr(cls, "test_{}_without_metadata".format(study_id).lower(), _test_study_without_metadata)
        setattr(cls, "test_{}_with_inline_metadata".format(study_id).lower(), _test_study_with_inline_metadata)

    def assertIsaWasExported(self, study_id):
        """checks if tempdir contains generated files"""
        for isa_glob in ("i_Investigation.txt", "a_*.txt", "s_*.txt"):
            isa_glob = os.path.join(self.out_dir, study_id, isa_glob)
            self.assertTrue(glob.glob(isa_glob))

    def assertIsaIsValid(self, study_id):
        """validates generated ISA using isa-api"""
        result = isatools.isatab.validate2(
            open(os.path.join(self.out_dir, study_id, "i_Investigation.txt")),
            self.config_dir, log_level=50,
        )
        self.assertEqual(result['errors'], [])


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    TestMtblsStudy.register_tests()
    suite.addTests(loader.loadTestsFromTestCase(TestMtblsStudy))
    return suite
