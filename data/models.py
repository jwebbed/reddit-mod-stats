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

class Subreddit(models.Model):
    name_lower = models.CharField(max_length=22, primary_key=True)
    name = models.CharField(max_length=22)
    subscribers = models.IntegerField(default=0)
    last_checked = models.DateTimeField(auto_now_add=True)
    last_changed = models.DateTimeField(auto_now_add=True)
    forbidden = models.BooleanField(default=False)

    def latest_mods(self):
        query = self.subredditquery_set.latest('time').prev
        
        return [m for m in query.mods.all()]

class SubredditQuery(models.Model):
    sub = models.ForeignKey(Subreddit)
    mods = models.ManyToManyField(User)
    time = models.DateTimeField(auto_now_add=True)
    prev = models.ForeignKey("SubredditQuery", null=True)

class LastChecked(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    last_checked = models.DateTimeField(default=datetime(1970, 1, 1))
