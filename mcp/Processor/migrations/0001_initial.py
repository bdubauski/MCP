# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Promotion'
        db.create_table('Processor_promotion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('to_state', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('Processor', ['Promotion'])

        # Adding model 'PromotionPkgVersion'
        db.create_table('Processor_promotionpkgversion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('promotion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Processor.Promotion'])),
            ('package_version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.PackageVersion'])),
            ('packrat_id', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('Processor', ['PromotionPkgVersion'])

        # Adding unique constraint on 'PromotionPkgVersion', fields ['promotion', 'package_version']
        db.create_unique('Processor_promotionpkgversion', ['promotion_id', 'package_version_id'])

        # Adding model 'PromotionBuild'
        db.create_table('Processor_promotionbuild', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('promotion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Processor.Promotion'])),
            ('build', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Build'])),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('Processor', ['PromotionBuild'])

        # Adding unique constraint on 'PromotionBuild', fields ['promotion', 'build']
        db.create_unique('Processor_promotionbuild', ['promotion_id', 'build_id'])

        # Adding model 'QueueItem'
        db.create_table('Processor_queueitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('build', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Build'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Project'])),
            ('branch', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('target', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('requires', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('priority', self.gf('django.db.models.fields.IntegerField')(default=50)),
            ('manual', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('resource_status', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('commit', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Commit'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('promotion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Processor.Promotion'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('Processor', ['QueueItem'])

        # Adding M2M table for field resource_groups on 'QueueItem'
        db.create_table('Processor_queueitem_resource_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('queueitem', models.ForeignKey(orm['Processor.queueitem'], null=False)),
            ('resourcegroup', models.ForeignKey(orm['Resource.resourcegroup'], null=False))
        ))
        db.create_unique('Processor_queueitem_resource_groups', ['queueitem_id', 'resourcegroup_id'])

        # Adding model 'BuildJob'
        db.create_table('Processor_buildjob', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('build', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Build'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Project'])),
            ('branch', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('target', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('requires', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('_resources', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('built_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ran_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('reported_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('released_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('manual', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('commit', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Project.Commit'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('promotion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['Processor.Promotion'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('Processor', ['BuildJob'])


    def backwards(self, orm):
        # Removing unique constraint on 'PromotionBuild', fields ['promotion', 'build']
        db.delete_unique('Processor_promotionbuild', ['promotion_id', 'build_id'])

        # Removing unique constraint on 'PromotionPkgVersion', fields ['promotion', 'package_version']
        db.delete_unique('Processor_promotionpkgversion', ['promotion_id', 'package_version_id'])

        # Deleting model 'Promotion'
        db.delete_table('Processor_promotion')

        # Deleting model 'PromotionPkgVersion'
        db.delete_table('Processor_promotionpkgversion')

        # Deleting model 'PromotionBuild'
        db.delete_table('Processor_promotionbuild')

        # Deleting model 'QueueItem'
        db.delete_table('Processor_queueitem')

        # Removing M2M table for field resource_groups on 'QueueItem'
        db.delete_table('Processor_queueitem_resource_groups')

        # Deleting model 'BuildJob'
        db.delete_table('Processor_buildjob')


    models = {
        'Processor.buildjob': {
            'Meta': {'object_name': 'BuildJob'},
            '_resources': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'branch': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'build': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Build']"}),
            'built_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'commit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Commit']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Project.Project']"}),
            'promotion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['Processor.Promotion']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'ran_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'released_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'reported_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'requires': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'target': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
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
            'requires': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'resource_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Resource.ResourceGroup']", 'symmetrical': 'False'}),
            'resource_status': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'target': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
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
        },
        'Resource.resourcegroup': {
            'Meta': {'object_name': 'ResourceGroup'},
            '_config_list': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['Processor']