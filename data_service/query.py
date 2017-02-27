from datetime import datetime

import praw
import prawcore

from rmodstats.api.models import User, Subreddit, SubredditEvent, SubredditEventDetail, ModRelation
from data_service.termination import check_terminate

def query_sub(r, sub):
    global terminate
    now = datetime.now()
    sub_obj = r.subreddit(sub)
    try:
        sub_obj.display_name
    except prawcore.exceptions.PrawcoreException as e:
        print(e)
        sub_model = Subreddit.objects.get_or_create(name_lower=sub.lower())
        sub_model[0].forbidden = True
        sub_model[0].save()
        return

    process_query(sub_obj, now)
    check_terminate()

def process_query(query, now):
    sub_model = Subreddit.objects.get_or_create(name_lower=query.display_name.lower(), defaults={'forbidden' : False})
    sub_model[0].subscribers = query.subscribers
    sub_model[0].name = query.display_name
    sub_model[0].nsfw = query.over18
    sub_model[0].save()

    if (sub_model[1] == True):
        print("Added new sub " + query.display_name)

    curr_mods = set(sub_model[0].mods.values_list('username', flat=True))
    new_mods = set([m.name for m in query.moderator]) - set(('AutoModerator',))

    additions = new_mods - curr_mods
    removals = curr_mods - new_mods

    if len(additions) > 0 or len(removals) > 0:
        print('Mods of ' + query.display_name + ' have changed')

        event = SubredditEvent(sub=sub_model[0], recorded=now, new=sub_model[1])
        if sub_model[1] == False:
            event.previous_check = sub_model[0].last_checked
        event.save()

        relations = []
        if len(additions) > 0:
            print('Added: ' + str(additions))
            for mod in additions:
                user_query = User.objects.get_or_create(username=mod)
                relations.append(SubredditEventDetail(event=event, user=user_query[0], addition=True))

                modrel = ModRelation(sub=sub_model[0], mod=user_query[0])
                modrel.save()


        if len(removals) > 0:
            assert(sub_model[1] == False)
            print('Removed: ' + str(removals))
            for mod in removals:
                user_query = User.objects.get(username=mod)
                relations.append(SubredditEventDetail(event=event, user=user_query, addition=False))

                ModRelation.objects.get(sub=sub_model[0], mod=user_query).delete()

        SubredditEventDetail.objects.bulk_create(relations)
        sub_model[0].last_changed = now

    sub_model[0].last_checked = now
    sub_model[0].save()
