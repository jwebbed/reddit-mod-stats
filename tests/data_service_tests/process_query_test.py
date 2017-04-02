from datetime import datetime, timedelta

from django.test import TestCase

from data_service.query import process_query
from rmodstats.api.models import Subreddit, SubredditEvent, SubredditEventDetail
from .fake_objs import *

class ProcessQueryTestCase(TestCase):
    def assertModsCorrect(self, sub, mods):
        modset = set(mods)
        for mod in sub.mods.all():
            self.assertIn(mod.username, modset)
            modset.remove(mod.username)
        self.assertTrue(len(modset) == 0)

    def test_two_queries_no_mod_changes(self):
        reddit_query = FakeRedditQuery('test_sub', 1000, nsfw=False, moderators=['mod1', 'mod2'])

        t1 = datetime.now()
        t2 = t1 + timedelta(hours=1)

        process_query(reddit_query, t1)
        process_query(reddit_query, t2)

        sub = Subreddit.objects.get(name_lower='test_sub')
        events = sub.events.all()

        self.assertTrue(len(events) == 1)

        event = events[0]

        self.assertTrue(event.new == True)
        self.assertTrue(event.previous_check == None)
        self.assertTrue(event.recorded == t1)

        self.assertModsCorrect(sub, ['mod1', 'mod2'])

    def test_two_queries_mod_addition(self):
        reddit_query = FakeRedditQuery('test_sub', 1000, nsfw=False, moderators=['mod1', 'mod2'])

        t1 = datetime.now()
        t2 = t1 + timedelta(hours=1)

        process_query(reddit_query, t1)
        reddit_query.add_mod('mod3')
        process_query(reddit_query, t2)

        sub = Subreddit.objects.get(name_lower='test_sub')
        events = sub.events.all()

        event = events[1]

        self.assertTrue(event.new == False)
        self.assertTrue(event.previous_check == t1)
        self.assertTrue(event.recorded == t2)

        details = event.details.all()

        self.assertTrue(len(details) == 1)

        detail = details[0]

        self.assertTrue(detail.user.username == 'mod3')
        self.assertTrue(detail.addition == True)

        self.assertModsCorrect(sub, ['mod1', 'mod2', 'mod3'])

    def test_two_queries_mod_removal(self):
        reddit_query = FakeRedditQuery('test_sub', 1000, nsfw=False, moderators=['mod1', 'mod2'])

        t1 = datetime.now()
        t2 = t1 + timedelta(hours=1)

        process_query(reddit_query, t1)
        reddit_query.remove_mod('mod1')
        process_query(reddit_query, t2)

        sub = Subreddit.objects.get(name_lower='test_sub')
        events = sub.events.all()

        event = events[1]

        self.assertTrue(event.new == False)
        self.assertTrue(event.previous_check == t1)
        self.assertTrue(event.recorded == t2)

        details = event.details.all()

        self.assertTrue(len(details) == 1)

        detail = details[0]

        self.assertTrue(detail.user.username == 'mod1')
        self.assertTrue(detail.addition == False)

        self.assertModsCorrect(sub, ['mod2'])

    def test_name_lower_valid(self):
        reddit_query = FakeRedditQuery('TEST_SUB', 1000)
        process_query(reddit_query, datetime.now())
        sub = Subreddit.objects.get(name='TEST_SUB')

        self.assertEqual(sub.name_lower, 'test_sub')
