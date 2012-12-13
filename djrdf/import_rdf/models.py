# -*- coding:utf-8 -*-
# Create your models here.
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django_push.subscriber.models import Subscription
from djrdf.repository import Repository
from rdflib import  plugin, URIRef, Graph
import djrdf.tools
import tempfile
import os
import feedparser
import datetime
import time
import djrdf
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from rdfalchemy.orm import mapper
from urlparse import urlsplit
import logging

log = logging.getLogger('pes')

# plugin.register(
#         'SPARQLStore', store.Store,
#         'rdflib_sparqlstore.SPARQLStore', 'SPARQLStore')
plugin.register('json-ld', plugin.Parser,
        'rdflib_jsonld.jsonld_parser', 'JsonLDParser')



class SparqlQuery(models.Model):
    query = models.TextField(_(u'query'))
    label = models.CharField(_(u'Label'), max_length=300)
    notation = models.TextField(_(u'notation'), null=True, blank=True)

    class Meta:
        verbose_name = _(u'query')
        verbose_name_plural = _(u'queries')

    def __unicode__(self):
        return self.label


class EntrySite(models.Model):
    label = models.CharField(_(u'Label'), max_length=100, unique=True)
    description = models.TextField(_(u'description'), null=True, blank=True)
    home = models.CharField(_(u'home'), max_length=250)
    rdfEndPoint = models.CharField(_(u'rdf endPoint'), max_length=250)
    feed = models.CharField(_(u'feed'), max_length=250)
    hub = models.CharField(_(u'hub'), max_length=250, blank=True)
    auto_subscribe = models. BooleanField(_(u'automatic subscription'), default=True)
    logs = models.TextField(_(u'logs'), null=True, blank=True)
    # Je ne suis pas sur que ca soit important
    # queries = models.ManyToManyField(SparqlQuery, verbose_name=_(u'queries'), related_name='queries')


    def save(self, *args, **kwargs):
         # create / update URI
        super(EntrySite, self).save(*args, **kwargs)
        if self.auto_subscribe:
            self.subscribFeeds()


    class Meta:
        verbose_name = _(u'Site entries')
        verbose_name_plural = _(u'Sites entries')

    def __unicode__(self):
        return self.label

    def graph(self, model=None):
        graph = Graph()

        if model in settings.FEED_MODELS:
            ep = self.rdfEndPoint
            remainder = ep.rsplit('all', 1)
            endPoint = model.join(remainder)
        else:
            endPoint = self.rdfEndPoint

        if endPoint.endswith('n3'):
            graph.parse(endPoint, format='n3')
        elif endPoint.endswith('ttl'):
            graph.parse(endPoint, format='n3')
        elif endPoint.endswith('json'):
            graph.parse(endPoint, format='json-ld')
        elif endPoint.endswith('trix'):
            graph.parse(endPoint, format='trix')
        elif endPoint.endswith('xml'):
            graph.parse(endPoint, format='xml')

        return graph

    @property
    def defaultCtxName(self):
        return self.home

    def addLog(self, log):
        self.logs = "%s : %s \n%s" % (datetime.datetime.now(), log, self.logs)

    def is_local(self, uri):
        if not isinstance(uri, URIRef) and hasattr(uri, 'uri'):
            uri = uri.uri
        scheme, host, path, query, fragment = urlsplit(uri)
        scheme, host_self, path, query, fragment = urlsplit(self.home)
        return host.startswith(host_self)

    def is_common(self, uri):
        if not isinstance(uri, URIRef) and hasattr(uri, 'uri'):
            uri = uri.uri
        scheme, host, path, query, fragment = urlsplit(uri)
        uri_domain = "%s://%s" % (scheme, host)
        for cd in settings.COMMON_DOMAINS:
            if cd.startswith(uri_domain):
                return True
        return False


    # Using a 'construct query' this method imports triples
    # from the graph (the first time, and for dumps the graph is self.parql())
    # The method to imported triples is described with mode details in doc
    # We process from the subjectrfd
    def toSesameRep(self, repository, graph, ctx='default', rdfType=None, force=False):
        # lets use the context posibility, should be useless
        if ctx == None and not getattr(settings, 'PES_USE_CONTEXT', False):
            sesame = Repository(repository)
        else:
            if ctx == 'default' or getattr(settings, 'PES_USE_CONTEXT', False):
                ctx = self.defaultCtxName
            ctx = "<%s>" % ctx
            sesame = Repository(repository, context=ctx)
        unknownTypes = []
        mapDjrdfTypes = djrdf.tools.rdfDjrdfMapTypes()
        subjects = graph.subjects(settings.NS.rdf.type, rdfType)
        for subject in subjects:
            # small delay to let jetty warmup
            time.sleep(0.01)
            stored_date = list(sesame.objects(subject, settings.NS.dct.modified))
            update_date = list(graph.objects(subject, settings.NS.dct.modified))
            replacedBy = list(graph.objects(subject, settings.NS.dct.isReplacedBy))
            deletedOn = list(graph.objects(subject, settings.NS.ov.deletedOn))

            if  (not force) and len(update_date) == 1 and len(stored_date) == 1 and update_date[0].toPython() <= stored_date[0].toPython():
                log.debug(u"Nothing to update for %s" % subject)
            else:
                log.debug("Handle %s in %s" % (subject, repository))
                types = list(graph.objects(subject, settings.NS.rdf.type))

                # look for a type corresponding to a mapped RDFAlchemy model
                RdfModel, djRdfModel = None, None
                i = 0
                n = len(types)
                while i < n and not RdfModel:
                    str_type = str(types[i])
                    if str_type in mapper():
                        RdfModel = mapper()[str_type]
                    i += 1

                if not RdfModel:
                    unknownTypes.extend(types)
                # look for and djRdf.models corresponding to that type
                if RdfModel:
                    try:
                        djRdfModel = mapDjrdfTypes[RdfModel.rdf_type]
                    except KeyError:
                        djRdfModel = None

                # If a triple <old_uri> dct.isReplacedBy <new_uri> exists, this supposed
                # the new_uri is up_to_date and the 'domain' which was hosting old_uri
                # aggrees this renaming of uri. The aggregator has just to registered it
                # and to populate this modification
                if len(replacedBy) == 1:
                    newSubject = replacedBy[0]
                    sesame.add((subject, settings.NS.dct.isReplacedBy, newSubject))
                    triples = graph.triples((None, None, subject))
                    try:
                        while True:
                            (s, p, o) = triples.next()
                            sesame.add((s, p, newSubject))
                    except StopIteration:
                        pass
                    # and we suppress triples that are now obsolete
                    sesame.remove((subject, None, None))
                    sesame.remove((None, None, subject))

                    # if subject is  django object
                    if djRdfModel:
                        oldSubject = djRdfModel.objects.get(uri=subject)
                        oldSubject.delete()
                        djSubject, created = djRdfModel.objects.get_or_create(uri=newSubject)
                        djSubject.save()  # To publish updates
                elif len(deletedOn) == 1:
                    if djRdfModel:
                        djSubject, created = djRdfModel.objects.get_or_create(uri=subject)
                        djSubject.remove()
                    elif RdfModel:
                        subject.remove()
                    else:
                        sesame.remove((subject, None, None))
                        sesame.remove((None, None, subject))
                else:
                    addtriples = []
                    undirect_triples = list(graph.triples((None, None, subject)))
                    for  (s, p, o) in list(graph.triples((subject, None, None))): 
                        # Skip triples belong to foreign "context", which correspond to
                        # "imported" triples in this application
                        # local property case
                        if self.is_local(p):
                            addtriples.append((s, p, o))
                        else:
                            if self.is_local(s):
                                addtriples.append((s, p, o))
                            elif self.is_common(s):
                                addtriples.append((s, p, o))
                            elif isinstance(o, URIRef):
                                if self.is_local(o):
                                    addtriples.append((s, p, o))
                                else:
                                    self.addLog("The triple (%s,%s,%s) CANNOT be added" % (s, p, o))
                            else:
                                self.addLog("The triple (%s,%s,%s) CANNOT be added" % (s, p, o))
                    undirect_triples = []
                    for (s, p, o) in list(graph.triples((None, None, subject))):
                        if self.is_local(p):
                            undirect_triples.append((s, p, o))
                            if self.is_local(o):
                                undirect_triples.append((s, p, o))
                            elif self.is_common(o):
                                undirect_triples.append((s, p, o))
                            elif isinstance(s, URIRef):
                                if self.is_local(s):
                                    undirect_triples.append((s, p, o))
                                else:
                                    self.addLog("The triple (%s,%s,%s) CANNOT be added" % (s, p, o))
                            else:
                                self.addLog("The triple (%s,%s,%s) CANNOT be added" % (s, p, o))


                    if djRdfModel:
                        djSubject, created = djRdfModel.objects.get_or_create(uri=subject)
                        djrdf.tools.addTriples(subject, addtriples, undirect_triples,  sesame)
                        djSubject.save()
                    else:
                        # print "When no djRdfModel exists for %s" % subject
                        djrdf.tools.addTriples(subject, addtriples, undirect_triples, sesame)

        for t in unknownTypes:
            self.addLog("The rdf:type %s is not handled yet by the aggregator" % t)
        # for the logs    
        self.save()


    def removeFromSesameRep(self, repository, ctx='default', rdfType=None):
        """
        remove triples (s,p,o) such as 
           - s has an uri hosted by self
           - o has an uri hosted by self
           - p has an uri hosted by seld
        """
        # lets use the context posibility, should be useless
        if ctx == None and not getattr(settings, 'PES_USE_CONTEXT', False):
            sesame = Repository(repository)
        else:
            if ctx == 'default' or getattr(settings, 'PES_USE_CONTEXT', False):
                ctx = self.defaultCtxName
            ctx = "<%s>" % ctx
            sesame = Repository(repository, context=ctx)
        subjects = sesame.subjects(settings.NS.rdf.type, rdfType)
        for subject in subjects:
            if self.is_local(subject):
                sesame.remove((subject, None, None))
        preds = sesame.predicates(None, None)
        for p in preds:
            if self.is_local(p):
                sesame.remove((None, p, None))
        objs = sesame.objects(None, None)
        for o in objs:
            if isinstance(o, URIRef) and self.is_local(o):
                sesame.remove((None, None, o))
        # Suppress also instance in db
        for m in models.get_models():
            if djrdf.models.djRdf in m.__mro__:
                for o in m.objects.filter(uri__contains=self.home):
                    o.delete()
  



    def updateFromFeeds(self, repository, ctx='default'):
        for f in getattr(settings, 'FEED_MODELS', []):
            feed_url = self.feed + f + '/'
            parsedFeed = feedparser.parse(feed_url)
            log.debug("Parse feed %s" % feed_url)
            for entry in parsedFeed.entries:
                fd, fname = tempfile.mkstemp()
                os.write(fd, entry.summary)
                os.close(fd)
                g = Graph()
                g.parse(fname, format="json-ld")
                self.toSesameRep(repository, g, ctx, None)

    def subscribFeeds(self):
        for f in getattr(settings, 'FEED_MODELS', []):
            feed_url = "%s%s/" % (self.feed, f)
            validate = URLValidator(verify_exists=True)
            try:            
                validate(feed_url)
                Subscription.objects.subscribe(feed_url, hub=self.hub)
            except ValidationError:
                pass


    def unsubscribFeeds(self):
        for f in getattr(settings, 'FEED_MODELS', []):
            feed_url = "%s%s/" % (self.feed, f)
            validate = URLValidator(verify_exists=True)
            try:
                validate(feed_url)
                Subscription.objects.unsubscribe(feed_url, hub=self.hub)
            except ValidationError:
                pass



