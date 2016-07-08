import string
import os
import csv

try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap

import nmrml2isa

class ISA_Tab(object):

    def __init__(self, out_dir, name, usermeta=None):

        # Create one or several study files / one or several study section in investigation

        dirname = os.path.dirname(os.path.realpath(__file__))
        self.usermeta = usermeta or {}
        self.isa_env = {
            'out_dir': os.path.join(out_dir, name),
            'Study Identifier':  name,
            'Study file name': 's_{}.txt'.format(name),
            'Assay file name': 'a_{}_metabolite_profiling_NMR_spectroscopy.txt'.format(name),
            'default_path': os.path.join(dirname, 'default'),
        }

    def write(self, metalist):

        self.isa_env['Platform'] = next((meta['Instrument'] for meta in metalist if 'Instrument' in meta), '')

        self.isa_env['Converter'] = nmrml2isa.__name__
        self.isa_env['Converter version'] = nmrml2isa.__version__

        if not os.path.exists(self.isa_env['out_dir']):
            os.makedirs(self.isa_env['out_dir'])

        h,d = self.make_assay_template(metalist)

        self.create_investigation(metalist)
        self.create_study(metalist)
        self.create_assay(metalist, h, d)

    def make_assay_template(self, metalist):

        template_a_path = os.path.join(self.isa_env['default_path'], 'a_nmrML.txt')

        with open(template_a_path, 'r') as a_in:
            headers, data = [x.strip().replace('"', '').split('\t') for x in a_in.readlines()]

        i = 0
        while i < len(headers):
            header, datum = headers[i], data[i]

            if '{{' in datum and 'Term' not in header:
                entry_list = metalist[0][self.unparameter(header)]['entry_list']
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

            writer=csv.writer(a_out, quotechar='"', quoting=csv.QUOTE_ALL, delimiter='\t')
            writer.writerow(headers)

            for meta in metalist:
                writer.writerow( [ fmt.vformat(x, None, ChainMap(meta, self.usermeta)) for x in data] )


    def create_study(self, metalist):

        template_s_path = os.path.join(self.isa_env['default_path'], 's_nmrML.txt')
        new_s_path = os.path.join(self.isa_env['out_dir'], self.isa_env['Study file name'])

        fmt = PermissiveFormatter()

        with open(template_s_path, 'r') as s_in:
            headers, data = s_in.readlines()

        with open(new_s_path, 'w') as s_out:
            s_out.write(headers)
            for meta in metalist:
                s_out.write(fmt.vformat(data, None, ChainMap(meta, self.usermeta)))

    def create_investigation(self, metalist):
        investigation_file = os.path.join(self.isa_env['default_path'], 'i_nmrML.txt')
        new_i_path = os.path.join(self.isa_env['out_dir'], 'i_Investigation.txt')

        meta = metalist[0]
        fmt = PermissiveFormatter()

        with open(investigation_file, 'r') as i_in:
            with open(new_i_path, "w") as i_out:
                for l in i_in:

                    ## FORMAT SECTIONS WHERE MORE THAN ONE VALUE IS ACCEPTED
                    #if l.startswith('Study Person'):
                    #    person_row = l.strip().split('\t')
                    #    l = person_row[0]
                    #    for person in meta['contacts']:
                    #        l +=  '\t' + fmt.format(person_row[1], study_contact=person)
                    #    l += '\n'

                    l = fmt.vformat(l, None, ChainMap(self.isa_env, meta, self.usermeta))
                    i_out.write(l)

    @staticmethod
    def unparameter(string):
        return string.replace('Parameter Value[', '').replace(']', '')



class PermissiveFormatter(string.Formatter):
    """A formatter that replace wrong and missing key with a blank."""
    def __init__(self, missing='', bad_fmt=''):
        self.missing, self.bad_fmt=missing, bad_fmt

    def get_field(self, field_name, args, kwargs):
        # Handle a key not found
        try:
            val=super(PermissiveFormatter, self).get_field(field_name, args, kwargs)
        except (KeyError, AttributeError, IndexError):
            val=None,field_name
        return val

    def format_field(self, value, spec):
        # handle an invalid format
        if value==None: return self.missing
        try:
            return super(PermissiveFormatter, self).format_field(value, spec)
        except ValueError:
            if self.bad_fmt is not None: return self.bad_fmt
            else: raise
