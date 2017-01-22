# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-22 05:49
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0003_auto_20170121_1313'),
    ]

    operations = [
        migrations.CreateModel(
            name='LastChecked',
            fields=[
                ('name', models.CharField(max_length=16, primary_key=True, serialize=False)),
                ('last_checked', models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0))),
            ],
        ),
    ]
