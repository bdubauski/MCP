# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-07-06 17:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import mcp.Processor.models
import mcp.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Project', '0001_initial'),
        ('Resource', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuildJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('branch', models.CharField(max_length=50)),
                ('target', models.CharField(max_length=50)),
                ('build_name', models.CharField(max_length=50)),
                ('value_map', mcp.fields.MapField(blank=True)),
                ('built_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('ran_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('reported_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('acknowledged_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('released_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('manual', models.BooleanField()),
                ('user', models.CharField(max_length=150)),
                ('package_file_map', mcp.fields.MapField(blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('build', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, to='Project.Build')),
                ('commit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Project.Commit')),
                ('project', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, to='Project.Project')),
            ],
            options={'default_permissions': (), 'permissions': (('can_build', 'Can queue builds'), ('can_ran', 'Can Flag a Build Resource as ran'), ('can_ack', 'Can Acknoledge a failed Build Resource'))},
        ),
        migrations.CreateModel(
            name='Instance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cookie', models.CharField(default=mcp.Processor.models.getCookie, max_length=36)),
                ('hostname', models.CharField(max_length=100)),
                ('name', models.CharField(blank=True, max_length=50, null=True)),
                ('index', models.IntegerField(blank=True, null=True)),
                ('state', models.CharField(choices=[('allocated', 'allocated'), ('building', 'building'), ('built', 'built'), ('ran', 'ran'), ('releasing', 'releasing'), ('released', 'released')], default='allocated', max_length=9)),
                ('message', models.CharField(blank=True, default='', max_length=200)),
                ('success', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('foundation_id', models.CharField(blank=True, max_length=100, null=True)),
                ('structure_id', models.CharField(blank=True, max_length=100, null=True)),
                ('buildjob', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='Processor.BuildJob')),
                ('interface_map', mcp.fields.MapField(default={})),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Resource.Resource')),
            ],
            options={'default_permissions': ()},
        ),
        migrations.CreateModel(
            name='PackageFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=100)),
                ('packrat_id', models.CharField(max_length=100, unique=True)),
                ('group', models.CharField(db_index=True, max_length=45)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Project.Package')),
            ],
            options={'default_permissions': ()},
        ),
        migrations.CreateModel(
            name='Promotion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.CharField(max_length=10)),
                ('result_map', mcp.fields.MapField(blank=True)),
                ('group', models.CharField(db_index=True, max_length=45)),
                ('done_at', models.DateTimeField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={'default_permissions': ()},
        ),
        migrations.CreateModel(
            name='PromotionBuild',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=50)),
                ('success', models.NullBooleanField()),
                ('build', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Project.Build')),
                ('promotion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Processor.Promotion')),
            ],
            options={'default_permissions': ()},
        ),
        migrations.CreateModel(
            name='QueueItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('branch', models.CharField(max_length=50)),
                ('target', models.CharField(max_length=50)),
                ('priority', models.IntegerField(default=50)),
                ('manual', models.BooleanField()),
                ('user', models.CharField(max_length=150)),
                ('resource_status_map', mcp.fields.MapField(blank=True, default={})),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('build', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='Project.Build')),
                ('commit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Project.Commit')),
                ('project', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='Project.Project')),
                ('promotion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Processor.Promotion')),
            ],
            options={'default_permissions': ()},
        ),
        migrations.AddField(
            model_name='promotion',
            name='status',
            field=models.ManyToManyField(through='Processor.PromotionBuild', to='Project.Build'),
        ),
        migrations.AddField(
            model_name='buildjob',
            name='promotion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Processor.Promotion'),
        ),
        migrations.AlterUniqueTogether(
            name='promotionbuild',
            unique_together=set([('promotion', 'build')]),
        ),
    ]
