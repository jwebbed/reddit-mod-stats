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

import praw

reddit = praw.Reddit(client_id='ufxVBVi9_Z03Gg',
                     client_secret='_zyrtt2C1oF2020U3dIBVHMb7V0',
                     user_agent='unix:modt:v0.1 (by /u/ssjjawa)')

r = Random()

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


if __name__ == '__main__':
    while True:
        for sub in get_subs():
            print("Updating " + sub)
            query_sub(reddit, sub)

        for _ in range(25):
            b = False
            if r.random() <= 0.05:
                b = True
            sub = reddit.random_subreddit(nsfw=b)
            print("Querying " + sub.display_name)
            query_sub(reddit, sub.display_name)

        sleep(2.5)
