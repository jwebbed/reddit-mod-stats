# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-02 15:50
from __future__ import unicode_literals

from django.db import migrations
from math import floor

def update_graph(event, apps):

    Graph = apps.get_model('api', 'Graph')
    EdgeModRelation = apps.get_model('api', 'EdgeModRelation')
    Edge = apps.get_model('api', 'Edge')

    source_sub = event.sub
    for detail in event.details.all():
        if detail.addition == False:
            #print('Processing event detail which removes ' + detail.user.username + ' from ' + source_sub.name)
            for edge in Edge.objects.filter(source=detail.event.sub):
                for rel in EdgeModRelation.objects.filter(edge=edge, mod=detail.user):
                    #print('Found with source: ' + rel.edge.source.name_lower + ' target: ' + rel.edge.target.name_lower)
                    rel.current_mod_source = False
                    rel.save()

            for edge in Edge.objects.filter(target=detail.event.sub):
                for rel in EdgeModRelation.objects.filter(edge=edge, mod=detail.user):
                    #print('Found with source: ' + rel.edge.source.name_lower + ' target: ' + rel.edge.target.name_lower)
                    rel.current_mod_target = False
                    rel.save()
        elif detail.addition == True:
            #print('Processing event detail which adds ' + detail.user.username + ' to ' + source_sub.name)
            for other_sub in detail.user.subreddit_set.all():
                if other_sub == source_sub:
                    continue
                source_sub.refresh_from_db()
                other_sub.refresh_from_db()
                # Mod is mod of 2 subs, neither in a graph - Make a new graph
                if source_sub.graph == None or other_sub.graph == None:
                    if source_sub.graph == None and other_sub.graph == None:
                        #print('Addition - mod: ' + detail.user.username + ' source_sub: ' + source_sub.name_lower + ' other_sub: ' + other_sub.name_lower + ' - neither sub in graph')
                        g = Graph(valid=True)
                        g.save()

                        source_sub.graph = g
                        source_sub.save()

                        other_sub.graph = g
                        other_sub.save()
                    elif source_sub.graph == None:
                        #print('Addition - mod: ' + detail.user.username + ' source_sub: ' + source_sub.name_lower + ' other_sub: ' + other_sub.name_lower + ' - source_sub not in graph')
                        g = other_sub.graph
                        source_sub.graph = g
                        source_sub.save()
                    elif other_sub.graph == None:
                        #print('Addition - mod: ' + detail.user.username + ' source_sub: ' + source_sub.name_lower + ' other_sub: ' + other_sub.name_lower + ' - other_sub not in graph')
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
                    #print('Addition - mod: ' + detail.user.username + ' source_sub: ' + source_sub.name_lower + ' other_sub: ' + other_sub.name_lower + ' - both subs in same graph')
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
                    #print('Addition - mod: ' + detail.user.username + ' source_sub: ' + source_sub.name_lower + ' other_sub: ' + other_sub.name_lower + ' - both subs in different graph')
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


def replay_events(apps, schema_editor):
    SubredditEvent = apps.get_model('api', 'SubredditEvent')
    events = SubredditEvent.objects.order_by('recorded')
    total = len(events)
    print('\n' + str(total) + ' events')
    prog = 0
    i = 0
    for event in events:
        update_graph(event, apps)
        i += 1
        per = floor((i / total) * 100)
        if per > prog:
            prog = per
            print(str(prog) + '%')


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_auto_20170402_1550'),
    ]

    operations = [
        migrations.RunPython(replay_events)
    ]