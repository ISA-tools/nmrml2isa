import owllib.ontology
import os
import json
import collections
#import xml.etree.ElementTree as etree
from lxml import etree


from nmrml2isa.owl import EasyOwl

def _urllize(accession):
        if accession.startswith('NMR'):
            return 'http://nmrML.org/nmrCV#'+accession
        elif accession.startswith('UO') or accession.startswith('CHEBI'):
            return 'http://purl.obolibrary.org/obo/'+accession
        return accession




class nmrMLmeta(object):

    Xpaths = {
        'instruments': '{root}/s:instrumentConfigurationList/s:instrumentConfiguration',
        'software':   '{root}/s:softwareList/s:software',
        'acquisition': '{root}/s:acquisition/s:acquisition1D/s:acquisitionParameterSet',
        'source_file': '{root}/s:sourceFileList/s:sourceFile'
    }


    def __init__(self, in_file, cached_onto=None):

        # setup lxml parsing
        self.in_file = in_file
        self.sample = os.path.splitext(os.path.basename(in_file))[0]

        self.tree = etree.parse(in_file)

        self._build_env()

        self.owl = EasyOwl("http://nmrml.org/cv/v1.0.rc1/nmrCV.owl", 
                            cached_onto)
        
        self.meta = collections.OrderedDict()

        self.meta['Sample Name'] = {'value': self.sample}

        # Start parsing
        self.instrument()
        self.acquisition()
        self.source_file()

        self._urllize(self.meta)

    


    def instrument(self):
        """Parses the instrument model, manufacturer and software"""
        instrument = self.tree.find(self.Xpaths['instruments'].format(**self.env), self.ns)
        cvs = instrument.iterfind('./s:cvParam', self.ns)    
        
        for cv in cvs:
            if cv.attrib['accession'] in self.owl.gen_cls.keys():
                
                self.meta['Instrument'] = {
                    'name': cv.attrib['name'], 
                    'accession':self.owl.gen_cls[cv.attrib['accession']].uri,
                    'ref': 'NMR',
                }

                self.meta['Instrument Manufacturer'] = self._get_vendor( 
                    self.owl.gen_cls[cv.attrib['accession']]._get_parents().pop() 
                )
            elif cv.attrib['accession'] in self.owl.ins_cls.keys():
                
                self.meta['Instrument'] = {
                    'name': cv.attrib['name'], 
                    'accession':self.owl.ins_cls[cv.attrib['accession']].uri,
                    'ref': 'NMR',
                }

                self.meta['Instrument Manufacturer'] = self._get_vendor( 
                    self.owl.ins_cls[cv.attrib['accession']]._get_parents().pop() \
                                                            ._get_parents().pop() 
                )
        
        soft_ref = instrument.find('s:softwareRef', self.ns).attrib['ref']
        self.software(soft_ref, 'Instrument')
                        
    def software(self, soft_ref, name):
        """Parses software information."""
        for soft in self.tree.iterfind(self.Xpaths['software'].format(**self.env), self.ns):
            
            if soft.attrib['id'] == soft_ref:
                
                self.meta[name+' software'] = { 'name': soft.attrib['name'],
                                                'ref':  soft.attrib['cvRef'],
                                                'accession': soft.attrib['accession'] }
                
                if 'version' in soft.attrib.keys():
                    self.meta[name+' software version'] = {'value': soft.attrib['version']}
                
                break

    def acquisition(self):
        acquisition = self.tree.find(self.Xpaths['acquisition'].format(**self.env), self.ns)

        self.meta['Number of scans'] = {'value': int(acquisition.attrib['numberOfScans'])}
        self.meta['Number of steady state scans'] = {'value': int(acquisition.attrib['numberOfSteadyStateScans'])}

        terms = {'./s:sampleAcquisitionTemperature': 'Temperature',
                 './s:sampleContainer': 'NMR tube type',
                 './s:spinningRate': 'Spinning Rate',
                 './s:relaxationDelay': 'Relaxation Delay',
                 './s:pulseSequence/s:userParam': 'Pulse sequence name',
                 './s:DirectDimensionParameterSet/s:acquisitionNucleus': 'Acquisition Nucleus',
                 './s:DirectDimensionParameterSet/s:decouplingNucleus': 'Decoupling Nucleus',
                 './s:DirectDimensionParameterSet/s:effectiveExcitationField': 'Effective Excitation Field',
                 './s:DirectDimensionParameterSet/s:sweepWidth': 'Sweep Width',
                 './s:DirectDimensionParameterSet/s:pulseWidth': 'Pulse Width',
                 './s:DirectDimensionParameterSet/s:irradiationFrequency': 'Irradiation Frequency',
                 './s:DirectDimensionParameterSet/s:samplingStrategy': 'Sampling Strategy',
                 }


        for childpath, name in terms.items():
            child = acquisition.find(childpath, self.ns)
            
            self.meta[name] = {}

            if 'value' in child.attrib.keys():
                self.meta[name]['value'] = child.attrib['value']
            
            if 'name' in child.attrib.keys():
                self.meta[name]['name'] = child.attrib['name']

            if 'unitName' in child.attrib.keys():
                self.meta[name]['unit'] = { 'name': child.attrib['unitName'],
                                            'ref': child.attrib['unitCvRef'],
                                            'accession': child.attrib['unitAccession'] }

            if 'cvRef' in child.attrib.keys():
                self.meta[name]['ref'] = child.attrib['cvRef']
                self.meta[name]['accession'] = child.attrib['accession']

    def source_file(self):
        source_files = self.tree.iterfind(self.Xpaths['source_file'].format(**self.env), self.ns)        

        terms = [
            {'hook': lambda cv: cv.attrib['accession'] in self.owl.fmt_cls.keys(), 'name':'Format'},
            {'hook': lambda cv: cv.attrib['accession'] in self.owl.fid_cls.keys(), 'name':'Type'},
            {'hook': lambda cv: cv.attrib['accession'] in self.owl.pls_cls.keys(), 'name':'Type'},
            {'hook': lambda cv: cv.attrib['accession'] in self.owl.acq_cls.keys(), 'name':'Type'},
            {'hook': lambda cv: cv.attrib['accession'] in self.owl.prc_cls.keys(), 'name':'Type'},

            {'hook': lambda cv: cv.attrib['accession'] == 'NMR:1000319', 'name':'Type'},

        ]

        names = {
            'fid': 'Free Induction Decay Data',
            'pulseprogram': 'Pulse Sequence Data',
            'acqus': 'Acquisition Parameter Data',
            'procs': 'Processing Parameter Data',
            '1r': '1r Data',
        }

        for source in source_files:
            source_terms = {}

            if source.attrib['name'] in names.keys():
                name = names[source.attrib['name']]
                self.meta[name+' File'] = { 
                    'value': self.sample + source.attrib['location'].split(self.sample)[-1]
                }
                

                self._parse_cv(source, terms, name)

        
                

    def _urllize(self, starting_point):

        for k,v in starting_point.items():
            
            if isinstance(v, dict):
                for key, param in v.items():

                    if isinstance(param, dict):
                        self._urllize(param)

                    elif key=='accession':
                        if 'http' not in param:
                            param = _urllize(param)

            elif k == 'accession':
                v = _urllize(v)
                

    def _parse_cv(self, node, terms, name):

        for cv in node.iterfind('./s:cvParam', self.ns):
            for term in terms:

                if term['hook'](cv):
                        self.meta[name+' '+term['name']] = { 
                            'name': cv.attrib['name'],
                            'ref': cv.attrib['cvRef'],
                            'accession': cv.attrib['accession']
                        }


    def _get_vendor(self, manufacturer_node):
        """Get vendor name/ref/accession from an instrument generic model"""

        manufacturer = manufacturer_node.labels.copy().pop().value.replace(' instrument model', '') \
                        
        

        if manufacturer in self.owl.ven_cls.keys():
            return {
                'name': manufacturer,
                'ref': 'NMR',
                'accession': self.owl.ven_cls[manufacturer].uri
            }
        else:
            return {'name': manufacturer}
          

    def _build_env(self):

        try:
            self.ns = self.tree.getroot().nsmap
            self.ns['s'] = self.ns[None]
            del self.ns[None]
        except AttributeError:
            self.ns = {'s': self.tree.getroot().tag[1:].split('}')[0] }

        self.env = {}

        if self.tree.find('./s:nmrML', self.ns) is None:
            self.env['root'] = '.'


    @property
    def meta_json(self):
        return json.dumps(self.meta, indent=4, sort_keys=True)

    @property
    def meta_isa(self):
        keep = ["data transformation", "data transformation software version", "data transformation software",
                "term_source", "Raw Spectral Data File", "MS Assay Name", "Derived Spectral Data File", "Sample Name",
                "Acquisition Parameter Data File", "Free Induction Decay Data File", ]

        meta_isa = collections.OrderedDict()

        for meta_name in self.meta:
            if meta_name in keep:
                meta_isa[meta_name] = self.meta[meta_name]
            else:
                #print(meta_name)
                meta_isa["Parameter Value["+meta_name+"]"] = self.meta[meta_name]
        return meta_isa
    
    @property
    def isa_json(self):
        return json.dumps(self.meta_isa, indent=4, sort_keys=True)



if __name__ == '__main__':
    import sys
    print(nmrMLmeta(sys.argv[1]).isa_json)
    




