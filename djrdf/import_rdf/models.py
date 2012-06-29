# -*- coding:utf-8 -*-
# Create your models here.
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django_push.subscriber.models import Subscription
from djrdf.repository import Repository
from rdflib import Graph, plugin, store, URIRef
import djrdf.tools
import tempfile
import os
import feedparser
import datetime


plugin.register(
        'SPARQLStore', store.Store,
        'rdflib_sparqlstore.SPARQLStore', 'SPARQLStore')
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
    label = models.CharField(_(u'Label'), max_length=300)
    description = models.TextField(_(u'description'), null=True, blank=True)
    home = models.CharField(_(u'home'), max_length=250)
    sparqlEndPoint = models.CharField(_(u'sparql endPoint URI'), max_length=250)
    feed = models.CharField(_(u'feed'), max_length=250)
    hub = models.CharField(_(u'hub'), max_length=250, blank=True)
    logs = models.TextField(_(u'logs'), null=True, blank=True)
    # Je ne suis pas sur que ca soit important
    # queries = models.ManyToManyField(SparqlQuery, verbose_name=_(u'queries'), related_name='queries')

    class Meta:
        verbose_name = _(u'Site entries')
        verbose_name_plural = _(u'Sites entries')

    def __unicode__(self):
        return self.label

    def sparql(self):
        graph = Graph(store="SPARQLStore")
        graph.open(self.sparqlEndPoint, False)
        graph.store.baseURI = str(self.sparqlEndPoint)
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
        if ctx == None:
            sesame = Repository(repository)
        else:
            if ctx == 'default':
                ctx = self.defaultCtxName
            ctx = "<%s>" % ctx
            sesame = Repository(repository, context=ctx)
        unknownTypes = []
        mapDjrdfTypes = djrdf.tools.rdfDjrdfMapTypes()
        subjects = graph.subjects(settings.NS.rdf.type, rdfType)
        for subject in subjects:
            stored_date = list(sesame.objects(subject, settings.NS.dct.modified))
            update_date = list(graph.objects(subject, settings.NS.dct.modified))
            if (not force) and len(update_date) == 1 and len(stored_date) == 1 and update_date[0].toPython() <= stored_date[0].toPython():
                print "Nothing to update for %s" % subject
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
                # Get the Django Model object
                addtriples = []
                triples = graph.triples((subject, None, None))
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
                    djSubject.addTriples(addtriples)
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

    def updateFromFeeds(self, repository, ctx='default'):
        for f in settings.FEED_MODELS:
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
        for f in settings.FEED_MODELS:
            feed_url = "%s%s/" % (self.feed, f)
            Subscription.objects.subscribe(feed_url, hub=self.hub)


    def unsubscribFeeds(self):
        for f in settings.FEED_MODELS:
            feed_url = "%s%s/" % (self.feed, f)
            Subscription.objects.unsubscribe(feed_url, hub=self.hub)



