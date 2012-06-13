# -*- coding:utf-8 -*-
from rdflib import Namespace

COMMON_DOMAIN_NAME = [
    'http://data.economie-solidaire.fr', 
    'http://rdf.insee.fr/geo/2011/'
    ]

OPENSAHARA = Namespace('http://rdf.opensahara.com/search#')
ORG = Namespace('http://www.w3.org/ns/org#')
DCT = Namespace('http://purl.org/dc/terms/')
CTAG = Namespace('http://commontag.org/ns#')
FOAF = Namespace('http://xmlns.com/foaf/0.1/')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
ESS = Namespace('http://ns.economie-solidaire.fr/ess#')
V = Namespace('http://www.w3.org/2006/vcard/ns#')
LOCN = Namespace('http://www.w3.org/ns/locn#')
SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
LEGAL = Namespace('http://www.w3.org/ns/legal#')
SKOSXL = Namespace('http://www.w3.org/2008/05/skos-xl#')


 # 'xsd': 'http://www.w3.org/2001/XMLSchema#',
 # 'insee': u'http://rdf.insee.fr/geo/2011/',
 # 'skosxl': u'http://www.w3.org/2008/05/skos-xl#',
 # 'gr': u'http://purl.org/goodrelations/v1#',
 # 'event': u'http://purl.org/NET/c4dm/event.owl#',
 # 'sioc': u'http://rdfs.org/sioc/ns#',
 # 'opens': u'http://rdf.opensahara.com/type/geo/',
 # 'person': u'http://www.w3.org/ns/person#',
 # 'schema': u'http://schema.org/',
 # 'rss': u'http://purl.org/net/rss1.1#'

DJRDF_NS = dict(
    opens=OPENSAHARA, skos=SKOS, legal=LEGAL,
    org=ORG, skosxl=SKOSXL,
    dct=DCT,
    ctag=CTAG,
    foaf=FOAF,
    rdfs=RDFS,
    rdf=RDF,
    owl=OWL,
    ess=ESS,
    v=V,
    locn=LOCN
    ) 


FEED_NAMES = ['organization']
# Later ....
# FEED_NAMES = ['organization', 'person', 'role', 'product', 'engagement',
#               'relation', 'exchange', 'contact', 'article']
