import sys
from datetime import datetime

try:
    from django.db import models
except  Exception:
    print("There was an error loading django modules. Do you have django installed?")
    sys.exit()

class User(models.Model):
    username = models.CharField(max_length=20, primary_key=True)

class Subreddit(models.Model):
    name = models.CharField(max_length=22, primary_key=True)
    name_lower = models.CharField(max_length=22, unique=True)
    subscribers = models.IntegerField()
    last_checked = models.DateTimeField(auto_now_add=True)
    last_changed = models.DateTimeField(auto_now_add=True)

    def latest_mods(self):
        query = self.subredditquery_set.filter(time__isnull=False).latest('time').mods.all()
        print(len(query))
        return [m for m in query]

class SubredditQuery(models.Model):
    sub = models.ForeignKey(Subreddit)
    mods = models.ManyToManyField(User)
    time = models.DateTimeField(auto_now_add=True)

class LastChecked(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    last_checked = models.DateTimeField(default=datetime(1970, 1, 1))
