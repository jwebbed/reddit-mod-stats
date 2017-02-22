#! /usr/bin/env python

# Django specific settings
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rmodstats.settings")

from time import sleep
from datetime import datetime, timedelta
import signal,sys
from traceback import format_exc
# Ensure settings are read
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


# Your application specific imports
from rmodstats.api.models import *
from data_service.termination import *


from data_service.actions import get_actions

import praw
import prawcore

def simple_method(reddit):
    actions = get_actions(reddit)

    while True:
        activity = False
        for action in actions:
            activity |= action.perform()
            if terminate:
                print("goodbye")
                sys.exit()
        if not activity:
            now = datetime.now()
            times = [action.ready(now) for action in actions]
            print(times)
            sleep(min(times))

if __name__ == '__main__':
    register_termination()
    entry = LastChecked.objects.get_or_create(name='last_started')
    entry[0].last_checked = datetime.now()
    entry[0].save()

    reddit = praw.Reddit(client_id='ufxVBVi9_Z03Gg',
                         client_secret='_zyrtt2C1oF2020U3dIBVHMb7V0',
                         user_agent='unix:modt:v0.11 (by /u/ssjjawa)')
    while True:
        tb = None
        now = None
        try:
            simple_method(reddit)
        except:
            now = datetime.now()
            tb = format_exc()
            print('Received unhandled internal exception. Logging, sleeping, and resuming.')

        for _ in range(60):
            check_terminate()
            sleep(1)


        Failure.objects.create(traceback=tb, time=now)
