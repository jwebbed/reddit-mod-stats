#! /usr/bin/env python

# Django specific settings
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from time import sleep
from datetime import datetime, timedelta
import signal,sys
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

terminate = False

def signal_handling(signum,frame):
    global terminate
    terminate = True

# If a sub has been changed in the last week, there seems a higher probability
# if will be changed more soon. The closer it has been since it last has been changed
# the higher the frequency we check it starting at 1m and 10s and increasing
# exponetially

def get_subs_by_last_changed():
    subs = Subreddit.objects.filter(forbidden=False).order_by('-last_changed').values('last_changed', 'last_checked', 'name_lower')
    threshold =  datetime.now() - timedelta(days=7)
    now = datetime.now()
    for sub in subs:
        if sub['last_changed'] < threshold:
            break
        diff = now - sub['last_changed']
        mins = diff.total_seconds() // 60
        if mins <= 1:
            rank = 0
        else:
            rank = log2(mins)
        if sub['last_checked'] < (now - timedelta(seconds=((2 ** rank) * 10))):
            yield sub['name_lower']


# Priority Algorithm
# Broken into n bins size 2^(i + 8) starting at i = 0
# Bins are for the largest subs
# The frequency at which a sub should be checked is 2^(i - 2) hours

def get_subs_by_size():
    subs = Subreddit.objects.filter(forbidden=False).order_by('-subscribers').values('last_checked', 'name_lower')
    remaining = len(subs)
    start = 0
    i = 0
    while True:
        t = datetime.now() - timedelta(minutes=(2**(i - 2)) * 60)
        end = min(2 ** (i + 8), remaining)
        for sub in subs[start:end]:
            if sub['last_checked'] < t:
                yield sub['name_lower']

        if end == remaining:
            break
        else:
            remaining -= end
            start += end
            i += 1


def query_sub(r, sub):
    now = datetime.now()
    sub_obj = reddit.subreddit(sub)
    try:
        sub_model = Subreddit.objects.only('mods').get(name_lower=sub.lower())
        new = False
    except Subreddit.DoesNotExist:
        sub_model = Subreddit(name_lower=sub.lower())
        new = True

    try:
        if (new == True):
            print("Added new sub " + sub_obj.display_name)
            sub_model.subscribers = sub_obj.subscribers
            sub_model.name = sub_obj.display_name
            sub_model.save()
        curr_mods = set(sub_model.mods.values_list('username', flat=True))
        new_mods = set([m.name for m in sub_obj.moderator]) - set(('AutoModerator',))
    except prawcore.exceptions.PrawcoreException as e:
        print(e)
        sub_model.forbidden = True
        sub_model.save()
        return


    additions = new_mods - curr_mods
    removals = curr_mods - new_mods

    if len(additions) > 0 or len(removals) > 0:
        print('Mods of ' + sub + ' have changed')

        event = SubredditEvent(sub=sub_model, recorded=now, previous_check=sub_model.last_checked, new=new)
        event.save()

        relations = []
        if len(additions) > 0:
            print('Added: ' + str(additions))
            for mod in additions:
                user_query = User.objects.get_or_create(username=mod)
                relations.append(SubredditEventDetail(event=event, user=user_query[0], addition=True))

                modrel = ModRelation(sub=sub_model, mod=user_query[0])
                modrel.save()


        if len(removals) > 0:
            assert(new == False)
            print('Removed: ' + str(removals))
            for mod in removals:
                user_query = User.objects.get(username=mod)
                relations.append(SubredditEventDetail(event=event, user=user_query[0], addition=False))

                ModRelation.objects.get(sub=sub_model, mod=user_query[0]).delete()

        SubredditEventDetail.objects.bulk_create(relations)
        sub_model.last_changed = now

    sub_model.last_checked = now
    sub_model.save()

    if terminate:
        print("goodbye")
        sys.exit()

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
                    action(iters)
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

    def random_action_impl(iters=1):
        for _ in range(2 * iters):
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

    def least_freq_action_impl(iters=1):
        for sub in Subreddit.objects.filter(forbidden=False).order_by('last_checked')[:(2 * iters)].values_list('name_lower', flat=True):
            print("Updating " + sub + " for least recently checked")
            query_sub(reddit, sub)

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
        #action('random', False, random_action_impl),
        action('least_freq', timedelta(seconds=3), least_freq_action_impl, True),
        #action('least_freq', False, least_freq_action_impl),
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
    signal.signal(signal.SIGINT,signal_handling)

    entry = LastChecked.objects.get_or_create(name='last_started')
    entry[0].last_checked = datetime.now()
    entry[0].save()

    reddit = praw.Reddit(client_id='ufxVBVi9_Z03Gg',
                         client_secret='_zyrtt2C1oF2020U3dIBVHMb7V0',
                         user_agent='unix:modt:v0.9 (by /u/ssjjawa)')

    simple_method(reddit)
