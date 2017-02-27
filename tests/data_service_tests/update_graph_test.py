from datetime import datetime, timedelta

from django.test import TestCase

from data_service.query import process_query, update_graph
from rmodstats.api.models import *
from .fake_objs import *

class UpdateGraphTestCase(TestCase):
    def setUp(self):
        '''
            Initalize graph as follows
            node1:  node2:  node3:
              mod1    mod1    mod2
              mod2

            node4:  node5:
              mod3    mod3

            node6
              mod4:
        '''
        reddit_query = FakeRedditQuery('node1', 1000, nsfw=False, moderators=['mod1', 'mod2'])
        t1 = datetime.now()
        process_query(reddit_query, t1)

        reddit_query = FakeRedditQuery('node2', 1000, nsfw=False, moderators=['mod1'])
        t2 = t1 + timedelta(minutes=1)
        process_query(reddit_query, t2)

        reddit_query = FakeRedditQuery('node3', 1000, nsfw=False, moderators=['mod2'])
        t3 = t2 + timedelta(minutes=1)
        process_query(reddit_query, t3)

        reddit_query = FakeRedditQuery('node4', 1000, nsfw=False, moderators=['mod3'])
        t4 = t3 + timedelta(minutes=1)
        process_query(reddit_query, t4)

        reddit_query = FakeRedditQuery('node5', 1000, nsfw=False, moderators=['mod3'])
        t5 = t4 + timedelta(minutes=1)
        process_query(reddit_query, t5)

        reddit_query = FakeRedditQuery('node6', 1000, nsfw=False, moderators=['mod4'])
        t6 = t5 + timedelta(minutes=1)
        process_query(reddit_query, t6)

    def assertEdgeRels(self, edge, current_mods=[], former_mods=[]):
        for mod in current_mods:
            rel = EdgeModRelation.objects.get_or_create(edge=edge, mod=mod)
            self.assertTrue(not rel[1])
            self.assertTrue(rel[0].current_mod_source)

        for mod in former_mods:
            rel = EdgeModRelation.objects.get_or_create(edge=edge, mod=mod)
            self.assertTrue(not rel[1])
            self.assertTrue(not rel[0].current_mod_source)

    def test_no_graph(self):
        # node6 should have no graph
        node = Subreddit.objects.get(name='node6')
        self.assertIsNone(node.graph)

    def test_two_node_graph(self):
        # node4 and node5 should have graphs and be the same graph
        sub_node_4 = Subreddit.objects.get(name='node4')
        sub_node_5 = Subreddit.objects.get(name='node5')

        self.assertIsNotNone(sub_node_4.graph)
        self.assertIsNotNone(sub_node_5.graph)
        self.assertEqual(sub_node_4.graph, sub_node_5.graph)

        g = sub_node_4.graph
        self.assertTrue(g.valid)

        edges = g.edge_set.all()
        self.assertTrue(len(edges) == 2)
        if edges[0].source == sub_node_4:
            edge_source_4 = edges[0]
            edge_source_5 = edges[1]
        else:
            edge_source_4 = edges[1]
            edge_source_5 = edges[0]

        self.assertTrue(edge_source_4.source == sub_node_4)
        self.assertTrue(edge_source_5.source == sub_node_5)
        self.assertTrue(edge_source_4.target == sub_node_5)
        self.assertTrue(edge_source_5.target == sub_node_4)

        self.assertEdgeRels(edge_source_4, current_mods=['mod3'])
        self.assertEdgeRels(edge_source_5, current_mods=['mod3'])
