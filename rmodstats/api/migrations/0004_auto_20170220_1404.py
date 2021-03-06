# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-20 14:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_failure'),
    ]

    operations = [
        migrations.RenameField(
            model_name='failure',
            old_name='contents',
            new_name='exception_type',
        ),
        migrations.AddField(
            model_name='failure',
            name='traceback',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='failure',
            name='value',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
