# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-23 13:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0008_auto_20170123_1317'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subreddit',
            name='name',
            field=models.CharField(max_length=22),
        ),
        migrations.AlterField(
            model_name='subreddit',
            name='name_lower',
            field=models.CharField(max_length=22, primary_key=True, serialize=False),
        ),
    ]
