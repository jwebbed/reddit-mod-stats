# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-14 07:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0002_auto_20170213_1057'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subreddit',
            name='name',
            field=models.CharField(max_length=22),
        ),
    ]
