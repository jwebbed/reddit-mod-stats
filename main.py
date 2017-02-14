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
# the higher the frequency we check it starting at 1m and 10s and increasing
# exponetially

def get_subs_by_last_changed():
    subs = Subreddit.objects.filter(forbidden=False).order_by('-last_changed')
    threshold =  datetime.now() - timedelta(days=7)
    now = datetime.now()
    for sub in subs:
        if sub.last_changed < threshold:
            break
        diff = now - sub.last_changed
        mins = diff.total_seconds() // 60
        if mins <= 1:
            rank = 0
        else:
            rank = log2(mins)
        if sub.last_checked < (now - timedelta(seconds=((2 ** rank) * 10))):
            yield sub.name_lower


# Priority Algorithm
# Broken into n bins size 2^(i + 8) starting at i = 0
# Bins are for the largest subs
# The frequency at which a sub should be checked is 2^(i - 2) hours

def get_subs_by_size():
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
                yield sub.name_lower

        if end == remaining:
            break
        else:
            remaining -= end
            start += end
            i += 1


def query_sub(r, sub):
    sub_obj = reddit.subreddit(sub)
    sub_model = Subreddit.objects.get_or_create(name_lower=sub.lower(), defaults={'forbidden' : False})
    try:
        sub_model[0].subscribers = sub_obj.subscribers
        sub_model[0].name = sub_obj.display_name
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
    new_mods = []
    change = False
    for mod in sub_obj.moderator:
        if mod.name == 'AutoModerator':
            continue
        mod_model = User.objects.get_or_create(username=mod.name)
        mods.append(mod_model[0])

        if new == False:
            if mod_model[1] == True:
                change = True

            removed = False
            for c in curr_mods:
                if c.username == mod_model[0].username:
                    curr_mods.remove(c)
                    removed = True
                    break
            if removed == False:
                new_mods.append(mod_model[0])
                change = True

    if new == False and (change == True or len(curr_mods) != 0):
        print('Mods of ' + sub + ' have changed')
        print('Removed: ' + str(curr_mods))
        print('Added: ' + str(new_mods))
        sub_model[0].last_changed = datetime.now()
        sub_model[0].save()

    query.mods.add(*mods)
    query.save()

def simple_method(reddit):
    r = Random()
    def action(name, delta, action, strict=False):
        if delta:
            created = LastChecked.objects.get(name='last_started').last_checked
            action_entry = LastChecked.objects.get_or_create(name=name)[0]
        def perform():
            now = datetime.now()
            if delta == False:
                action()
            elif action_entry.last_checked < now - delta:
                if strict:
                    if action_entry.last_checked < created:
                        iters = (now - created) // delta
                    else:
                        iters = (now - action_entry.last_checked) // delta
                    iters = iters ** 0.95
                    iters = max(int(iters), 1)

                    if iters > 1:
                        print("Strict mode on, performing action " + name + " " + str(iters) + " times")
                    for _ in range(iters):
                        action()
                else:
                    action()
                action_entry.last_checked = datetime.now()
                action_entry.save()
        return perform

    def rall_action_impl():
        print("Querying top 100 r/all subs")
        for sub in set([post.subreddit.display_name for post in reddit.subreddit('all').hot(limit=100)]):
            print("Querying " + sub)
            query_sub(reddit, sub)

    def random_action_impl():
        for _ in range(2):
            b = False
            if r.random() <= 0.05:
                b = True
            sub = reddit.random_subreddit(nsfw=b)
            print("Querying " + sub.display_name + " randomly")
            query_sub(reddit, sub.display_name)

    def trending_action_impl():
        print("Querying daily trending")
        post = list(reddit.subreddit('trendingsubreddits').new(limit=1))[0]
        for sub in set(re.findall('/r/[A-Za-z]+', str(post.selftext))):
            name = sub[3:]
            print("Querying " + name)
            query_sub(reddit, name)

    def least_freq_action_impl():
        for sub in Subreddit.objects.filter(forbidden=False).order_by('last_checked')[:2]:
            print("Updating " + sub.name_lower + " for least recently checked")
            query_sub(reddit, sub.name_lower)

    def subs_by_size_action_impl():
        for sub in get_subs_by_size():
            print("Updating " + sub + " for size")
            query_sub(reddit, sub)

    def subs_by_last_changed_action_impl():
        for sub in get_subs_by_last_changed():
            print("Updating " + sub + " for recently changed")
            query_sub(reddit, sub)

    def sub_action_impl(s):
        def f():
            subs = set()
            for post in reddit.subreddit(s).new(limit=25):
                match = re.search('/r/[A-Za-z]+', str(post.url))
                if match:
                    name = match.group(0)[3:]
                    subs.add(name)
                if 'selftext' in dir(post) or 'selftext' in vars(post):
                    for m in re.findall('/r/[A-Za-z]+', str(post.selftext)):
                        subs.add(m[3:])
            for sub in subs:
                print("Querying " + sub)
                query_sub(reddit, sub)
        return f

    actions = (
        action('changed', False, subs_by_last_changed_action_impl),
        action('size', False, subs_by_size_action_impl),
        action('rall', timedelta(hours=1), rall_action_impl),
        action('random', timedelta(seconds=3), random_action_impl, True),
        action('least_freq', timedelta(seconds=3), least_freq_action_impl, True),
        action('trending', timedelta(hours=24), trending_action_impl),
        action('newreddits', timedelta(hours=6), sub_action_impl('newreddits')),
        action('redditrequest', timedelta(hours=6), sub_action_impl('redditrequest')),
        action('adoptareddit', timedelta(hours=6), sub_action_impl('adoptareddit')),
        action('NOTSONEWREDDITS', timedelta(hours=6), sub_action_impl('NOTSONEWREDDITS')),
        action('obscuresubreddits', timedelta(hours=6), sub_action_impl('obscuresubreddits')),
        action('newreddits_nsfw', timedelta(hours=6), sub_action_impl('newreddits_nsfw')),
    )


    while True:
        for action in actions:
            action()

if __name__ == '__main__':
    LastChecked.objects.get_or_create(name='last_started', defaults={ 'last_checked' : datetime.now() })
    reddit = praw.Reddit(client_id='ufxVBVi9_Z03Gg',
                         client_secret='_zyrtt2C1oF2020U3dIBVHMb7V0',
                         user_agent='unix:modt:v0.7 (by /u/ssjjawa)')

    simple_method(reddit)
