from abc import ABC, abstractmethod
from random import Random
from datetime import datetime, timedelta
from math import log2
from django.db.models import F
import re

from rmodstats.api.models import LastChecked, Subreddit
from data_service.query import query_sub

r = Random()

class Action(ABC):
    @abstractmethod
    def __init__(self, reddit):
        self.reddit = reddit

    @abstractmethod
    def perform(self, now=None):
        '''
        Abstract method that should attempt to perform the implemented action.
        It should also return True iff the action was performed (i.e. a query
        was made), and return False otherwise.
        '''
        pass

    @abstractmethod
    def ready(self, now):
        '''
        Abstract method that should return the number of seconds from input
        datetime, now, until this action is ready to perform.
        '''
        pass

    @abstractmethod
    def action_impl(self, iters=None):
        '''
        Abstract method that should perform the action of the given subclass.
        Should return True iff the action was sucessfully performed and must
        return False otherwise.
        '''
        pass

@abstractmethod
class TimerAction(Action):
    '''
    A timer action is an action that is performed periodically on a timer. It is
    implemented with it's own table where it stores the last time the action
    was performed and will perform said action if the timedelta has expired.

    This is an abstract class and requires a subclass to implement an action
    implementation in order to be used.
    '''
    def __init__(self, reddit, name, delta, strict=False):
        super().__init__(reddit)

        query = LastChecked.objects.get_or_create(name=name)
        self.db_entry = query[0]
        created = LastChecked.objects.get(name='last_started').last_checked
        if query[1] == True:
            self.db_entry.last_checked = datetime.now() - delta
            self.db_entry.save()
        elif query[1] == False and strict == True and self.db_entry.last_checked < created - delta:
            self.db_entry.last_checked = created - delta
            self.db_entry.save()

        self.name = name
        self.delta = delta
        self.strict = strict

    def ready(self, now):
        if self.db_entry.last_checked < now - self.delta:
            return 0
        diff = self.db_entry.last_checked - (now - self.delta)
        return diff.total_seconds()

    def perform(self, now=None):
        '''
        Attempts to perform the implemented action. Returns True if action was
        performed (and a query was made), returns false otherwise.
        '''
        if not now:
            now = datetime.now()

        performed = False
        if self.db_entry.last_checked < now - self.delta:
            if self.strict:
                iters = (now - self.db_entry.last_checked) // self.delta
                iters = iters ** 0.95
                iters = max(int(iters), 1)

                if iters > 1:
                    print("Strict mode on, performing action " + self.name + " " + str(iters) + " times")
                performed = self.action_impl(iters=iters)
            else:
                performed = self.action_impl()
            self.db_entry.last_checked = datetime.now()
            self.db_entry.save()
        return performed

class RecentlyChangedAction(Action):
    '''
    Queries subreddits based on which are most recently changed. The logic
    behind this action is that a subreddit that has recently changed is likely
    to have another subsequent change the mods are changing the mods around.
    The frequency is determined by the following algorithm:

    * Assume `d` is the ammount of time since a sub has last been changed
    * If the sub has not been checked in 2 ** (log2(d)) * 30 seconds, check it

    Because this doesn't set a nescessary frequency for being checked, we cannot
    calculate an absolute frequency with which subs will be checked, just if
    this action is called and there are some subs that can be checked, they will.
    '''
    def __init__(self, reddit):
        super().__init__(reddit)
        self.next_time = datetime.now()

    def perform(self, now=None):
        if not now:
            now = datetime.now()
        if now > self.next_time:
            return self.action_impl()
        return False

    def ready(self, now):
        q = Subreddit.objects.filter(forbidden=False)
        if q.count() == 0:
            return 10000

        #sub = Subreddit.objects.filter(forbidden=False).order_by('-last_changed').values('last_changed', 'last_checked')[0]
        sub = Subreddit.objects.filter(forbidden=False).order_by(F('last_checked') - F('last_changed')).values('last_changed', 'last_checked')[0]
        diff = now - sub['last_changed']
        mins = diff.total_seconds() // 60
        if mins <= 1:
            rank = 0
        else:
            rank = log2(mins)

        if sub['last_checked'] < (now - timedelta(seconds=((2 ** rank) * 30))):
            return 0
        diff = sub['last_checked'] - (now - timedelta(seconds=((2 ** rank) * 30)))
        secs = diff.total_seconds()
        self.next_time = now + timedelta(seconds=secs)
        return secs

    # If a sub has been changed in the last week, there seems a higher probability
    # if will be changed more soon. The closer it has been since it last has been changed
    # the higher the frequency we check it starting at 1m and 10s and increasing
    # exponetially

    def action_impl(self):
        subs = Subreddit.objects.filter(forbidden=False).order_by('-last_changed').values('last_changed', 'last_checked', 'name_lower')
        threshold =  datetime.now() - timedelta(days=7)
        now = datetime.now()
        performed = False
        max_wait = 7 * 24 * 60 * 60
        for sub in subs:
            if sub['last_changed'] < threshold:
                break
            diff = now - sub['last_changed']
            mins = diff.total_seconds() // 60
            if mins <= 1:
                rank = 0
            else:
                rank = log2(mins)
            if sub['last_checked'] < (now - timedelta(seconds=((2 ** rank) * 30))):
                performed = True
                print("Updating " + sub['name_lower'] + " for recently changed")
                query_sub(self.reddit, sub['name_lower'])
            elif performed == False:
                diff = sub['last_checked'] - (now - timedelta(seconds=((2 ** rank) * 30)))
                max_wait = min(diff.total_seconds(), max_wait)

        if performed == False:
            self.next_time = now + timedelta(seconds=max_wait)
        return performed

class SizeAction(Action):
    '''
    Queries subreddits with a frequency that is a function of the subreddits
    size (number of subscribers). The frequency is determined by the following
    algorithm:

    * Break subs into n bins size 2^(i + 8) starting at i = 0
    * Check all the subs in the ith bin every 2^(i - 1) * 45 minutes

    Something to note, all bins are checked at least once every 6 hours, so i
    such that 2^(i - 1) * 45 > 360 (aka 6 hours in minutes) is irrelevent and
    should just be ignored. At present that value is 4.
    '''
    def __init__(self, reddit):
        super().__init__(reddit)
        self.maximum_age = timedelta(hours=6)
        self.next_time = datetime.now()

    def perform(self, now=None):
        if not now:
            now = datetime.now()
        if now > self.next_time:
            return self.action_impl()
        return False

    def ready(self, now):
        if now > self.next_time:
            return 0
        diff = self.next_time - now
        return diff.total_seconds()

    def action_impl(self, iters=None):
        subs = Subreddit.objects.filter(forbidden=False).order_by('-subscribers').values('last_checked', 'name_lower')
        now = datetime.now()
        start = 0
        performed = False
        max_wait = 6 * 60 * 60
        for i in range(5):
            t = now - timedelta(minutes=(2 ** (i - 1)) * 45)
            end = min(2 ** (i + 8), len(subs))
            for sub in subs[start:start + end]:
                if sub['last_checked'] < t:
                    peformed = True
                    print("Updating " + sub['name_lower'] + " for size")
                    query_sub(self.reddit, sub['name_lower'])
                elif performed == False:
                    diff = sub['last_checked'] - t
                    max_wait = min(diff.total_seconds(), max_wait)

            if end == len(subs):
                break
            else:
                start += end

        if performed == False:
            self.next_time = now + timedelta(seconds=max_wait)
        return performed

class LeastFreqAction(Action):
    def __init__(self, reddit):
        super().__init__(reddit)
        self.maximum_age = timedelta(hours=6)
        self.current_oldest = datetime.now() - self.maximum_age

    def _update_current_oldest(self):
        q = Subreddit.objects.filter(forbidden=False).order_by('last_checked')
        if q.count() > 0:
            self.current_oldest = q.only('last_checked')[0].last_checked

    def perform(self, now=None):
        if not now:
            now = datetime.now()
        if self.current_oldest < now - self.maximum_age:
            return self.action_impl()
        return False

    def ready(self, now):
        if self.current_oldest < now - self.maximum_age:
            return 0
        diff = self.current_oldest -  (now - self.maximum_age)
        return diff.total_seconds()

    def action_impl(self, iters=None):
        threshold = datetime.now() - self.maximum_age

        performed = False
        for sub in Subreddit.objects.filter(forbidden=False, last_checked__lt=threshold).order_by('last_checked')[:5].values_list('name_lower', flat=True):
            performed = True
            print("Updating " + sub + " for least recently checked")
            query_sub(self.reddit, sub)

        if performed == False:
            self._update_current_oldest()
        return performed

class RandomAction(TimerAction):
    def __init__(self, reddit):
        super().__init__(reddit, 'random', timedelta(seconds=3), strict=True)

    def action_impl(self, iters=1):
        for _ in range(2 * iters):
            b = False
            if r.random() <= 0.02:
                b = True
            sub = self.reddit.random_subreddit(nsfw=b)
            print("Querying " + sub.display_name + " randomly")
            query_sub(self.reddit, sub.display_name)
        return True

class RAllAction(TimerAction):
    def __init__(self, reddit):
        super().__init__(reddit, 'rall', timedelta(hours=4))

    def action_impl(self, iters=None):
        print("Querying top 100 r/all subs")
        for sub in set([post.subreddit.display_name for post in self.reddit.subreddit('all').hot(limit=100)]):
            print("Querying " + sub)
            query_sub(self.reddit, sub)
        return True

class PopularAction(TimerAction):
    def __init__(self, reddit):
        super().__init__(reddit, 'popular', timedelta(hours=4))

    def action_impl(self, iters=None):
        print("Querying top 100 r/popular subs")
        for sub in set([post.subreddit.display_name for post in self.reddit.subreddit('popular').hot(limit=100)]):
            print("Querying " + sub)
            query_sub(self.reddit, sub)
        return True

class TrendingAction(TimerAction):
    def __init__(self, reddit):
        super().__init__(reddit, 'trending', timedelta(hours=24))

    def action_impl(self, iters=None):
        print("Querying daily trending")
        post = list(self.reddit.subreddit('trendingsubreddits').new(limit=1))[0]
        for sub in set(re.findall('/r/[A-Za-z]+', str(post.selftext))):
            name = sub[3:]
            print("Querying " + name)
            query_sub(self.reddit, name)
        return True

class SubAction(TimerAction):
    def __init__(self, reddit, sub, delta):
        super().__init__(reddit, sub, delta)

    def action_impl(self, iters=None):
        subs = set()
        for post in self.reddit.subreddit(self.name).new(limit=25):
            match = re.search('/r/[A-Za-z]+', str(post.url))
            if match:
                name = match.group(0)[3:]
                subs.add(name)
            if 'selftext' in dir(post) or 'selftext' in vars(post):
                for m in re.findall('/r/[A-Za-z]+', str(post.selftext)):
                    subs.add(m[3:])
        for sub in subs:
            print("Querying " + sub)
            query_sub(self.reddit, sub)
        return True

def get_actions(reddit):
    return (
        RecentlyChangedAction(reddit),
        SizeAction(reddit),
        LeastFreqAction(reddit),
        RandomAction(reddit),
        RAllAction(reddit),
        PopularAction(reddit),
        TrendingAction(reddit),
        SubAction(reddit, 'newreddits', timedelta(hours=6)),
        SubAction(reddit, 'redditrequest', timedelta(hours=6)),
        SubAction(reddit, 'adoptareddit', timedelta(hours=6)),
        SubAction(reddit, 'NOTSONEWREDDITS', timedelta(days=1)),
        SubAction(reddit, 'obscuresubreddits', timedelta(days=1)),
        SubAction(reddit, 'newreddits_nsfw', timedelta(days=1)),
    )
