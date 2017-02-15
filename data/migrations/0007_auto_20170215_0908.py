# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-15 09:08
from __future__ import unicode_literals

from django.db import migrations

def populate_mod_relation(apps, schema_editor):
    SubredditQuery = apps.get_model('data', 'SubredditQuery')
    Subreddit = apps.get_model('data', 'Subreddit')
    ModRelation = apps.get_model('data', 'ModRelation')

    for sub in Subreddit.objects.all():
        print('Populating mod relation for ' + sub.name)
        query = SubredditQuery.objects.filter(sub=sub).latest('time').prev
        relations = []
        for mod in query.mods.all():
            relations.append(ModRelation(sub=sub, mod=mod))
        ModRelation.objects.bulk_create(relations)


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0006_auto_20170215_0908'),
    ]

    operations = [
        migrations.RunPython(populate_mod_relation)
    ]
