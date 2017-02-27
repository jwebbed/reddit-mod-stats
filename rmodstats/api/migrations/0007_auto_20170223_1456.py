# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-23 14:56
from __future__ import unicode_literals

from django.db import migrations

from queue import Queue

def update_graph(apps, schema_editor):
    Subreddit = apps.get_model('api', 'Subreddit')
    #User = apps.get_model('api', 'User')
    SubredditEvent = apps.get_model('api', 'SubredditEvent')
    SubredditEventDetail = apps.get_model('api', 'SubredditEventDetail')
    Graph = apps.get_model('api', 'Graph')
    Edge = apps.get_model('api', 'Edge')

    print('')

    node_edge_map = {}
    for event in SubredditEvent.objects.filter(new=True).all():
        users = []
        for detail in event.details.all():
            name = detail.user.username
            users.append(name)
        node_edge_map[event.sub.name_lower] = set(users)

    print(str(len(node_edge_map)) + ' subs in db')

    dup_node_edge_map = {}
    for key in node_edge_map:
        other_set = set()
        for other_key in node_edge_map:
            if other_key != key:
                other_set |= node_edge_map[other_key]
        dups = node_edge_map[key] & other_set
        if len(dups) > 0:
            dup_node_edge_map[key] = dups
    #print(dup_node_edge_map)

    print(str(len(dup_node_edge_map)) + ' connected subs in db')

    # this next piece of code is the most disgusting code I've ever written
    # in my life
    edge_set = {}
    for node in dup_node_edge_map:
        edge_set[node] = {}
        for mod in dup_node_edge_map[node]:
            for other_node in dup_node_edge_map:
                if node != other_node:
                    for other_mod in dup_node_edge_map[other_node]:
                        if mod == other_mod:
                            if other_node in edge_set[node]:
                                edge_set[node][other_node].append(mod)
                            else:
                                edge_set[node][other_node] = [mod]

    graphs = []
    while len(edge_set) > 0:
        visited_nodes = set()
        node_queue = Queue()
        node_queue.put(list(edge_set.keys())[0])
        edges = []

        while not node_queue.empty():
            node = node_queue.get()
            if node in visited_nodes:
                continue

            visited_nodes.add(node)

            for child in edge_set[node]:
                node_queue.put(child)
                edge = {
                    'source' : node,
                    'target' : child,
                    'mods' : edge_set[node][child]
                }
                edges.append(edge)

        for node in visited_nodes:
            del edge_set[node]

        graphs.append((visited_nodes, edges))

    print(str(len(graphs)) + ' unique graph(s)')

    for graph in graphs:
        g = Graph(valid=True)
        g.save()
        for edge in graph[1]:
            source = Subreddit.objects.get(name_lower=edge['source'])
            target = Subreddit.objects.get(name_lower=edge['target'])
            e = Edge(graph=g, source=source, target=target)
            e.save()
            e.mods.add(*edge['mods'])

        for sub in graph[0]:
            sub_query = Subreddit.objects.get(name_lower=sub)
            sub_query.graph = g
            sub_query.save()

    # process non-new actions
    other_events = SubredditEvent.objects.filter(new=False).order_by('recorded').all()
    print(str(len(other_events)) + ' non-new events')
    print(str(Graph.objects.count()) + ' graphs in db before non-new events')
    for event in other_events:
        source_sub = event.sub
        for detail in event.details.all():
            if detail.addition == True:
                for other_sub in detail.user.subreddit_set.all():
                    if other_sub == source_sub:
                        continue
                    source_sub.refresh_from_db()
                    other_sub.refresh_from_db()
                    # Mod is mod of 2 subs, neither in a graph - Make a new graph
                    if source_sub.graph == None and other_sub.graph == None:
                        print('Addition - mod: ' + detail.user.username + ' source_sub: ' + source_sub.name_lower + ' other_sub: ' + other_sub.name_lower + ' - neither sub in graph')
                        g = Graph(valid=True)
                        g.save()

                        e = Edge(graph=g, source=source_sub, target=other_sub)
                        e.save()
                        e.mods.add(detail.user)

                        e = Edge(graph=g, source=other_sub, target=source_sub)
                        e.save()
                        e.mods.add(detail.user)

                        source_sub.graph = g
                        source_sub.save()

                        other_sub.graph = g
                        other_sub.save()
                    # Mod is mod of 2 subs, source_sub not in graph, other_sub in graph - Add source_sub to other_sub graph
                    elif source_sub.graph == None:
                        print('Addition - mod: ' + detail.user.username + ' source_sub: ' + source_sub.name_lower + ' other_sub: ' + other_sub.name_lower + ' - source_sub not in graph')
                        e = Edge(graph=other_sub.graph, source=source_sub, target=other_sub)
                        e.save()
                        e.mods.add(detail.user)

                        e = Edge(graph=other_sub.graph, source=other_sub, target=source_sub)
                        e.save()
                        e.mods.add(detail.user)

                        source_sub.graph = other_sub.graph
                        source_sub.save()
                    # Mod is mod of other_sub not in graph - Add other sub to graph
                    elif other_sub.graph == None:
                        print('Addition - mod: ' + detail.user.username + ' source_sub: ' + source_sub.name_lower + ' other_sub: ' + other_sub.name_lower + ' - other_sub not in graph')
                        e = Edge(graph=source_sub.graph, source=source_sub, target=other_sub)
                        e.save()
                        e.mods.add(detail.user)

                        e = Edge(graph=source_sub.graph, source=other_sub, target=source_sub)
                        e.save()
                        e.mods.add(detail.user)

                        other_sub.graph = source_sub.graph
                        other_sub.save()
                    # Mod is mod of other sub(s) in graph - add this mod to the mod list of the edges (both directions)
                    elif source_sub.graph == other_sub.graph:
                        print('Addition - mod: ' + detail.user.username + ' source_sub: ' + source_sub.name_lower + ' other_sub: ' + other_sub.name_lower + ' - both subs in same graph')
                        e = Edge.objects.get_or_create(graph=other_sub.graph, source=source_sub, target=other_sub)
                        e[0].mods.add(detail.user)

                        e = Edge.objects.get_or_create(graph=other_sub.graph, source=other_sub, target=source_sub)
                        e[0].mods.add(detail.user)
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
                        e.mods.add(detail.user)

                        e = Edge(graph=base_graph, source=other_sub, target=source_sub)
                        e.save()
                        e.mods.add(detail.user)

                        for sub in merge_graph.subreddit_set.all():
                            sub.graph = base_graph
                            sub.save()

                        for edge in merge_graph.edge_set.all():
                            edge.graph = base_graph
                            edge.save()

                        merge_graph.delete()
    print(str(Graph.objects.count()) + ' graphs in db after non-new events')

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_auto_20170223_1538'),
    ]

    operations = [
        migrations.RunPython(update_graph)
    ]
