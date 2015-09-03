# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Resource'
        db.create_table('Resource_resource', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('config_profile', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('Resource', ['Resource'])

        # Adding model 'VMResource'
        db.create_table('Resource_vmresource', (
            ('resource_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['Resource.Resource'], unique=True, primary_key=True)),
            ('vm_template', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('Resource', ['VMResource'])

        # Adding model 'HardwareResource'
        db.create_table('Resource_hardwareresource', (
            ('resource_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['Resource.Resource'], unique=True, primary_key=True)),
            ('hardware_template', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('Resource', ['HardwareResource'])

        # Adding model 'ResourceGroup'
        db.create_table('Resource_resourcegroup', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('_config_list', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('Resource', ['ResourceGroup'])


    def backwards(self, orm):
        # Deleting model 'Resource'
        db.delete_table('Resource_resource')

        # Deleting model 'VMResource'
        db.delete_table('Resource_vmresource')

        # Deleting model 'HardwareResource'
        db.delete_table('Resource_hardwareresource')

        # Deleting model 'ResourceGroup'
        db.delete_table('Resource_resourcegroup')


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
            'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['Resource.Resource']", 'unique': 'True', 'primary_key': 'True'}),
            'vm_template': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['Resource']