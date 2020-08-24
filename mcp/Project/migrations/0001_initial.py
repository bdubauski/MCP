# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2020-08-24 17:03
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion
import mcp.fields


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
                ('network_map', mcp.fields.MapField(blank=True, default=mcp.fields.defaultdict, editable=True)),
                ('manual', models.BooleanField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='BuildDependancy',
            fields=[
                ('key', models.CharField(editable=False, max_length=250, primary_key=True, serialize=False)),
                ('tag', models.CharField(max_length=10)),
                ('build', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Project.Build')),
            ],
        ),
        migrations.CreateModel(
            name='BuildResource',
            fields=[
                ('key', models.CharField(editable=False, max_length=250, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('blueprint', models.CharField(max_length=40)),
                ('config_values', mcp.fields.MapField(blank=True, default=mcp.fields.defaultdict, editable=True)),
                ('quantity', models.IntegerField(default=1)),
                ('autorun', models.BooleanField(default=False)),
                ('interface_map', mcp.fields.MapField(blank=True, default=mcp.fields.defaultdict, editable=True)),
                ('build', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Project.Build')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Resource.Resource')),
            ],
        ),
        migrations.CreateModel(
            name='Commit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('branch', models.CharField(max_length=50)),
                ('commit', models.CharField(max_length=45)),
                ('version', models.CharField(blank=True, max_length=50, null=True)),
                ('lint_results', mcp.fields.MapField(blank=True, default=mcp.fields.defaultdict, editable=True)),
                ('test_results', mcp.fields.MapField(blank=True, default=mcp.fields.defaultdict, editable=True)),
                ('build_results', mcp.fields.MapField(blank=True, default=mcp.fields.defaultdict, editable=True)),
                ('doc_results', mcp.fields.MapField(blank=True, default=mcp.fields.defaultdict, editable=True)),
                ('test_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('build_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('doc_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('done_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('package_file_map', mcp.fields.MapField(blank=True, default=mcp.fields.defaultdict, editable=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('name', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('packrat_id', models.CharField(max_length=100, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='PackageFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=100)),
                ('packrat_id', models.CharField(max_length=100, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('commit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Project.Commit')),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Project.Package')),
            ],
            options={
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('name', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('release_branch', models.CharField(default='master', max_length=100)),
                ('local_path', models.CharField(blank=True, editable=False, max_length=150, null=True)),
                ('build_counter', models.IntegerField(default=0)),
                ('last_checked', models.DateTimeField(default=datetime.datetime(1, 1, 1, 0, 0))),
                ('max_commit_count', models.IntegerField(default=50)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='GitHubProject',
            fields=[
                ('project_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='Project.Project')),
                ('github_org', models.CharField(max_length=50)),
                ('github_repo', models.CharField(max_length=50)),
            ],
            bases=('Project.project',),
        ),
        migrations.CreateModel(
            name='GitLabProject',
            fields=[
                ('project_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='Project.Project')),
                ('gitlab_project_path', models.CharField(max_length=200)),
                ('gitlab_project_id', models.IntegerField()),
            ],
            bases=('Project.project',),
        ),
        migrations.CreateModel(
            name='GitProject',
            fields=[
                ('project_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='Project.Project')),
                ('git_repo', models.CharField(max_length=200)),
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
    ]
