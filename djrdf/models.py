# -*- coding:utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import CharField
from rdfalchemy import rdfSubject, rdfSingle
import rdflib
from repository import RDFS


# We store here the whole mecanism to mix together django model objects and openrdf objects
# with the help of rdfalchemy
# Mixing classes have to inherite from djRdf and myRdfSubject (or rdfalchemy.rdfSubject) classes
# in this order.....
# example 
# class Organization(djRdf, myRdfSubject):
#    # rdf attributes
#    ...
#    # django.model attributes
#    ....


# A class where every common methods are stored
class myRdfSubject(rdfSubject):

    # It is false that every rdfSubject has an rdfs:label, but
    # as it occurs very often.... it is a way not to forget it
    label = rdfSingle(RDFS.label)

    # The _remove methode delele only triples where self.resUri
    # occurs as the subject of the triple

    def remove(self):
        try:
            self.delete()
        except Exception:
            pass
        self._remove(self.db, cascade='all', objectCascade=True)


# The "joint" class. This class is used only in multiple heritage context
# One from rdfSubject (over classes by sesame.myRdfSubject class) and this one which
# overclasses the models.Model class
# Be careful, when deleting an rddfSubject with sesame.myRdfSubject.remove(), this call
# will also call the delete method of the Model class
class djRdf(models.Model):
    # the uri
    # TODO : need a validator (uri validator)
    uri = CharField(max_length=250)

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        # print "ENTER INIT with %s and %s" % (args, kwargs)
        # import pdb; pdb.set_trace();
        if args != ():
            # As the objects inherites from differents classes
            # We have to discard the args in order to prepare the calls
            # of the mothers' methods

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
                # Here the instanceis created using the methodes of rdfSubject
                else:
                    if isinstance(a0, rdfSubject):
                        kwargs['uri'] = a0.resUri
                    elif isinstance(a0, rdflib.term.URIRef):
                        kwargs['uri'] = a0
                    else:
                        raise Exception(_(u'Unhandled call for object %s with args %s and kwargs') % (self, args, kwargs))
                    # We have to make the links with de django database objects, if it exists
                    try:
                        o = self.__class__.objects.get(uri=kwargs['uri'])
                        # id and uri are already set
                        kwargs['id'] = o.id
                        for i in range(2, n):
                            kwargs[lf[i].name] = o.__dict__[lf[i].name]
                    except self.__class__.DoesNotExist:
                        # Nothing to do.... waith for a save for example
                        pass
            else:
                raise Exception(_(u'Unhandled call for object %s with args %s and kwargs') % (self, args, kwargs))
        # print "ARGs %s and %s" % (args, kwargs)
        super(djRdf, self).__init__(**kwargs)
        # oui car la methode __init__ de Model appelle cette de rdfSubject et
        # créer un blank node
        if kwargs.has_key('uri'):
            self.resUri = rdflib.term.URIRef(kwargs['uri'])

    def __repr__(self):
        """ To be compliante with the rdfSubject representation """
        return "%s('%s')" % (self.__class__.__name__, self.n3())

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._get_pk_val() == other._get_pk_val() and self.uri == other.uri

    def save(self, *args, **kwargs):
        self.resUri = rdflib.term.URIRef(self.uri)
        # Call the "real" save() method.
        super(djRdf, self).save(*args, **kwargs)


