# -*- coding:utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.db import models
# from django.db.models import CharField
from rdfalchemy import rdfSubject, rdfSingle, rdfMultiple
from rdfalchemy.descriptors import rdfAbstract
import rdflib
from django.conf import settings
from tools import prefixNameForPred
from django_extensions.db import fields as exfields
import pickle
from django.contrib.sites.models import Site
from django_push.publisher import ping_hub


# Serializer
rdflib.plugin.register('json-ld', rdflib.plugin.Serializer,
        'rdflib_jsonld.jsonld_serializer', 'JsonLDSerializer')


# Introspection let us add attributes fields on the fly
# This class aims to store the resulting attributes
class FlyAttr(models.Model):
    modelName = models.CharField(max_length=100)
    key = models.CharField(max_length=50)
    value = models.TextField()

    def __repr__(self):
        """ To be compliante with the rdfSubject representation """
        return "%s('%s')" % (self.modelName, self.key)

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def reload():
        # print "ENTER load FLY ATTR"
        mm = models.get_models()
        mname = {}
        for m in mm:
            mname[m.__name__] = m
        for fattr in FlyAttr.objects.all():
            setattr(mname[fattr.modelName], fattr.key, pickle.loads(str(fattr.value)))


# Mechanism to mix django model objects and RDF data with the help of RDFAlchemy
# Composite classes inherit from djRdf and myRdfSubject (or rdfalchemy.rdfSubject) classes
# in this *exact* order, example:
# 
# class Organization(djRdf, myRdfSubject):
#    # rdf attributes
#    ...
#    # django.model attributes
#    ....


# A class where every common methods are stored
class myRdfSubject(rdfSubject):
    dct_created = rdfSingle(settings.NS.dct.created)
    dct_modified = rdfSingle(settings.NS.dct.modified)

    # The _remove method deletes all the triples which
    # have  self.resUri as subject of the triple
    def remove(self):
        try:
            self.delete()
        except Exception:
            pass
        self._remove(self.db, cascade='all', objectCascade=True)


# The "joint" class. This class is only used in a multiple heritage context :
# - One class derived from rdfSubject (over classes by sesame.myRdfSubject class) 
# - and the djRdf class which subclasses the Django Model class
#
# Warning : deleting a rdfSubject using myRdfSubject.remove() 
# will also call the delete() method of the django Model class

class djRdf(models.Model):
    # TODO : ces deux champs doivent disparaitre.... cela casse la logique
    # rdf. Ils ne sont la  que pour nourrir les feeds. Charcher comment remplir 
    # le feeds a l'aide query sparql
    created = exfields.CreationDateTimeField(_(u'created'), null=True)
    modified = exfields.ModificationDateTimeField(_(u'modified'), null=True)
    uri = models.CharField(max_length=250)

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        # print "ENTER INIT with %s and %s" % (args, kwargs)
        # import pdb; pdb.set_trace();
        if args != ():
            # As the objects inherits from differents classes
            # We have to discard the args in order to prepare the calls
            # of the superclass methods

            # TODO C'est pas fini..... On perd trop de trucs

            if kwargs == {}:
                kwargs['id'] = None
                kwargs['uri'] = None
                a0 = args[0]
                lf = self.__class__._meta.local_fields
                n = lf.__len__()
                 # In this case the args are a rows from the django database
                if isinstance(a0, int):
                    if (args.__len__() == n):
                        for i in range(n):
                            kwargs[lf[i].name] = args[i]
                    else:
                        raise Exception(_(u'Unhandled call for object %s with args %s and kwargs') % (self, args, kwargs))
                # Here the instance is created using the methods of rdfSubject
                else:
                    if isinstance(a0, rdfSubject):
                        kwargs['uri'] = a0.resUri
                    elif isinstance(a0, rdflib.term.URIRef):
                        kwargs['uri'] = a0
                    else:
                        raise Exception(_(u'Unhandled call for object %s with args %s and kwargs') % (self, args, kwargs))
                    # We have to make the links with the django objects, if it exists
                    try:
                        o = self.__class__.objects.get(uri=kwargs['uri'])
                        # id and uri are already set
                        kwargs['id'] = o.id
                        for i in range(2, n):
                            kwargs[lf[i].name] = o.__dict__[lf[i].name]
                    except self.__class__.DoesNotExist:
                        # Nothing to do.... wait for a save for example
                        pass
            else:
                raise Exception(_(u'Unhandled call for object %s with args %s and kwargs') % (self, args, kwargs))
        # print "ARGs %s and %s" % (args, kwargs)
        super(djRdf, self).__init__(**kwargs)
        # oui car la methode __init__ de Model appelle cette de rdfSubject et crée un blank node
        if 'uri' in kwargs:
            self.resUri = rdflib.term.URIRef(kwargs['uri'])

    def __repr__(self):
        """ To be compliante with the rdfSubject representation """
        return "%s('%s')" % (self.__class__.__name__, self.n3())

    def __str__(self):
        return str(self.resUri)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._get_pk_val() == other._get_pk_val() and self.uri == other.uri

    # TODO : It is possible that we have to set all "rdfalchemy" fields
    # to None so that they are re-initialized
    def save(self, *args, **kwargs):
        self.resUri = rdflib.term.URIRef(self.uri)
        # USELESS?????
        if self.uri != '':
            # It is important, if the resource is created in django ORM
            # first and if the uri does not exists before
            self.db.add((self, settings.NS.rdf.type, self.rdf_type))
        # Call the "real" save() method.
        super(djRdf, self).save(*args, **kwargs)
        ping_hub('http://%s/%s/%s' % (Site.objects.get_current(), 'feed', self.__class__.__name__.lower()))

    # This method is used to build and set the attributs according to the
    # triples list in parameters.
    # If this method is called, this means that from de subject of the triples
    # its class has been set
    def addTriples(self, triples):
        # store  the triples according to the pred
        pred = {}
        for (s, p, o) in triples:
            if p in pred:
                pred[p].append(o)
            else:
                pred[p] = [o]
        attrlist = self.__class__.__dict__
        for (p, olist) in pred.iteritems():
            # look for an attribute corresponding to this predicate
            attr = None
            for (aname, adef) in attrlist.iteritems():
                if isinstance(adef, rdfAbstract):
                    if (adef.pred == p):
                        attr = aname
                        break

            # This attribute does not exist yet. Just create id and set its value
            if (attr == None):
                # version simplifiée
                # for o in olist:
                #     self.db.add((self.resUri, p, o))

                # Introspection version: attributes create on the fly
                # The attribute name is made from the predicate uri...
                # Hope it could be safe.
                attr = prefixNameForPred(p)
                # special case for rdf_type because of ....
                # triples are simply added
                if attr == 'rdf_type':
                    for o in olist:
                        self.db.add((self.resUri, p, o))
                else:
                    if attr in attrlist:
                        # choose another name
                        raise Exception("NYI chose an other name for %s" % attr)
                    # the cardinality defined if we use a rdfSingle or rdfMultiple
                    # Thus we need to parse the graph corresponding to the URI of the property
                    # TODO : something more complex to deal with owl:cardinality
                    gr = rdflib.Graph()
                    try:
                        gr.parse(p)
                    except:
                        # It is impossible to access the the graph of the
                        # property. Let's do the simplest thing we could do
                        for o in olist:
                            self.db.add((self.resUri, p, o))
                    types = gr.objects(p, settings.NS.rdf.type)
                    ranges = list(gr.objects(p, settings.NS.rdfs.range))
                    if settings.NS.owl.FunctionalProperty in types or settings.NS.owl.InverseFunctionalProperty in types:
                        # look for possible range_type
                        if len(ranges) == 1  and not (settings.NS.rdfs.Literal in ranges):
                            descriptor = rdfSingle(p, range_type=ranges[0])
                        else:
                            descriptor = rdfSingle(p)
                        setattr(self.__class__, attr, descriptor)
                        FlyAttr.objects.get_or_create(modelName=self.__class__.__name__,
                                    key=attr,
                                    value=pickle.dumps(descriptor))
                        setattr(self, attr, olist[0])
                    else:
                        # look for possible range_type
                        if len(ranges) == 1  and not (settings.NS.rdfs.Literal in ranges): 
                            descriptor = rdfMultiple(p, range_type=ranges[0])
                        else:
                            descriptor = rdfMultiple(p)
                        setattr(self.__class__, attr, descriptor)
                        FlyAttr.objects.get_or_create(modelName=self.__class__.__name__,
                                    key=attr,
                                    value=pickle.dumps(descriptor))
                        # attention aux triplets qu sont deja dans le store
                        # il faut les supprimer
                        oldvalue = self.db.triples((self, p, None))
                        for tr in oldvalue:
                            self.db.remove(tr)
                        setattr(self, attr, olist) 
            else:
                # attr contains the name of the attribute.... just set the new values
                if isinstance(getattr(self.__class__, attr), rdfSingle):
                    setattr(self, attr, olist[0])
                else:
                    # attention ici on ne supprime pas les vieux
                    oldvalue = self.db.triples((self, p, None))
                    for tr in oldvalue:
                        self.db.remove(tr)
                    setattr(self, attr, olist)

    def toJson(self):
        triples = self.db.triples((self.resUri, None, None))
        g = rdflib.Graph()
        try:
            while True:
                g.add(triples.next())
        except:
            pass
        # let's see if it is useful to put also the "ValueOf"
        triples = self.db.triples((None, None, self.resUri))
        try:
            while True:
                g.add(triples.next())
        except:
            pass 
        return g.serialize(format='json-ld')





