#!/usr/bin/env python
# coding: utf-8


from setuptools import setup, find_packages
import sys
import nmrml2isa


setup(
    name='nmrml2isa',
    version=nmrml2isa.__version__,
    packages=find_packages(),
    py_modules=['mzml2isa'],

    author=nmrml2isa.__author__,

    author_email=nmrml2isa.__email__,

    description="nmrml2isa - nmrML to ISA-Tab parsing tool",
    long_description=open('README.rst').read(),

    install_requires=open('requirements.txt').read().splitlines()
                      if sys.version_info[0]==3 \
                      else open('requirements-py2.txt').read().splitlines(),

    include_package_data=True,

    url='http://github.com/althonos/nmrml2isa',

    classifiers=[
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
    "Topic :: Text Processing :: Markup :: XML",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
    "Topic :: Scientific/Engineering :: Chemistry",
    "Topic :: Utilities",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: OS Independent",
    ],

    entry_points = {
        'console_scripts': [
            'nmrml2isa = nmrml2isa.parsing:run',
        ],
    },

    license="GPLv3",

    keywords=['Metabolomics', 'NMR', 'Nuclear Magnetic Resonance', 'ISA Tab', 'nmrML', 'metabolites', 'parsing'],

)
