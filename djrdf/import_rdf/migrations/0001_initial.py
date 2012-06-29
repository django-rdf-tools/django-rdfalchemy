# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SparqlQuery'
        db.create_table('import_rdf_sparqlquery', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('query', self.gf('django.db.models.fields.TextField')()),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('notation', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('import_rdf', ['SparqlQuery'])

        # Adding model 'EntrySite'
        db.create_table('import_rdf_entrysite', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('home', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('sparqlEndPoint', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('feed', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('logs', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('import_rdf', ['EntrySite'])


    def backwards(self, orm):
        
        # Deleting model 'SparqlQuery'
        db.delete_table('import_rdf_sparqlquery')

        # Deleting model 'EntrySite'
        db.delete_table('import_rdf_entrysite')


    models = {
        'import_rdf.entrysite': {
            'Meta': {'object_name': 'EntrySite'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'feed': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'home': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'logs': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'sparqlEndPoint': ('django.db.models.fields.CharField', [], {'max_length': '250'})
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
