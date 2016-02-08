# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        for gh in orm.Project.githubproject:
          parts = gh.git_url.split( '/' )
          gh.org = parts[3]
          gh.repo = parts[4]
          gh.save()

    def backwards(self, orm):
        pass

    models = {
        'Project.build': {
            'Meta': {'unique_together': "(('name', 'project'),)", 'object_name': 'Build'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dependancies': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Project.Package']", 'through': "orm['Project.BuildDependancy']", 'symmetrical': 'False'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '160', 'primary_key': 'True'}),
            'manual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'networks': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Project']"}),
            'resources': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Resource.Resource']", 'through': "orm['Project.BuildResource']", 'symmetrical': 'False'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'Project.builddependancy': {
            'Meta': {'unique_together': "(('build', 'package'),)", 'object_name': 'BuildDependancy'},
            'build': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Build']"}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '250', 'primary_key': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Package']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '5'})
        },
        'Project.buildresource': {
            'Meta': {'unique_together': "(('build', 'name'),)", 'object_name': 'BuildResource'},
            'build': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Build']"}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '250', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'quanity': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Resource.Resource']"})
        },
        'Project.commit': {
            'Meta': {'unique_together': "(('project', 'commit'),)", 'object_name': 'Commit'},
            'branch': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'build_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'build_results': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'commit': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'done_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lint_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'lint_results': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Project']"}),
            'test_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'test_results': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'Project.githubproject': {
            'Meta': {'object_name': 'GitHubProject', '_ormbases': ['Project.Project']},
            'git_url': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'project_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['Project.Project']", 'unique': 'True', 'primary_key': 'True'}),
            'repo_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'org_name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'Project.gitproject': {
            'Meta': {'object_name': 'GitProject', '_ormbases': ['Project.Project']},
            'git_url': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'project_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['Project.Project']", 'unique': 'True', 'primary_key': 'True'})
        },
        'Project.package': {
            'Meta': {'object_name': 'Package'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'Project.packageversion': {
            'Meta': {'unique_together': "(('package', 'version'),)", 'object_name': 'PackageVersion'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Package']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'Project.project': {
            'Meta': {'object_name': 'Project'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'last_checked': ('django.db.models.fields.DateTimeField', [], {}),
            'local_path': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'Resource.resource': {
            'Meta': {'object_name': 'Resource'},
            'config_profile': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['Project']
