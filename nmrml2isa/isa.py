# coding: utf-8
from __future__ import (
    print_function,
    absolute_import,
    unicode_literals,
)

import string
import six
import os
import csv

from . import __version__, __author__, __email__, __name__
from .utils import ChainMap, PermissiveFormatter

class ISA_Tab(object):

    def __init__(self, out_dir, name, usermeta=None, template_directory=None):

        # Create one or several study files / one or several study section in investigation

        dirname = os.path.dirname(os.path.realpath(__file__))
        self.usermeta = usermeta or {}
        self.isa_env = {
            'out_dir': os.path.join(out_dir, name),
            'Study Identifier':  name,
            'Study file name': 's_{}.txt'.format(name),
            'Assay file name': 'a_{}_metabolite_profiling_NMR_spectroscopy.txt'.format(name),
            'default_path': os.path.join(dirname, 'default'),
            'template_path': template_directory or os.path.join(dirname, 'default')
        }

    def write(self, metalist):

        self.isa_env['Platform'] = next((meta['Instrument'] for meta in metalist if 'Instrument' in meta), '')

        self.isa_env['Converter'] = __name__
        self.isa_env['Converter version'] = __version__

        if not os.path.exists(self.isa_env['out_dir']):
            os.makedirs(self.isa_env['out_dir'])

        h,d = self.make_assay_template(metalist)

        self.create_investigation(metalist)
        self.create_study(metalist)
        self.create_assay(metalist, h, d)

    def make_assay_template(self, metalist):

        template_a_path = os.path.join(self.isa_env['template_path'], 'a_nmrML.txt')

        with open(template_a_path, 'r') as a_in:
            headers, data = [x.strip().replace('"', '').split('\t') for x in a_in.readlines()]

        i = 0
        while i < len(headers):
            header, datum = headers[i], data[i]

            if '{{' in datum and 'Term' not in header:
                entry_list = metalist[0][self.unparameter(header)]['entry_list'] \
                                if self.unparameter(header) in metalist[0].keys() \
                                else [ None ]

                hsec, dsec = (headers[i:i+3], data[i:i+3]) \
                                if headers[i+1] == "Term Source REF" \
                                else (headers[i:i+1], data[i:i+1])

                headers[:] = headers[:i] + headers[i+len(hsec):] # Remove the sections we are
                data[:] =    data[:i]    +    data[i+len(dsec):] # going to format and insert

                for n in reversed(range(len(entry_list))):
                    for (h,d) in zip(reversed(hsec),reversed(dsec)):
                        headers.insert(i, h)
                        data.insert(i, d.format(n))

            i+= 1

        return headers, data

    def create_assay(self, metalist, headers, data):
        #template_a_path = os.path.join(self.isa_env['default_path'], 'a_imzML_parse.txt')
        new_a_path = os.path.join(self.isa_env['out_dir'], self.isa_env['Assay file name'])

        fmt = PermissiveFormatter()

        with open(new_a_path, 'w') as a_out:

            writer=csv.writer(a_out, quotechar=str('"'), quoting=csv.QUOTE_ALL, delimiter=str('\t'))
            writer.writerow(headers)

            for meta in metalist:
                writer.writerow( [ fmt.vformat(x, None, ChainMap(meta, self.usermeta)) for x in data] )

    def create_study(self, metalist):

        template_s_path = os.path.join(self.isa_env['template_path'], 's_nmrML.txt')
        new_s_path = os.path.join(self.isa_env['out_dir'], self.isa_env['Study file name'])

        fmt = PermissiveFormatter()

        with open(template_s_path, 'r') as s_in:
            headers, data = s_in.readlines()

        with open(new_s_path, 'w') as s_out:
            s_out.write(headers)
            for meta in metalist:
                s_out.write(fmt.vformat(data, None, ChainMap(meta, self.usermeta)))

    def create_investigation(self, metalist):
        investigation_file = os.path.join(self.isa_env['template_path'], 'i_nmrML.txt')
        new_i_path = os.path.join(self.isa_env['out_dir'], 'i_Investigation.txt')

        meta = metalist[0]
        fmt = PermissiveFormatter()

        chained = ChainMap(meta, self.usermeta)

        with open(investigation_file, 'r') as i_in:
            with open(new_i_path, "w") as i_out:
                for l in i_in:

                    if "{{" in l:
                        l, value = l.strip().split('\t')
                        label = value[3:].split('[')[0]

                        if label in chained:
                            for k in range(len(chained[label])):
                                l = '\t'.join([l, value.format(k)])
                            l += '\n'
                        else:
                            l = "\t".join([l, '\"\"', '\n'])

                    l = fmt.vformat(l, None, ChainMap(self.isa_env, meta, self.usermeta))
                    i_out.write(l)

    @staticmethod
    def unparameter(string):
        return string.strip()[16:-1]


