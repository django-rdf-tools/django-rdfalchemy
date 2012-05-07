# -*- coding:utf-8 -*-
from rdfalchemy.sparql.sesame2 import SesameGraph
from rdflib import Namespace, BNode

OPENSAHARA = Namespace('http://rdf.opensahara.com/search#')
ORG = Namespace('http://www.w3.org/ns/org#')
DCT = Namespace('http://purl.org/dc/terms/')
CTAG = Namespace('http://commontag.org/ns#')
FOAF = Namespace('http://xmlns.com/foaf/0.1/')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')


class Repository(SesameGraph):
    """ Init a Sesame graph and set some values in to perform
        UseekM queries
    """
    # the context parametre defines a context, that will add this context
    # to all new triples added in the repository.
    # But we can't see this context with the help of the contexts attribut
    def __init__(self, repository, serverName='localhost', portNumber='8080', context=None):
        """  repository is th repository id as express in opendRdf documention"""
        url = "http://%s:%s/openrdf-sesame/repositories/%s" % (serverName, portNumber, repository)
        super(Repository, self).__init__(url, context)
        #self.namespaces['search'] = 'http://rdf.opensahara.com/search#'

    # This a way to break problems raised by multiple inheriting the from
    # rdfSubject and Django.db.models.Model
    # A better solution could be find, I guess,... but for now I have not it
    def add(self, (s, p, o), context=None):
        if isinstance(s, BNode):
            pass
        else:
            # print "ENTER ADDD with object %s %s %s" % (s, p, o)
            # print "N3 de objects is %s " % o.n3()
            # print "TRY NT %s" % _xmlcharref_encode(o.n3())
            # print "try encoding %s " % o.n3().encode("utf-8")
            super(Repository, self).add((s, p, o), context)


# Set the default database for rdfSubject
# import rdfalchemy
# pesSesame = Repository("pesRepository")
# rdfalchemy.rdfSubject.db = pesSesame



