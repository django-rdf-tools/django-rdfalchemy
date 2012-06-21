# -*- coding:utf-8 -*-

class AttributeDict(dict): 
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

PUSH_HUB = 'http://quinode.superfeedr.com'

from rdflib import Namespace
COMMON_DOMAINS = [
    'http://data.economie-solidaire.fr', 
    'http://rdf.insee.fr/geo/'
    ]


DJRDF_NS = AttributeDict(

    # Base
    rdf=Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#'),
    rdfs=Namespace('http://www.w3.org/2000/01/rdf-schema#'),
    owl=Namespace('http://www.w3.org/2002/07/owl#'),
    xsd=Namespace('http://www.w3.org/2001/XMLSchema#'),

    # Classics
    gr=Namespace('http://purl.org/goodrelations/v1#'),
    dct=Namespace('http://purl.org/dc/terms/'),
    foaf=Namespace('http://xmlns.com/foaf/0.1/'),
    skos=Namespace('http://www.w3.org/2004/02/skos/core#'),
    skosxl=Namespace('http://www.w3.org/2008/05/skos-xl#'),
    vcard=Namespace('http://www.w3.org/2006/vcard/ns#'),
 
    # UE Namespaces
    org=Namespace('http://www.w3.org/ns/org#'),
    locn=Namespace('http://www.w3.org/ns/locn#'),
    legal=Namespace('http://www.w3.org/ns/legal#'),
    person=Namespace('http://www.w3.org/ns/person#'),
)


FEED_MODELS = ['organization', 'contact', 'exchange']
# Later ....
# FEED_MODELS=['organization', 'person', 'role', 'product', 'engagement',
#               'relation', 'exchange', 'contact', 'article']
