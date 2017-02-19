# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-19 16:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subreddit',
            name='nsfw',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='subredditevent',
            name='sub',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='api.Subreddit'),
        ),
        migrations.AlterField(
            model_name='subredditeventdetail',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='details', to='api.SubredditEvent'),
        ),
    ]
