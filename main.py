#! /usr/bin/env python

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
import re

import praw
import prawcore

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
    subs = Subreddit.objects.filter(forbidden=False).order_by('-subscribers')
    remaining = subs.count()
    start = 0
    i = 0
    while True:
        t = datetime.now() - timedelta(minutes=(2**(i - 2)) * 60)
        end = min(2 ** (i + 8), remaining)
        #print(end)
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
    sub_model = Subreddit.objects.get_or_create(name_lower=sub.lower(), defaults={'name' : sub, 'forbidden' : False})
    try:
        sub_model[0].subscribers = sub_obj.subscribers
        sub_model[0].save()
    except prawcore.exceptions.PrawcoreException as e:
        print(e)
        sub_model[0].forbidden = True
        sub_model[0].save()
        return

    if (sub_model[1] == True):
        print("Added new sub " + sub)
        curr_mods = []
        new = True
    else:
        curr_mods = sub_model[0].latest_mods()
        sub_model[0].last_checked = datetime.now()
        sub_model[0].save()
        new = False

    query = SubredditQuery.objects.create(sub=sub_model[0])
    query.save()

    mods = []
    change = False
    for mod in sub_obj.moderator:
        if mod.name == 'AutoModerator':
            continue
        mod_model = User.objects.get_or_create(username=mod.name)
        mods.append(mod_model[0])

        if new == False and change == False:
            if mod_model[1] == True:
                change = True
                continue

            for c in curr_mods:
                if c.username == mod_model[0].username:
                    curr_mods.remove(c)

    if new == False and (change == True or len(curr_mods) != 0):
        print("Mods of " + sub + " have changed")
        print(curr_mods)
        sub_model[0].last_changed = datetime.now()
        sub_model[0].save()

    query.mods.add(*mods)
    query.save()

def simple_method(reddit):
    def action(name, delta, action, strict=False):
        created = datetime.now()
        action_entry = LastChecked.objects.get_or_create(name=name)[0]
        def perform():
            now = datetime.now()
            if action_entry.last_checked < now - delta:
                if strict:
                    if action_entry.last_checked < created:
                        iters = (now - created) // delta
                    else:
                        iters = (now - action_entry.last_checked) // delta

                    print("Strict mode on, performing action " + name + " " + str(iters) + " times")
                    for _ in range(iters):
                        action()
                else:
                    action()
                action_entry.last_checked = now
                action_entry.save()
        return perform

    def rall_action_impl():
        print("Querying top 100 r/all subs")
        for sub in set([post.subreddit.display_name for post in reddit.subreddit('all').hot(limit=100)]):
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

    def trending_action_impl():
        print("Querying daily trending")
        post = list(reddit.subreddit('trendingsubreddits').new(limit=1))[0]
        for sub in set(re.findall('/r/[A-Za-z]+', str(post.selftext))):
            name = sub[3:]
            print("Querying " + name)
            query_sub(reddit, name)

    def sub_action_impl(s):
        def f():
            for post in reddit.subreddit(s).new(limit=25):
                match = re.search('/r/[A-Za-z]+', str(post.url))
                if match:
                    name = match.group(0)[3:]
                    print("Querying " + name)
                    query_sub(reddit, name)
        return f


    r = Random()
    rall_action = action('rall', timedelta(hours=1), rall_action_impl)
    random_action = action('random', timedelta(seconds=3), random_action_impl, True)
    trending_action = action('trending', timedelta(hours=24), trending_action_impl)
    newreddits_action = action('newreddits', timedelta(hours=6), sub_action_impl('newreddits'))
    redditrequest_action = action('redditrequest', timedelta(hours=6), sub_action_impl('redditrequest'))
    #adoptareddit_action = action('adoptareddit', timedelta(hours=6), sub_action_impl('adoptareddit'))
    NOTSONEWREDDITS_action = action('NOTSONEWREDDITS', timedelta(hours=6), sub_action_impl('NOTSONEWREDDITS'))
    obscuresubreddits_action = action('obscuresubreddits', timedelta(hours=6), sub_action_impl('obscuresubreddits'))
    newreddits_nsfw_action = action('newreddits_nsfw', timedelta(hours=6), sub_action_impl('newreddits_nsfw'))

    while True:
        for sub in get_subs_by_last_changed():
            print("Updating " + sub + " for recently changed")
            query_sub(reddit, sub)

        for sub in get_subs():
            print("Updating " + sub + " for size")
            query_sub(reddit, sub)

        rall_action()
        random_action()
        trending_action()
        newreddits_action()
        redditrequest_action()
        #adoptareddit_action()
        NOTSONEWREDDITS_action()
        obscuresubreddits_action()
        newreddits_nsfw_action()

if __name__ == '__main__':
    LastChecked.objects.get_or_create(name='last_started', defaults={ 'last_checked' : datetime.now() })
    reddit = praw.Reddit(client_id='ufxVBVi9_Z03Gg',
                         client_secret='_zyrtt2C1oF2020U3dIBVHMb7V0',
                         user_agent='unix:modt:v0.6 (by /u/ssjjawa)')

    simple_method(reddit)
