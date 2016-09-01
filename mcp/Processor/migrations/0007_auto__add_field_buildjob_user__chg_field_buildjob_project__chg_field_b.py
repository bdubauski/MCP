# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'BuildJob.user'
        db.add_column('Processor_buildjob', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Users.MCPUser'], null=True, on_delete=models.SET_NULL, blank=True),
                      keep_default=False)


        # Changing field 'BuildJob.project'
        db.alter_column('Processor_buildjob', 'project_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Project'], on_delete=models.PROTECT))

        # Changing field 'BuildJob.build'
        db.alter_column('Processor_buildjob', 'build_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Build'], on_delete=models.PROTECT))
        # Adding field 'QueueItem.user'
        db.add_column('Processor_queueitem', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Users.MCPUser'], null=True, on_delete=models.SET_NULL, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'BuildJob.user'
        db.delete_column('Processor_buildjob', 'user_id')


        # Changing field 'BuildJob.project'
        db.alter_column('Processor_buildjob', 'project_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Project']))

        # Changing field 'BuildJob.build'
        db.alter_column('Processor_buildjob', 'build_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Build']))
        # Deleting field 'QueueItem.user'
        db.delete_column('Processor_queueitem', 'user_id')


    models = {
        'Processor.buildjob': {
            'Meta': {'object_name': 'BuildJob'},
            'acknowledged_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'branch': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'build': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Build']", 'on_delete': 'models.PROTECT'}),
            'built_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'commit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Commit']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'networks': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Resource.NetworkResource']", 'through': "orm['Processor.BuildJobNetworkResource']", 'symmetrical': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Project']", 'on_delete': 'models.PROTECT'}),
            'promotion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Processor.Promotion']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'ran_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'released_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'reported_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'resources': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'target': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Users.MCPUser']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'Processor.buildjobnetworkresource': {
            'Meta': {'unique_together': "(('buildjob', 'networkresource'), ('buildjob', 'name'))", 'object_name': 'BuildJobNetworkResource'},
            'buildjob': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Processor.BuildJob']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'networkresource': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Resource.NetworkResource']"})
        },
        'Processor.promotion': {
            'Meta': {'object_name': 'Promotion'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'package_versions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Project.PackageVersion']", 'through': "orm['Processor.PromotionPkgVersion']", 'symmetrical': 'False'}),
            'status': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Project.Build']", 'through': "orm['Processor.PromotionBuild']", 'symmetrical': 'False'}),
            'to_state': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'Processor.promotionbuild': {
            'Meta': {'unique_together': "(('promotion', 'build'),)", 'object_name': 'PromotionBuild'},
            'build': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Build']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'promotion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Processor.Promotion']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'Processor.promotionpkgversion': {
            'Meta': {'unique_together': "(('promotion', 'package_version'),)", 'object_name': 'PromotionPkgVersion'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'package_version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.PackageVersion']"}),
            'packrat_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'promotion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Processor.Promotion']"})
        },
        'Processor.queueitem': {
            'Meta': {'object_name': 'QueueItem'},
            'branch': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'build': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Build']"}),
            'commit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Commit']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '50'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Project']"}),
            'promotion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Processor.Promotion']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'resource_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Resource.ResourceGroup']", 'symmetrical': 'False'}),
            'resource_status': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'target': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Users.MCPUser']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
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
            'Meta': {'unique_together': "(('project', 'commit', 'branch'),)", 'object_name': 'Commit'},
            'branch': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'build_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'build_results': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'built': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'commit': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'docs_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'docs_results': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'done_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lint_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'lint_results': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'owner_override': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'passed': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Project']"}),
            'test_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'test_results': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
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
            'local_path': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'Resource.networkresource': {
            'Meta': {'object_name': 'NetworkResource'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'subnet': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
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
        'Users.mcpuser': {
            'Meta': {'object_name': 'MCPUser', '_ormbases': ['auth.User']},
            'github_oath': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'github_orgs': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'github_username': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Project.Project']", 'through': "orm['Users.MCPUserProject']", 'symmetrical': 'False'}),
            'slack_handle': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        'Users.mcpuserproject': {
            'Meta': {'unique_together': "(('user', 'project'),)", 'object_name': 'MCPUserProject'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Project']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Users.MCPUser']"})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['Processor']