# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'EntrySite.auto_subscribe'
        db.add_column('import_rdf_entrysite', 'auto_subscribe', self.gf('django.db.models.fields.BooleanField')(default=True), keep_default=False)

        # Changing field 'EntrySite.label'
        db.alter_column('import_rdf_entrysite', 'label', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100))

        # Adding unique constraint on 'EntrySite', fields ['label']
        db.create_unique('import_rdf_entrysite', ['label'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'EntrySite', fields ['label']
        db.delete_unique('import_rdf_entrysite', ['label'])

        # Deleting field 'EntrySite.auto_subscribe'
        db.delete_column('import_rdf_entrysite', 'auto_subscribe')

        # Changing field 'EntrySite.label'
        db.alter_column('import_rdf_entrysite', 'label', self.gf('django.db.models.fields.CharField')(max_length=300))


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
