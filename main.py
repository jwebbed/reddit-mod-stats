# Django specific settings
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from time import sleep
from datetime import datetime, timedelta
# Ensure settings are read
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Your application specific imports
from data.models import *

from random import Random
from math import log2

import praw

def get_rall_subs(r):
    return [post.subreddit.display_name for post in r.subreddit('all').hot(limit=100)]

# If a sub has been changed in the last week, there seems a higher probability
# if will be changed more soon. The closer it has been since it last has been changed
# the higher the frequency we check it starting at 1 minutes and 5s and increasing
# exponetially

def get_subs_by_last_changed():
    subs = Subreddit.objects.order_by('-last_changed')
    threshold =  datetime.now() - timedelta(days=7)
    now = datetime.now()
    for sub in subs:
        if sub.last_changed < threshold:
            print('breaking')
            break
        diff = now - sub.last_changed
        mins = diff.total_seconds() // 60
        if mins <= 1:
            rank = 0
        else:
            rank = log2(mins)
        if sub.last_checked < (now - timedelta(seconds=((2 ** rank) * 5))):
            yield sub.name


# Priority Algorithm
# Broken into n bins size 2^(i + 8) starting at i = 0
# Bins are for the largest subs
# The frequency at which a sub should be checked is 2^(i - 2) hours

def get_subs():
    subs = Subreddit.objects.order_by('-subscribers')
    remaining = subs.count()
    start = 0
    i = 0
    while True:
        t = datetime.now() - timedelta(minutes=(2**(i - 2)) * 60)
        end = min(2 ** (i + 8), remaining)
        print(end)
        for sub in subs[start:end]:
            if sub.last_checked < t:
                yield sub.name

        if end == remaining:
            break
        else:
            remaining -= end
            start += end
            i += 1


def query_sub(r, sub):
    sub_obj = reddit.subreddit(sub)
    sub_model = Subreddit.objects.get_or_create(name=sub, defaults = {'subscribers' : sub_obj.subscribers})
    query = SubredditQuery.objects.create(sub=sub_model[0])
    query.save()

    if (sub_model[1] == True):
        print("Added new sub " + sub)
        curr_mods = []
    else:
        curr_mods = sub_model[0].latest_mods()
        sub_model[0].last_checked = datetime.now()
        sub_model[0].save()

    mods = []
    change = False
    for mod in sub_obj.moderator:
        if mod.name == 'AutoModerator':
            continue
        mod_model = User.objects.get_or_create(username=mod.name)
        mods.append(mod_model[0])

        if change == False:
            if mod_model[1] == True:
                change = True
                continue

            for c in curr_mods:
                if c == mod_model[0]:
                    curr_mods.remove(c)

    if change == True and len(curr_mods) != 0:
        print("Mods of " + sub + " have changed")
        sub_model[0].last_changed = datetime.now()
        sub_model[0].save()

    query.mods.add(*mods)
    query.save()

def simple_method(reddit):
    def action(name, delta, action):
        action_entry = LastChecked.objects.get_or_create(name=name)[0]
        def perform():
            if action_entry.last_checked < datetime.now() - delta:
                action()
                action_entry.last_checked = now
                action_entry.save()
        return perform

    def rall_action_impl():
        print("Querying top 100 r/all subs")
        for sub in get_rall_subs(reddit):
            print("Querying " + sub)
            query_sub(reddit, sub)

    def random_action_impl():
        print("Querying 2 random subs")
        for _ in range(2):
            b = False
            if r.random() <= 0.05:
                b = True
            sub = reddit.random_subreddit(nsfw=b)
            print("Querying " + sub.display_name)
            query_sub(reddit, sub.display_name)

    r = Random()
    rall_action = action('rall', timedelta(hours=1), rall_action_impl)
    random_action = action('random', timedelta(seconds=3), random_action_impl)

    while True:
        now = datetime.now()

        print("Checking and updating recently changed")
        for sub in get_subs_by_last_changed():
            print("Updating " + sub)
            query_sub(reddit, sub)

        print("Checking and updating with frequency on size")
        for sub in get_subs():
            print("Updating " + sub)
            query_sub(reddit, sub)

        rall_action()
        random_action()

if __name__ == '__main__':
    reddit = praw.Reddit(client_id='ufxVBVi9_Z03Gg',
                         client_secret='_zyrtt2C1oF2020U3dIBVHMb7V0',
                         user_agent='unix:modt:v0.1 (by /u/ssjjawa)')
    simple_method(reddit)
