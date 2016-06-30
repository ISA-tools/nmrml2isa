import string
import os
import collections
import csv

class ISA_Tab(object):

    def __init__(self, metalist, out_dir, name):

        # Create one or several study files / one or several study section in investigation

        dirname = os.path.dirname(os.path.realpath(__file__))
        self.isa_env = {
            'out_dir': os.path.join(out_dir, name),
            'study_identifier':  name, 
            'study_file_name': 's_{}.txt'.format(name),
            'assay_file_name': 'a_{}_metabolite_profiling_mass_spectrometry.txt'.format(name),
            'investigation_file_name': 'i_Investigation.txt',
            'default_path': os.path.join(dirname, 'default'),
            'platform': {},
        }


        if not os.path.exists(self.isa_env['out_dir']):
            os.makedirs(self.isa_env['out_dir'])       

        self.make_assay_headers(metalist)
        
        self.create_investigation(metalist)     
        self.create_study(metalist)
        self.create_assay(metalist)

    def make_assay_headers(self, metalist):

        keep = ["data transformation", "data transformation software version", "data transformation software",
                "term_source", "Raw Spectral Data File", "MS Assay Name", "Derived Spectral Data File", "Sample Name",
                "Acquisition Parameter Data File", "Free Induction Decay Data File", ]

        self.assay_headers = collections.OrderedDict()
        for meta in metalist: 
            
            for k,v in meta.items():
                print(k, ':', v)
                if k not in self.assay_headers.keys():
                    self.assay_headers[k] = { 'name': 'Parameter Value[{}]'.format(k) if k not in keep else k, 
                                              'is_valued': 'value' in v.keys() if isinstance(v, dict) else False,
                                              'has_units': 'unit' in v.keys() if isinstance(v, dict) else False,
                                              'has_accession': 'accession' in v.keys() if isinstance(v, dict) else False, 
                                            }
        #print(self.assay_headers['Irradiation Frequency'])

        

    def create_assay(self, metalist):
        template_a_path = os.path.join(self.isa_env['default_path'], 'a_nmr_metabolite_profiling_NMR_spectroscopy.txt')
        new_a_path = os.path.join(self.isa_env['out_dir'], self.isa_env['assay_file_name'])

        fmt = PermissiveFormatter()

        with open(template_a_path, 'r') as a_in:
            headers, data = [x.strip().replace('"', '').split('\t') for x in a_in.readlines()]

        
        param_index = headers.index('Parameter Value[Instrument]') + 3

        additional_headers, additional_data = [], []
        
        for key, param in self.assay_headers.items():
            
            additional_headers.append(param['name'])
            if param['is_valued']:
                additional_data.append('{'+fmt.format('{n}[value]', n=key)+'}')
            else:
                additional_data.append('{'+fmt.format('{n}[name]', n=key)+'}')
            
            if param['has_accession']:
                additional_headers.append('Term Source REF')
                additional_headers.append('Term Accession Number')

                additional_data.append('{'+fmt.format('{n}[ref]', n=key)+'}')
                additional_data.append('{'+fmt.format('{n}[accession]', n=key)+'}')

            if param['has_units']:
                additional_headers.append('Unit')
                additional_headers.append('Term Source REF')
                additional_headers.append('Term Accession Number')                

                additional_data.append('{'+fmt.format('{n}[unit][name]', n=key)+'}')
                additional_data.append('{'+fmt.format('{n}[unit][ref]', n=key)+'}')
                additional_data.append('{'+fmt.format('{n}[unit][accession]', n=key)+'}')

            
        

        

        headers = headers[:param_index] + additional_headers + headers[param_index:]
        data = data[:param_index] + additional_data + data[param_index:]

        fmt = PermissiveFormatter()

        with open(new_a_path, 'w') as a_out:

            writer=csv.writer(a_out, quotechar='"', quoting=csv.QUOTE_ALL, delimiter='\t')
            # Write headers
            #a_out.write( headers )
            writer.writerow(headers)

            for meta in metalist:
                #a_out.write( fmt.format(data, **meta) )
                writer.writerow( [ fmt.format(x, **meta) for x in data] )




    def create_study(self, metalist):
        pass

    def create_investigation(self, metalist):
        pass





class PermissiveFormatter(string.Formatter):
    """A formatter that replace wrong and missing key with a blank."""
    def __init__(self, missing='', bad_fmt=''):
        self.missing, self.bad_fmt=missing, bad_fmt

    def get_field(self, field_name, args, kwargs):
        # Handle a key not found
        try:
            val=super(PermissiveFormatter, self).get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
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
