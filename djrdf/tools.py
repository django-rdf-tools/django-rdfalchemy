# -*- coding:utf-8 -*-
from django.conf import settings
from django.db import models
import djrdf
from rdflib import Namespace



# In this file one can found some  usefull function to deal
# with uri (as rdflib.term.URIRef) or Namespaces


_reverseNs = {}
for (k, v) in settings.DJRDF_NS.iteritems():
    _reverseNs[v] = k



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

