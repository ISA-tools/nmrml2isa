import os
import json
import collections
import pronto
import xml.etree.ElementTree as etree



class nmrMLmeta(object):

    xpaths = {
        'instruments':    '{root}/s:instrumentConfigurationList/s:instrumentConfiguration',
        'software':       '{root}/s:softwareList/s:software',
        'acquisition':    '{root}/s:acquisition/s:acquisition1D/s:acquisitionParameterSet',
        'source_file':    '{root}/s:sourceFileList/s:sourceFile',
        'contacts':       '{root}/s:contactList/s:contact',
        'processing':     '{root}/s:dataProcessingList/s:dataProcessing/s:processingMethod',
        'spectrum':       '{root}/s:spectrum/s:spectrum1D',
        'probehead':      '{root}/s:instrumentConfigurationList/s:instrumentConfiguration/s:userParam',
        'pulse_sequence': '{root}/s:acquisition/s:acquisition1D/s:acquisitionParameterSet/s:pulseSequence/s:userParam',
    }

    gyromagnetic_table = {
        'CHEBI_49637': 42.576, # 1H
        'CHEBI_29237':  6.536, # 2H
        'CHEBI_36928': 10.705, # 13C
        'CHEBI_36938':  3.077, # 14N
        'CHEBI_36934': -4.316, # 15N
        'CHEBI_33819': -5.772, # 17O
        'CHEBI_37971': 17.235, # 31P
    }

    nmrcv = None

    def __init__(self, in_file, cached_onto=None):

        # setup lxml parsing
        self.in_file = in_file
        self.sample = os.path.splitext(os.path.basename(in_file))[0]

        parser = etree.XMLParser()
        self.tree = etree.parse(in_file, parser=parser)

        self._build_env()
        self._load_ontology(cached_onto)


        self.meta = collections.OrderedDict()
        self.meta['Sample Name'] = {'value': self.sample}
        self.meta['Derived Spectral Data File'] = {'value': self.in_file}
        self.meta['NMR Assay Name'] = {'value': self.in_file}
        self.meta['Free Induction Decay Data File'] = {'value': "{}.zip".format(self.sample)}

        # Start parsing
        self.instrument()
        self.acquisition()
        self.source_file()
        self.contacts()
        self.processing()
        self.spectrum()
        self.probehead()
        self.pulse_sequence()

        self._convert_magnetic_field()

        self._urllize(self.meta)

        if 'contacts' in self.meta.keys():
            self.meta['study_contacts'] = self.meta['contacts']['entry_list']
            del self.meta['contacts']

    def _load_ontology(self, cached_onto):
        if self.nmrcv is None:
            if cached_onto is not None:
                self.nmrcv = cached_onto
            else:
                try:
                    self.nmrcv =  pronto.Ontology('http://nmrml.org/cv/v1.0.rc1/nmrCV.owl')
                except:
                    self.nmrcv = pronto.Ontology(
                        os.path.join(os.path.dirname(os.path.abspath(__file__)),'nmrCV.owl')
                    )

    def instrument(self):
        """Parses the instrument model, manufacturer and software"""
        instrument = self.tree.find(self.xpaths['instruments'].format(**self.env), self.ns)
        cvs = instrument.iterfind('./{cvParam}'.format(**self.env), self.ns)

        for cv in cvs:
            if cv.attrib['accession'] in self.nmrcv['NMR:1000031'].rchildren():

                self.meta['Instrument'] = {
                    'name': cv.attrib['name'],
                    'accession': cv.attrib['accession'],
                    'ref': cv.attrib['cvRef'],
                }

                manufacturer = next((x for x in self.nmrcv['NMR:1400255'].rchildren() if cv.attrib['name'].startswith(x.name)), None)
                if manufacturer is not None:
                    self.meta['Instrument manufacturer'] = {
                        'name': manufacturer.name,
                        'accession': manufacturer.id,
                        'ref': 'NMRCV',
                    }

            # PROBE
            elif cv.attrib['accession'] in self.nmrcv['NMR:1400014'].rchildren():
                self.meta['NMR Probe'] = {
                    'name': cv.attrib['name'],
                    'accession': cv.attrib['accession'],
                    'ref': cv.attrib['cvRef'],
                }

            # AUTOSAMPLER
            elif cv.attrib['accession'] in self.nmrcv['NMR:1000234'].rchildren():
                self.meta['Autosample'] = {
                    'name': cv.attrib['name'],
                    'accession': cv.attrib['accession'],
                    'ref': cv.attrib['cvRef'],
                }

        soft_ref = instrument.find('s:softwareRef', self.ns)
        if soft_ref is not None:
            soft, softv = self.software(soft_ref.attrib['ref'])
            if soft is not None:
                self.meta['Instrument software'] = soft
            if softv is not None:
                self.meta['Instrument software version'] = {'value': softv}

    def software(self, soft_ref):
        """Parses software information

        Returns:
            software (dict or None)
            software version (str or None)
        """

        for soft in self.tree.iterfind(self.xpaths['software'].format(**self.env), self.ns):

            if soft.attrib['id'] == soft_ref:

                soft_meta = { 'name': soft.attrib['name'],
                              'ref':  soft.attrib['cvRef'],
                              'accession': soft.attrib['accession'] }

                if 'version' in soft.attrib.keys():
                    return soft_meta, soft.attrib['version']
                else:
                    return soft_meta, None

        return None,None

    def acquisition(self):
        acquisition = self.tree.find(self.xpaths['acquisition'].format(**self.env), self.ns)
        if acquisition is None: return

        self.meta['Number of transients'] = {'value': int(acquisition.attrib['numberOfScans'])}
        self.meta['Number of steady state scans'] = {'value': int(acquisition.attrib['numberOfSteadyStateScans'])}

        terms = {'s:sampleAcquisitionTemperature': 'Temperature',
                 's:sampleContainer': 'NMR tube type',
                 's:spinningRate': 'Spinning Rate',
                 's:relaxationDelay': 'Relaxation Delay',
                 's:pulseSequence': 'Pulse sequence',
                 's:DirectDimensionParameterSet/s:acquisitionNucleus': 'Acquisition Nucleus',
                 's:DirectDimensionParameterSet/s:decouplingNucleus': 'Decoupling Nucleus',
                 's:DirectDimensionParameterSet/s:effectiveExcitationField': 'Magnetic field strength',
                 's:DirectDimensionParameterSet/s:sweepWidth': 'Sweep Width',
                 's:DirectDimensionParameterSet/s:pulseWidth': 'Pulse Width',
                 's:DirectDimensionParameterSet/s:irradiationFrequency': 'Irradiation Frequency',
                 's:DirectDimensionParameterSet/s:samplingStrategy': 'Sampling Strategy',
                 }

        self.read_children(acquisition, terms)

    def source_file(self):
        source_files = self.tree.iterfind(self.xpaths['source_file'].format(**self.env), self.ns)

        hooked_terms = [
            {'hook': lambda cv: cv.attrib['accession'] in self.nmrcv['NMR:1400285'].rchildren(), 'name':'Format'},
            {'hook': lambda cv: cv.attrib['accession'] in self.nmrcv['NMR:1400119'].rchildren(), 'name':'Type'},

            {'hook': lambda cv: cv.attrib['accession'] in self.nmrcv['NMR:1400122'].rchildren(), 'name':'Type'},
            {'hook': lambda cv: cv.attrib['accession'] in self.nmrcv['NMR:1002006'].rchildren(), 'name':'Type'},
            {'hook': lambda cv: cv.attrib['accession'] in self.nmrcv['NMR:1400123'].rchildren(), 'name':'Type'},
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

                self._parse_cv(source, hooked_terms, name)

    def contacts(self):
        contacts = self.tree.iterfind(self.xpaths['contacts'].format(**self.env), self.ns)
        self.meta['contacts'] = {'entry_list': []}
        for contact in contacts:
            name = contact.attrib['fullname'].split(' ')
            if len(name)==1: first_name, last_name, mid = '', *name, ''
            elif len(name)==2: first_name, last_name, mid = *name, ''
            else: first_name, mid, last_name = name

            self.meta['contacts']['entry_list'].append( {
                'first_name': first_name,
                'mid': mid,
                'last_name': last_name,
                'mail': contact.attrib['email']
                          if 'email' in contact.attrib.keys()
                          else ''
            } )

    def processing(self):
        processing = self.tree.find(self.xpaths['processing'].format(**self.env), self.ns)
        if processing is None: return

        soft_ref = processing.attrib['softwareRef']
        soft, softv = self.software(soft_ref)
        self.meta['Data Transformation software'] = soft
        if softv is not None:
            self.meta['Data Transformation software version'] = {'value': softv}

        self.meta['Data Transformation Name'] = {'entry_list':[]}
        for data_transformation in processing.iterfind(self.env['cvParam'], self.ns):
            self.meta['Data Transformation Name']['entry_list'].append(
                {
                    'name': data_transformation.attrib['name'],
                    'ref': data_transformation.attrib['cvRef'],
                    'accession': data_transformation.attrib['accession'],
                }
            )

    def spectrum(self):
        spectrum = self.tree.find(self.xpaths['spectrum'].format(**self.env), self.ns)
        if spectrum is None: return

        self.meta['Number of data points'] = {'value': int(spectrum.attrib['numberOfDataPoints'])}

        terms = {'s:xAxis': 'X axis range',
                 's:yAxisType': 'Y axis type',

                 's:processingParameterSet/s:postAcquisitionSolventSuppressionMethod/':'Post Acquisition Solvent Supression Method',
                 's:processingParameterSet/s:calibrationCompound/':'Calibration Compound',
                 's:processingParameterSet/s:dataTransformationMethod/':'Spectrum transformation method',
                 's:firstDimensionProcessingParameterSet/s:zeroOrderPhaseCorrection': 'Zero Value Phase Correction',
                 's:firstDimensionProcessingParameterSet/s:firstOrderPhaseCorrection': 'First Order Phase Correction',
                 's:firstDimensionProcessingParameterSet/s:calibrationReferenceShift': 'Calibration Reference Shift',
                 's:firstDimensionProcessingParameterSet/s:spectralDenoisingMethod': 'Spectral Denoising Method',
                 's:firstDimensionProcessingParameterSet/s:windowFunction/s:windowFunctionMethod': 'Window Function Method',
                 's:firstDimensionProcessingParameterSet/s:windowFunction/s:windowFunctionMethodParameter': 'Window Function Parameter',
                 's:firstDimensionProcessingParameterSet/s:baselineCorrectionMethod': 'Baseline Correction Method',
                 }

        self.read_children(spectrum, terms)

    def read_children(self, node, terms):
        for childpath, name in terms.items():
            child = node.find(childpath, self.ns)

            if child is not None:
                extract = self._children_extract(child)

                if not name in self.meta.keys() or not self.meta[name]:
                    self.meta[name] = extract.copy()

                elif not 'entry_list' in self.meta.keys():
                    self.meta[name] = {'entry_list': [ self.meta[name], extract.copy() ]}

                else:
                    self.meta[name]['entry_list'].append(extract.copy())

    def probehead(self):
        """Extracts the userParam ProbeHead if no CV term was found before."""
        if 'NMR Probe' not in self.meta.keys():
            probehead = self.tree.find(self.xpaths['probehead'].format(**self.env), self.ns)
            self.meta['NMR Probe'] = {'name': probehead.attrib['value'], 'ref':'', 'accession':''}

    def pulse_sequence(self):
        """Extracts the userParam Pulse sequence if no CV term was found before."""

        if 'Pulse sequence' not in self.meta.keys() or not self.meta['Pulse sequence']:

            pulse_sequence = self.tree.find(self.xpaths['pulse_sequence'].format(**self.env), self.ns)
            self.meta['Pulse sequence'] = {'name': pulse_sequence.attrib['value'], 'ref':'', 'accession':''}

    def _children_extract(self, child):

        _dict = dict()

        if 'value' in child.attrib.keys():
            _dict['value'] = child.attrib['value']
        if 'name' in child.attrib.keys():
            _dict['name'] = child.attrib['name']
        if 'unitName' in child.attrib.keys():
            _dict['unit'] = { 'name': child.attrib['unitName'],
                              'ref': child.attrib['unitCvRef'],
                              'accession': child.attrib['unitAccession'] }
        if 'cvRef' in child.attrib.keys():
            _dict['ref'] = child.attrib['cvRef']
            _dict['accession'] = child.attrib['accession']

        return _dict

    def _convert_magnetic_field(self):
        """Convert magnetic field value from mHz to tesla."""

        if not 'Magnetic field strength' in self.meta.keys():
            return

        if self.meta['Magnetic field strength']['unit']['accession'] != 'UO_0000325':
            return

        if 'Acquisition Nucleus' in self.meta.keys():

            if self.meta['Acquisition Nucleus']['accession']  in self.gyromagnetic_table.keys():

                mhz   =   float(self.meta['Magnetic field strength']['value'])
                tesla = mhz / self.gyromagnetic_table[self.meta['Acquisition Nucleus']['accession']]

                self.meta['Magnetic field strength'] = {
                    'value': "{:4}".format(tesla),
                    'unit': {'name':'tesla', 'ref':'UO', 'accession':'UO_0000228' }
                }

    @classmethod
    def _urllize(cls, starting_point):
        for k,v in starting_point.items():

            if isinstance(v, dict):
                for key, param in v.items():

                    if isinstance(param, dict):
                        cls._urllize(param)

                    elif isinstance(param, list):
                        for element in param:
                            cls._urllize(element)

                    elif key=='accession':
                        if 'http' not in param:
                            starting_point[k][key] = cls._urllize_name(param)

            elif k == 'accession':
                starting_point[k] = cls._urllize_name(v)

    @staticmethod
    def _urllize_name(accession):
        if accession.startswith('NMR'):
            return 'http://nmrml.org/cv/v1.0.rc1/nmrCV.owl#{}'.format(accession)
        elif accession.startswith('UO') or accession.startswith('CHEBI'):
            return 'http://purl.obolibrary.org/obo/{}'.format(accession)
        elif accession.startswith('C'):
            return 'http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#{}'.format(accession)
        return accession

    def _parse_cv(self, node, terms, name):

        for cv in node.iterfind('./{cvParam}'.format(**self.env), self.ns):
            for term in terms:
                if term['hook'](cv):
                        self.meta[' '.join([name, term['name']])] = {
                            'name': cv.attrib['name'],
                            'ref': cv.attrib['cvRef'],
                            'accession': cv.attrib['accession']
                        }
                        if 'unitName' in cv.attrib.keys():
                            self.meta[' '.join([name, term['name']])]['unit'] = {
                                'name': cv.attrib['unitName'],
                                'ref': cv.attrib['unitCvRef'],
                                'accession': cv.attrib['unitAccession'],
                            }

    def _build_env(self):

        try:
            # proper method to get namespace through nsmap (lxml)
            self.ns = self.tree.getroot().nsmap
            self.ns['s'] = self.ns[None]
            del self.ns[None]
        except AttributeError:
            # 'hacked' method to get namespace through root tag (xml.etree)
            self.ns = {'s': self.tree.getroot().tag[1:].split('}')[0] }

        self.env = {}

        if self.tree.find('./s:nmrML', self.ns) is None:
            self.env['root'] = '.'

        if self.tree.find('{root}/s:instrumentConfigurationList'
                          '/s:instrumentConfiguration/s:cvTerm'.format(**self.env), self.ns) is None:
            self.env['cvParam'] = 's:cvParam'
        else:
            self.env['cvParam'] = 's:cvTerm'

    @property
    def meta_json(self):
        return json.dumps(self.meta, indent=4, sort_keys=True)

    @property
    def meta_isa(self):
        keep = ["data transformation", "data transformation software version", "data transformation software",
                "term_source", "Raw Spectral Data File", "MS Assay Name", "Derived Spectral Data File", "Sample Name",
                "Acquisition Parameter Data File", "Free Induction Decay Data File", 'contacts']

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
    print(nmrMLmeta(sys.argv[1]).meta_json)





