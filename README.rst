nmrml2isa
=========

Parser to get meta information from nmrML file and parse relevant information to an ISA-Tab structure
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


|Version| |Py versions| |Git| |Build Status| |License|


Overview
--------

nmrml2isa is a Python3 program that can be used to generate an ISA-Tab structured
investigation out of nmrML files, providing the backbone of a study that can then be
edited with an ISA editing tool (see `MetaboLights pre-packaged
ISA Creator <http://www.ebi.ac.uk/metabolights/>`__)

Install
-------

See the `Installation page <http://2isa.readthedocs.io/en/latest/nmrml2isa/install.html>`__ of
the `online documentation <http://2isa.readthedocs.io/en/latest/nmrml2isa/index.html>`__.


Use
---

CLI
~~~

The parser comes with a simple one-liner:

.. code:: bash

   mzml2isa -i /path/to/nmrml_files/ -o /path/to/out_folder -s name_of_study


Module
~~~~~~

It possible to import **nmrml2isa** as a Python module:

.. code:: python

   from nmrml2isa import parsing

   in_dir = "/path/to/nmrml_files/"
   out_dir = "/path/to/out_folder/"
   study_identifier_name = "name_of_study"

   parsing.full_parse(in_dir, out_dir, study_identifier_name)


Meta extraction
~~~~~~~~~~~~~~~~

If you just want to extract the meta information without writing them
in ISA-Tab files, it is possible to do so either by running the ``nmrml2isa.nmrml``
module as main:

.. code:: bash

   python -m nmrml2isa.nmrml /path/to/your/file.nmrML
   # this will produce a JSON dict of all extracted metadata


Or within a python program with the **nmrml** submodule:

.. code:: python

   from nmrml2isa import nmrml

   nmrml_path = "/path/to/file.nmrML"
   nmrml_meta = nmrml.nmrMLmeta(nmrml_path)

   # python dictionnary
   print(nmrml_meta.meta)

   # json dictionnary
   print(nmrml_meta.meta_json)




.. |Build Status| image:: https://img.shields.io/travis/althonos/nmrml2isa.svg?style=flat&maxAge=2592000
   :target: https://travis-ci.org/althonos/nmrml2isa

.. |Py versions| image:: https://img.shields.io/pypi/pyversions/nmrml2isa.svg?style=flat&maxAge=2592000
   :target: https://pypi.python.org/pypi/nmrml2isa/

.. |Version| image:: https://img.shields.io/pypi/v/nmrml2isa.svg?style=flat&maxAge=2592000
   :target: https://pypi.python.org/pypi/nmrml2isa/

.. |Git| image:: https://img.shields.io/badge/repository-GitHub-blue.svg?style=flat&maxAge=2592000
   :target: https://github.com/althonos/nmrml2isa

.. |License| image:: https://img.shields.io/pypi/l/nmrml2isa.svg?style=flat&maxAge=2592000
   :target: https://www.gnu.org/licenses/gpl-3.0.html
