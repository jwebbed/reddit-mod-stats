# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-15 09:08
from __future__ import unicode_literals

import data.models
from django.db import migrations, models
import django.db.models.deletion
import enumfields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0005_auto_20170214_2222'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModRelation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mod', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.User')),
                ('sub', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.Subreddit')),
            ],
        ),
        migrations.CreateModel(
            name='SubredditEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recorded', models.DateTimeField(auto_now_add=True)),
                ('previous_check', models.DateTimeField()),
                ('sub', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.Subreddit')),
            ],
        ),
        migrations.CreateModel(
            name='SubredditEventDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', enumfields.fields.EnumField(enum=data.models.Event, max_length=10)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.SubredditEvent')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.User')),
            ],
        ),
        migrations.AddField(
            model_name='subreddit',
            name='mods',
            field=models.ManyToManyField(through='data.ModRelation', to='data.User'),
        ),
    ]