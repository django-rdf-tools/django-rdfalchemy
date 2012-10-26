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
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

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

    def graph(self):
        graph = Graph()
        if self.rdfEndPoint.endswith('n3'):
            graph.parse(self.rdfEndPoint, format='n3')
        elif self.rdfEndPoint.endswith('ttl'):
            graph.parse(self.rdfEndPoint, format='n3')
        elif self.rdfEndPoint.endswith('json'):
            graph.parse(self.rdfEndPoint, format='json-ld')
        elif self.rdfEndPoint.endswith('trix'):
            graph.parse(self.rdfEndPoint, format='trix')
        elif self.rdfEndPoint.endswith('xml'):
            graph.parse(self.rdfEndPoint, format='xml')

        return graph

    @property
    def defaultCtxName(self):
        return self.home

    def addLog(self, log):
        self.logs = "%s : %s \n%s" % (datetime.datetime.now(), log, self.logs)


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

            if  (not force) and len(update_date) == 1 and len(stored_date) == 1 and update_date[0].toPython() <= stored_date[0].toPython():
                print u"Nothing to update for %s" % subject
            else:
                print "Add %s in %s" % (subject, repository) 
                types = graph.objects(subject, settings.NS.rdf.type)
                # look for and djRdf.models corresponding to that type
                djRdfModel = None
                for t in types:
                    if t in mapDjrdfTypes:
                        djRdfModel = mapDjrdfTypes[t]
                        break
                    else:
                        if not(t in unknownTypes):
                            unknownTypes.append(t)

                addtriples = []
                triples = graph.triples((subject, None, None))

                # If a triple <old_uri> dct.isReplacedBy <new_uri> exists, this supposed
                # the new_uri is up_to_date and the 'domain' which was hosting old_uri
                # aggrees this renaming of uri. The aggregator has just to registered it
                # and to populate this modification
                if djRdfModel and len(replacedBy) == 1:
                    newSubject = replacedBy[0]
                    try:
                        while True:
                            tr = triples.next()
                            sesame.remove(tr)
                    except StopIteration:
                        pass
                    sesame.add((subject, settings.NS.dct.isReplacedBy, newSubject))
                    triples = graph.triples((None, None, subject))
                    try:
                        while True:
                            (s, p, o) = triples.next()
                            sesame.remove((s, p, o))
                            sesame.add((s, p, newSubject))
                    except StopIteration:
                        pass

                    djSubject, created = djRdfModel.objects.get_or_create(uri=subject)
                    djSubject.save()  # To publish updates
                else:
                    try:
                        while True: 
                            (s, p, o) = triples.next()
                            # Skip triples belong to foreign "context", which correspond to
                            # "imported" triples in this application
                            pNs = djrdf.tools.splitUri(p)[0]
                            # local property case
                            if pNs.startswith(self.home):
                                addtriples.append((s, p, o))
                            else:
                                sNs = djrdf.tools.splitUri(s)[0]
                                if sNs.startswith(self.home):
                                    addtriples.append((s, p, o))
                                # or sNs.startswith(COMMON_DOMAINS)
                                elif settings.COMMON_DOMAINS != []:
                                    i = 0
                                    sw = sNs.startswith(settings.COMMON_DOMAINS[i])
                                    while (not sw) and (i < len(settings.COMMON_DOMAINS) - 1):
                                        i = i + 1
                                        sw = sNs.startswith(settings.COMMON_DOMAINS[i])
                                    if sw:
                                        addtriples.append((s, p, o))
                                elif isinstance(o, URIRef):
                                    oNs = djrdf.tools.splitUri(o)[0]
                                    if oNs.startswith(self.home):
                                        addtriples.append((s, p, o))
                                    else:
                                        self.addLog("The triple (%s,%s,%s) CANNOT be added" % (s, p, o))
                                else:
                                    self.addLog("The triple (%s,%s,%s) CANNOT be added" % (s, p, o))
                    except StopIteration:
                        pass

                if djRdfModel and addtriples != []:
                    djSubject, created = djRdfModel.objects.get_or_create(uri=subject)
                    log = djSubject.addTriples(addtriples, sesame)
                    self.addLog(log)
                    djSubject.save()
                elif addtriples == []:
                    print "No triple could be imported for %s" % subject
                # There is no djrdf model for the rdf:type of the subject
                # the selected type are still add
                else:
                    print "When no djRdfModel exists for %s" % subject
                    for t in addtriples:
                        sesame.add(t)
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
            if str(subject).startswith(self.home):
                triples = sesame.triples((subject, None, None))
                for tr in triples:
                    try:
                        sesame.remove(tr)
                    except:
                        pass
        preds = sesame.predicates(None, None)
        for p in preds:
            if str(p).startswith(self.home):
                triples = sesame.triples((None, p, None))
                for tr in triples:
                    try:
                        sesame.remove(tr)
                    except:
                        pass
        objs = sesame.objects(None, None)
        for o in objs:
            if isinstance(o, URIRef) and str(o).startswith(self.home):
                triples = sesame.triples((None, None, o))
                for tr in triples:
                    try:
                        sesame.remove(tr)
                    except:
                        pass



    def updateFromFeeds(self, repository, ctx='default'):
        for f in getattr(settings, 'FEED_MODELS', []):
            feed_url = self.feed + f + '/'
            parsedFeed = feedparser.parse(feed_url)
            print "Parse feed %s" % feed_url
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



