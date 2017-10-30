# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Project'
        db.create_table('Project_project', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, primary_key=True)),
            ('local_path', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('last_checked', self.gf('django.db.models.fields.DateTimeField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('Project', ['Project'])

        # Adding model 'GitHubProject'
        db.create_table('Project_githubproject', (
            ('project_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['Project.Project'], unique=True, primary_key=True)),
            ('github_url', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('Project', ['GitHubProject'])

        # Adding model 'Package'
        db.create_table('Project_package', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('Project', ['Package'])

        # Adding model 'PackageVersion'
        db.create_table('Project_packageversion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Package'])),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('Project', ['PackageVersion'])

        # Adding unique constraint on 'PackageVersion', fields ['package', 'version']
        db.create_unique('Project_packageversion', ['package_id', 'version'])

        # Adding model 'Commit'
        db.create_table('Project_commit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Project'])),
            ('branch', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('commit', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('lint_results', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('test_results', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('build_results', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('lint_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('test_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('build_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('done_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('Project', ['Commit'])

        # Adding unique constraint on 'Commit', fields ['project', 'branch']
        db.create_unique('Project_commit', ['project_id', 'branch'])

        # Adding model 'Build'
        db.create_table('Project_build', (
            ('key', self.gf('django.db.models.fields.CharField')(max_length=160, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Project'])),
            ('manual', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('Project', ['Build'])

        # Adding unique constraint on 'Build', fields ['name', 'project']
        db.create_unique('Project_build', ['name', 'project_id'])

        # Adding model 'BuildDependancy'
        db.create_table('Project_builddependancy', (
            ('key', self.gf('django.db.models.fields.CharField')(max_length=250, primary_key=True)),
            ('build', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Build'])),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Package'])),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=5)),
        ))
        db.send_create_signal('Project', ['BuildDependancy'])

        # Adding unique constraint on 'BuildDependancy', fields ['build', 'package']
        db.create_unique('Project_builddependancy', ['build_id', 'package_id'])

        # Adding model 'BuildResource'
        db.create_table('Project_buildresource', (
            ('key', self.gf('django.db.models.fields.CharField')(max_length=250, primary_key=True)),
            ('build', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Build'])),
            ('resource', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Resource.Resource'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('quanity', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal('Project', ['BuildResource'])

        # Adding unique constraint on 'BuildResource', fields ['build', 'name']
        db.create_unique('Project_buildresource', ['build_id', 'name'])


    def backwards(self, orm):
        # Removing unique constraint on 'BuildResource', fields ['build', 'name']
        db.delete_unique('Project_buildresource', ['build_id', 'name'])

        # Removing unique constraint on 'BuildDependancy', fields ['build', 'package']
        db.delete_unique('Project_builddependancy', ['build_id', 'package_id'])

        # Removing unique constraint on 'Build', fields ['name', 'project']
        db.delete_unique('Project_build', ['name', 'project_id'])

        # Removing unique constraint on 'Commit', fields ['project', 'branch']
        db.delete_unique('Project_commit', ['project_id', 'branch'])

        # Removing unique constraint on 'PackageVersion', fields ['package', 'version']
        db.delete_unique('Project_packageversion', ['package_id', 'version'])

        # Deleting model 'Project'
        db.delete_table('Project_project')

        # Deleting model 'GitHubProject'
        db.delete_table('Project_githubproject')

        # Deleting model 'Package'
        db.delete_table('Project_package')

        # Deleting model 'PackageVersion'
        db.delete_table('Project_packageversion')

        # Deleting model 'Commit'
        db.delete_table('Project_commit')

        # Deleting model 'Build'
        db.delete_table('Project_build')

        # Deleting model 'BuildDependancy'
        db.delete_table('Project_builddependancy')

        # Deleting model 'BuildResource'
        db.delete_table('Project_buildresource')


    models = {
        'Project.build': {
            'Meta': {'unique_together': "(('name', 'project'),)", 'object_name': 'Build'},
            '_resources': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Resource.Resource']", 'through': "orm['Project.BuildResource']", 'symmetrical': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dependancies': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Project.Package']", 'through': "orm['Project.BuildDependancy']", 'symmetrical': 'False'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '160', 'primary_key': 'True'}),
            'manual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Project']"}),
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
            'Meta': {'unique_together': "(('project', 'branch'),)", 'object_name': 'Commit'},
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
            'github_url': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
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