# -*- coding:utf-8 -*-


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


from rdflib import Namespace
COMMON_DOMAINS = [
    'http://data.economie-solidaire.fr',
    'http://rdf.insee.fr/geo/'
    ]


DJRDF_NS = AttributeDict(

    rdf=Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#'),
    rdfs=Namespace('http://www.w3.org/2000/01/rdf-schema#'),
    owl=Namespace('http://www.w3.org/2002/07/owl#'),
    xsd=Namespace('http://www.w3.org/2001/XMLSchema#'),
    dct=Namespace('http://purl.org/dc/terms/'),

)


FEED_MODELS = ['organization', 'contact', 'exchange']
# Later ....
# FEED_MODELS=['organization', 'person', 'role', 'product', 'engagement',
#               'relation', 'exchange', 'contact', 'article']


# Using subhub, the hud max lease time for a subscription is 1 year. So we cannot
# avoid handling the lease time.
PUSH_LEASE_SECONDS = 365 * 86400
# Django-push. This variable is not set here because it needs to import Site
# The hud is set in the Feed class
PUSH_HUB = ''
