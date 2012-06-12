from django.contrib import admin

from djrdf.import_rdf.models import EntrySite, SparqlQuery

admin.site.register(EntrySite)
admin.site.register(SparqlQuery)
