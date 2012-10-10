# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'EntrySite.sparqlEndPoint'
        db.delete_column('import_rdf_entrysite', 'sparqlEndPoint')

        # Adding field 'EntrySite.rdfEndPoint'
        db.add_column('import_rdf_entrysite', 'rdfEndPoint',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=250),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'EntrySite.sparqlEndPoint'
        db.add_column('import_rdf_entrysite', 'sparqlEndPoint',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=250),
                      keep_default=False)

        # Deleting field 'EntrySite.rdfEndPoint'
        db.delete_column('import_rdf_entrysite', 'rdfEndPoint')


    models = {
        'import_rdf.entrysite': {
            'Meta': {'object_name': 'EntrySite'},
            'auto_subscribe': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'feed': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'home': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'hub': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'logs': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'rdfEndPoint': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        'import_rdf.sparqlquery': {
            'Meta': {'object_name': 'SparqlQuery'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'notation': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'query': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['import_rdf']