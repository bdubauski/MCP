# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'VMResource.build_ahead_count'
        db.add_column('Resource_vmresource', 'build_ahead_count',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'VMResource.build_ahead_count'
        db.delete_column('Resource_vmresource', 'build_ahead_count')


    models = {
        'Resource.hardwareresource': {
            'Meta': {'object_name': 'HardwareResource', '_ormbases': ['Resource.Resource']},
            'hardware_template': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['Resource.Resource']", 'unique': 'True', 'primary_key': 'True'})
        },
        'Resource.resource': {
            'Meta': {'object_name': 'Resource'},
            'config_profile': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'Resource.resourcegroup': {
            'Meta': {'object_name': 'ResourceGroup'},
            '_config_list': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'Resource.vmresource': {
            'Meta': {'object_name': 'VMResource', '_ormbases': ['Resource.Resource']},
            'build_ahead_count': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['Resource.Resource']", 'unique': 'True', 'primary_key': 'True'}),
            'vm_template': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['Resource']
