import owllib.ontology
import copy


class EasyOwl(object):

    def __init__(self, owl_adress=None, cached_onto=None):

        self.owl = owllib.ontology.Ontology()
        
        if cached_onto is not None:
            self.owl = copy.deepcopy(cached_onto)
        elif owl_adress is not None:
            self.owl.load(location=owl_adress)
        else:
            self.owl.load(location="http://nmrml.org/cv/v1.0.rc1/nmrCV.owl")
    

    @property
    def gen_cls(self):
        """A dict of all the generic instruments nodes with accessions keys"""
        if not hasattr(self, '_gen_cls'):
            self._gen_cls = { manufacturer.uri.split('#')[-1]:manufacturer
                              for entity in self.owl.classes 
                                if 'NMR:1000031' in entity.uri
                              for manufacturers in entity._get_children()
                              for manufacturer in manufacturers._get_children() }
        return self._gen_cls

    @property
    def ins_cls(self):
        """A dict of all the instruments nodes with accessions keys"""
        if not hasattr(self, '_ins_cls'):
            self._ins_cls = {instrument.uri.split('#')[-1]:instrument
                             for generic in self.gen_cls.values()
                             for instrument in generic._get_children()}
        return self._ins_cls

    @property
    def ven_cls(self):
        """A dict of all vendors sorted by name"""
        if not hasattr(self, '_ven_cls'):
            self._ven_cls = { vendor.labels.pop().value:vendor
                              for entity in self.owl.classes 
                                if 'NMR:1400255' in entity.uri 
                              for vendor in entity._get_children() }
            
        return self._ven_cls

    @property
    def fmt_cls(self):
        """A dict of file formats sorted by dicts"""
        if not hasattr(self, '_fmt_cls'):
            self._fmt_cls = { fmt.uri.split('#')[-1]:fmt
                              for entity in self.owl.classes
                                if 'NMR:1400285' in entity.uri
                              for fmt in entity._get_children() } 
        return self._fmt_cls

    @property
    def fid_cls(self):
        if not hasattr(self, '_fid_cls'):
            self._fid_cls = { entity.uri.split('#')[-1]:entity
                              for entity in self.owl.classes
                                if 'NMR:1400119' in entity.uri}
            self._fid_cls.update( { fid.uri.split('#')[-1]:fid
                                    for base in self._fid_cls.values()
                                    for fid in base._get_children() } )
        return self._fid_cls

    @property
    def pls_cls(self):
        if not hasattr(self, '_pls_cls'):
            self._pls_cls = { entity.uri.split('#')[-1]:entity
                              for entity in self.owl.classes
                                if 'NMR:1400122' in entity.uri}
            self._pls_cls.update( { pls.uri.split('#')[-1]:pls
                                    for base in self._fid_cls.values()
                                    for pls in base._get_children() }
                )

        return self._pls_cls
    
    @property
    def acq_cls(self):
        if not hasattr(self, '_acq_cls'):
            self._acq_cls = { entity.uri.split('#')[-1]:entity
                              for entity in self.owl.classes
                                if 'NMR:1002006' in entity.uri}
            self._acq_cls.update( { acq.uri.split('#')[-1]:acq
                                    for base in self._fid_cls.values()
                                    for acq in base._get_children() }
                )
        return self._acq_cls
    
    @property
    def prc_cls(self):
        if not hasattr(self, '_prc_cls'):
            self._prc_cls = { entity.uri.split('#')[-1]:entity
                              for entity in self.owl.classes
                                if 'NMR:1400123' in entity.uri}
            self._prc_cls.update( { prc.uri.split('#')[-1]:prc
                                    for base in self._fid_cls.values()
                                    for prc in base._get_children() }
                )
        return self._prc_cls

    @property
    def prb_cls(self):
        if not hasattr(self, '_prb_cls'):
            self._prb_cls = { probe.uri.split('#')[-1]:probe
                              for entity in self.owl.classes
                                if 'NMR:1400014' in entity.uri
                              for probe in entity._get_children()}

            self._prb_cls.update( { detailled_probe.uri.split('#')[-1]:detailled_probe
                                    for probe in self._prb_cls.values()
                                    for detailled_probe in probe._get_children() } )

            self._prb_cls.update( { detailled_probe.uri.split('#')[-1]:detailled_probe
                                    for probe in self._prb_cls.values()
                                    for detailled_probe in probe._get_children() } )

        return self._prb_cls
    
    



    