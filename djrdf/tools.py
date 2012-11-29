# -*- coding:utf-8 -*-
# Some useful functions to deal with rdflib's URIRef and Namespaces

from django.conf import settings
from django.db import models
import djrdf
from rdflib import Namespace, URIRef, Graph
import rdfalchemy

_reverseNs = {}
for (k, v) in settings.NS.iteritems():
    _reverseNs[v] = k



def uri_to_json(uri, db=rdfalchemy.rdfSubject.db):
    triples = db.triples((URIRef(uri), None, None))
    g = Graph()
    for k in settings.NS: 
        g.bind(k, settings.NS[k])
    try:
        while True:
            g.add(triples.next())
    except:
        pass
    # let's see if it is useful to put also the "ValueOf"
    triples = db.triples((None, None, URIRef(uri)))
    try:
        while True:
            g.add(triples.next())
    except:
        pass 
    return g.serialize(format='json-ld')

    


def splitUri(uri):
    res = uri.split('#')
    if len(res) == 2:
        return  (res[0] + '#', res[1])
    res = uri.split('/')
    if uri.endswith('/'):
        uri_name = res[len(res) - 2] + '/'
    else:
        uri_name = res[len(res) - 1] 
    ns_name = uri.replace(uri_name, '')
    return (ns_name, uri_name)


def prefixNameForPred(pred):
    (ns_name, uri_name) = splitUri(pred)
    ns_name = Namespace(ns_name)
    if ns_name in _reverseNs:
        return '%s_%s' % (_reverseNs[ns_name], uri_name)
    else:
        raise Exception('NameSPACE %s is missing in settings files' % ns_name)


def rdfDjrdfMapTypes():
    mapRes = {}
    rdfModels = models.get_models()
    for m in rdfModels: 
        if djrdf.models.djRdf in m.__mro__:
            mapRes[m.rdf_type] = m
    return mapRes


def rdfTypeToModel(rdfType):
    rdfModels = models.get_models()
    for m in rdfModels: 
        if djrdf.models.djRdf in m.__mro__:
            if rdfType == m.rdf_type:
                return m
    return None

