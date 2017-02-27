from datetime import datetime

import praw
import prawcore

from rmodstats.api.models import User, Subreddit, SubredditEvent, SubredditEventDetail, ModRelation, Graph, Edge, EdgeModRelation
from data_service.termination import check_terminate

def update_graph(event):
    source_sub = event.sub
    for detail in event.details.all():
        if detail.addition == False:
            #print("Remove " + detail.user.username + ' from ' + detail.event.sub.name_lower)
            for edge in Edge.objects.filter(source=detail.event.sub):
                for rel in EdgeModRelation.objects.filter(edge=edge, mod=detail.user):
                    print('Found with source: ' + rel.edge.source.name_lower + ' target: ' + rel.edge.target.name_lower)
                    rel.current_mod_source = False
                    rel.save()

            for edge in Edge.objects.filter(target=detail.event.sub):
                for rel in EdgeModRelation.objects.filter(edge=edge, mod=detail.user):
                    print('Found with source: ' + rel.edge.source.name_lower + ' target: ' + rel.edge.target.name_lower)
                    rel.current_mod_target = False
                    rel.save()
        elif detail.addition == True:
            for other_sub in detail.user.subreddit_set.all():
                if other_sub == source_sub:
                    continue
                source_sub.refresh_from_db()
                other_sub.refresh_from_db()
                # Mod is mod of 2 subs, neither in a graph - Make a new graph
                if source_sub.graph == None or other_sub.graph == None:
                    if source_sub.graph == None and other_sub.graph == None:
                        print('Addition - mod: ' + detail.user.username + ' source_sub: ' + source_sub.name_lower + ' other_sub: ' + other_sub.name_lower + ' - neither sub in graph')
                        g = Graph(valid=True)
                        g.save()

                        source_sub.graph = g
                        source_sub.save()

                        other_sub.graph = g
                        other_sub.save()
                    elif source_sub.graph == None:
                        print('Addition - mod: ' + detail.user.username + ' source_sub: ' + source_sub.name_lower + ' other_sub: ' + other_sub.name_lower + ' - source_sub not in graph')
                        g = other_sub.graph
                        source_sub.graph = g
                        source_sub.save()
                    elif other_sub.graph == None:
                        print('Addition - mod: ' + detail.user.username + ' source_sub: ' + source_sub.name_lower + ' other_sub: ' + other_sub.name_lower + ' - other_sub not in graph')
                        g = source_sub.graph
                        other_sub.graph = g
                        other_sub.save()


                    e = Edge(graph=g, source=source_sub, target=other_sub)
                    e.save()
                    emr = EdgeModRelation(edge=e, mod=detail.user)
                    emr.save()

                    e = Edge(graph=g, source=other_sub, target=source_sub)
                    e.save()
                    emr = EdgeModRelation(edge=e, mod=detail.user)
                    emr.save()
                # Mod is mod of other sub(s) in graph - add this mod to the mod list of the edges (both directions)
                elif source_sub.graph == other_sub.graph:
                    print('Addition - mod: ' + detail.user.username + ' source_sub: ' + source_sub.name_lower + ' other_sub: ' + other_sub.name_lower + ' - both subs in same graph')
                    e = Edge.objects.get_or_create(graph=other_sub.graph, source=source_sub, target=other_sub)
                    emr = EdgeModRelation.objects.get_or_create(edge=e[0], mod=detail.user)
                    if emr[1] == False:
                        emr[0].current_mod_source = True
                        emr[0].save()

                    e = Edge.objects.get_or_create(graph=other_sub.graph, source=other_sub, target=source_sub)
                    emr = EdgeModRelation.objects.get_or_create(edge=e[0], mod=detail.user)
                    if emr[1] == False:
                        emr[0].current_mod_target = True
                        emr[0].save()
                # Mod is mod of other sub(s) outside graph - Merge these 2 graphs
                elif source_sub.graph != other_sub.graph:
                    print('Addition - mod: ' + detail.user.username + ' source_sub: ' + source_sub.name_lower + ' other_sub: ' + other_sub.name_lower + ' - both subs in different graph')
                    g1 = source_sub.graph
                    g2 = other_sub.graph
                    if g1.subreddit_set.count() >= g2.subreddit_set.count():
                        base_graph = g1
                        merge_graph = g2
                    else:
                        base_graph = g2
                        merge_graph = g1

                    e = Edge(graph=base_graph, source=source_sub, target=other_sub)
                    e.save()
                    emr = EdgeModRelation(edge=e, mod=detail.user)
                    emr.save()

                    e = Edge(graph=base_graph, source=other_sub, target=source_sub)
                    e.save()
                    emr = EdgeModRelation(edge=e, mod=detail.user)
                    emr.save()

                    for sub in merge_graph.subreddit_set.all():
                        sub.graph = base_graph
                        sub.save()

                    for edge in merge_graph.edge_set.all():
                        edge.graph = base_graph
                        edge.save()

                    merge_graph.delete()


def query_sub(r, sub):
    global terminate
    now = datetime.now()
    sub_obj = r.subreddit(sub)
    sub_model = Subreddit.objects.get_or_create(name_lower=sub.lower(), defaults={'forbidden' : False})
    try:
        sub_model[0].subscribers = sub_obj.subscribers
        sub_model[0].name = sub_obj.display_name
        sub_model[0].nsfw = sub_obj.over18
        sub_model[0].save()
    except prawcore.exceptions.PrawcoreException as e:
        print(e)
        sub_model[0].forbidden = True
        sub_model[0].save()
        return


    if (sub_model[1] == True):
        print("Added new sub " + sub)

    curr_mods = set(sub_model[0].mods.values_list('username', flat=True))
    new_mods = set([m.name for m in sub_obj.moderator]) - set(('AutoModerator',))

    additions = new_mods - curr_mods
    removals = curr_mods - new_mods

    if len(additions) > 0 or len(removals) > 0:
        print('Mods of ' + sub + ' have changed')

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
        update_graph(event)

    sub_model[0].last_checked = now
    sub_model[0].save()

    check_terminate()
