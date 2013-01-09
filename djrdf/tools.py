# -*- coding:utf-8 -*-
# Some useful functions to deal with rdflib's URIRef and Namespaces
from django.conf import settings
from django.db import models
import djrdf
from rdflib import Namespace, URIRef, Graph
from rdfalchemy import rdfSingle, rdfSubject
from rdfalchemy.descriptors import rdfAbstract
import logging

log = logging.getLogger('djrdf')

_reverseNs = {}
for (k, v) in settings.NS.iteritems():
    _reverseNs[v] = k



# This method is used to build and set the attributs according to the
# triples list in parameters.
# If this method is called, this means that from de subject of the triples
# its class has been set
def addTriples(uri, triples, undirect_triples, db=rdfSubject.db):
    # store  the triples according to the pred
    pred = {}
    for (s, p, o) in triples:
        if p in pred:
            pred[p].append(o)
        else:
            pred[p] = [o]
    # attrlist = uri.__class__.__dict__  # voir les commentaires si dessous
    for (p, olist) in pred.iteritems():
        # first suppress the old value
        try:
            db.remove((uri, p, None))
        except Exception, e:
            log.debug('Cannot remove %s, %s' % (uri, e))
        for o in olist:
            db.add((uri, p, o))

    pred = {}
    for (s, p, o) in undirect_triples:
        if p in pred:
            pred[p].append(s)
        else:
            pred[p] = [s]
    for (p, slist) in pred.iteritems():
        # first suppress the old value
        db.remove((None, p, uri))
        for s in slist:
            db.add((s, p, uri))


        # Bof ce qui suit ne sert à rien.... les 2 lignes qui 
        # précèdent suffisent
        # # look for an attribute corresponding to this predicate
        # attr = None
        # for (aname, adef) in attrlist.iteritems():
        #     if isinstance(adef, rdfAbstract):
        #         if (adef.pred == p):
        #             attr = aname
        #             break

        # # This attribute does not exist yet. Just create id and set its value
        # if (attr == None):
        #     # version simplifiée
        #     for o in olist:
        #         db.add((uri, p, o))
        #         # log.debug(u'Attr %s does not exist for %s\n' % (p, uri))
        # else:
        #     # attr contains the name of the attribute.... just set the new values
        #     if isinstance(getattr(uri.__class__, attr), rdfSingle):
        #         setattr(uri, attr, olist[0])
        #     else:
        #         setattr(uri, attr, olist)


def uri_to_json(uri, db=rdfSubject.db):
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

