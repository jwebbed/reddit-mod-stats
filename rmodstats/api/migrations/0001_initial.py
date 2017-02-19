# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-18 14:30
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LastChecked',
            fields=[
                ('name', models.CharField(max_length=30, primary_key=True, serialize=False)),
                ('last_checked', models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0))),
            ],
        ),
        migrations.CreateModel(
            name='ModRelation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Subreddit',
            fields=[
                ('name_lower', models.CharField(max_length=22, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=22)),
                ('subscribers', models.IntegerField(db_index=True, default=0)),
                ('last_checked', models.DateTimeField(auto_now_add=True)),
                ('last_changed', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('forbidden', models.BooleanField(db_index=True, default=False)),
            ],
        ),
        migrations.CreateModel(
            name='SubredditEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recorded', models.DateTimeField(auto_now_add=True)),
                ('previous_check', models.DateTimeField(null=True)),
                ('new', models.BooleanField()),
                ('sub', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Subreddit')),
            ],
        ),
        migrations.CreateModel(
            name='SubredditEventDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('addition', models.BooleanField()),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.SubredditEvent')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('username', models.CharField(max_length=20, primary_key=True, serialize=False)),
            ],
        ),
        migrations.AddField(
            model_name='subredditeventdetail',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.User'),
        ),
        migrations.AddField(
            model_name='subreddit',
            name='mods',
            field=models.ManyToManyField(through='api.ModRelation', to='api.User'),
        ),
        migrations.AddField(
            model_name='modrelation',
            name='mod',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.User'),
        ),
        migrations.AddField(
            model_name='modrelation',
            name='sub',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Subreddit'),
        ),
    ]