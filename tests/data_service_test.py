from datetime import datetime, timedelta

from django.test import TestCase

from data_service.query import process_query
from rmodstats.api.models import Subreddit, SubredditEvent, SubredditEventDetail

class FakeMod:
    def __init__(self, mod):
        self.name = mod

class FakeRedditQuery:
    def __init__(self, name, subscribers, nsfw=False, moderators=[]):
        self.display_name = name
        self.subscribers = subscribers
        self.over18 = nsfw
        self.moderator = [FakeMod(m) for m in moderators]

    def add_mod(self, name):
        self.moderator.append(FakeMod(name))

class ProcessQueryTestCase(TestCase):
    def setUp(self):
        pass

    def test_two_queries_no_mod_changes(self):
        reddit_query = FakeRedditQuery('test_sub', 1000, nsfw=False, moderators=['mod1', 'mod2'])

        t1 = datetime.now()
        t2 = t1 + timedelta(hours=1)

        process_query(reddit_query, t1)
        process_query(reddit_query, t2)

        sub = Subreddit.objects.get(name='test_sub')
        events = sub.events.all()

        self.assertTrue(len(events) == 1)

        event = events[0]

        self.assertTrue(event.new == True)
        self.assertTrue(event.previous_check == None)
        self.assertTrue(event.recorded == t1)

    def test_two_queries_mod_addition(self):
        reddit_query = FakeRedditQuery('test_sub', 1000, nsfw=False, moderators=['mod1', 'mod2'])

        t1 = datetime.now()
        t2 = t1 + timedelta(hours=1)

        process_query(reddit_query, t1)
        reddit_query.add_mod('mod3')
        process_query(reddit_query, t2)

        sub = Subreddit.objects.get(name='test_sub')
        events = sub.events.all()

        event = events[1]

        self.assertTrue(event.new == False)
        self.assertTrue(event.previous_check == t1)
        self.assertTrue(event.recorded == t2)
