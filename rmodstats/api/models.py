import sys
from datetime import datetime

try:
    from django.db import models
except Exception:
    print("There was an error loading django modules. Do you have django installed?")
    sys.exit()

class User(models.Model):
    username = models.CharField(max_length=20, primary_key=True)

    def __str__(self):
        return self.username

    def __hash__(self):
        return hash(self.username)

    def __eq__(self, other):
        return self.username == other.username

class Subreddit(models.Model):
    name_lower = models.CharField(max_length=22, primary_key=True)
    name = models.CharField(max_length=22)
    subscribers = models.IntegerField(default=0, db_index=True)
    last_checked = models.DateTimeField(auto_now_add=True)
    last_changed = models.DateTimeField(auto_now_add=True, db_index=True)
    forbidden = models.BooleanField(default=False, db_index=True)
    mods = models.ManyToManyField(User, through='ModRelation')

class SubredditEvent(models.Model):
    sub = models.ForeignKey(Subreddit, related_name='events')
    recorded = models.DateTimeField(auto_now_add=True)
    previous_check = models.DateTimeField(null=True)
    new = models.BooleanField()

class SubredditEventDetail(models.Model):
    event = models.ForeignKey(SubredditEvent, related_name='details')
    user = models.ForeignKey(User)
    addition = models.BooleanField()

class ModRelation(models.Model):
    sub = models.ForeignKey(Subreddit)
    mod = models.ForeignKey(User)

class LastChecked(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    last_checked = models.DateTimeField(default=datetime(1970, 1, 1))
