# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-22 08:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0004_lastchecked'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lastchecked',
            name='name',
            field=models.CharField(max_length=30, primary_key=True, serialize=False),
        ),
    ]