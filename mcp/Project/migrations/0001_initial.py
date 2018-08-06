# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-06-05 19:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from datetime import datetime, timezone
import mcp.fields


def load_builtins( app, schema_editor ):
  Project = app.get_model( 'Project', 'Project' )

  p = Project( name='_builtin_' )
  p.local_path = ''
  p.last_checked = datetime.now( timezone.utc )
  p.full_clean()
  p.save()

  Build = app.get_model( 'Project', 'Build' )
  BuildResource = app.get_model( 'Project', 'BuildResource' )
  Resource = app.get_model( 'Resource', 'Resource' )

  for name in ( 'ubuntu-trusty', 'ubuntu-xenial', 'ubuntu-bionic', 'centos-6' ):
    b = Build( name=name, project=p )
    b.manual = False
    b.key = '{0}_{1}'.format( b.project.name, b.name )  # from full_clean
    b.full_clean()
    b.save()

    br = BuildResource( name=name, build=b, resource=Resource.objects.get( pk='{0}-small'.format( name ) ) )
    br.quanity = 1
    br.key = '{0}_{1}_{2}'.format( br.build.key, br.name, br.resource.name )  # from full_clean
    br.full_clean()
    br.save()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Resource', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Build',
            fields=[
                ('key', models.CharField(editable=False, max_length=160, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('network_map', mcp.fields.MapField(blank=True, default={})),
                ('manual', models.BooleanField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='BuildDependancy',
            fields=[
                ('key', models.CharField(editable=False, max_length=250, primary_key=True, serialize=False)),
                ('from_state', models.CharField(max_length=10)),
                ('build', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Project.Build')),
            ],
        ),
        migrations.CreateModel(
            name='BuildResource',
            fields=[
                ('key', models.CharField(editable=False, max_length=250, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('quanity', models.IntegerField(default=1)),
                ('build', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Project.Build')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Resource.Resource')),
            ],
        ),
        migrations.CreateModel(
            name='Commit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('owner_override', models.CharField(blank=True, max_length=50, null=True)),
                ('branch', models.CharField(max_length=50)),
                ('commit', models.CharField(max_length=45)),
                ('lint_results', mcp.fields.MapField(blank=True, default={})),
                ('test_results', mcp.fields.MapField(blank=True, default={})),
                ('build_results', mcp.fields.MapField(blank=True, default={})),
                ('doc_results', mcp.fields.MapField(blank=True, default={})),
                ('test_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('build_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('doc_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('done_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('passed', models.NullBooleanField(editable=False)),
                ('built', models.NullBooleanField(editable=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('name', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='PackageVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=50)),
                ('state', models.CharField( max_length=10)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Project.Package')),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('name', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('local_path', models.CharField(blank=True, editable=False, max_length=150, null=True)),
                ('last_checked', models.DateTimeField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='GitHubProject',
            fields=[
                ('project_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='Project.Project')),
                ('_org', models.CharField(max_length=50)),
                ('_repo', models.CharField(max_length=50)),
            ],
            bases=('Project.project',),
        ),
        migrations.CreateModel(
            name='GitProject',
            fields=[
                ('project_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='Project.Project')),
                ('git_url', models.CharField(max_length=200)),
            ],
            bases=('Project.project',),
        ),
        migrations.AddField(
            model_name='commit',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Project.Project'),
        ),
        migrations.AddField(
            model_name='builddependancy',
            name='package',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Project.Package'),
        ),
        migrations.AddField(
            model_name='build',
            name='dependancies',
            field=models.ManyToManyField(through='Project.BuildDependancy', to='Project.Package'),
        ),
        migrations.AddField(
            model_name='build',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Project.Project'),
        ),
        migrations.AddField(
            model_name='build',
            name='resources',
            field=models.ManyToManyField(through='Project.BuildResource', to='Resource.Resource'),
        ),
        migrations.AlterUniqueTogether(
            name='packageversion',
            unique_together=set([('package', 'version')]),
        ),
        migrations.AlterUniqueTogether(
            name='buildresource',
            unique_together=set([('build', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='builddependancy',
            unique_together=set([('build', 'package')]),
        ),
        migrations.AlterUniqueTogether(
            name='build',
            unique_together=set([('name', 'project')]),
        ),
        migrations.RunPython( load_builtins ),
    ]
