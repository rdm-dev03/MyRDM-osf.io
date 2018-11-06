# -*- coding: utf-8 -*-
import json
import mock
import pytest
from tests.base import OsfTestCase
from osf_tests.factories import AuthUserFactory, ProjectFactory, NodeFactory
from framework.auth import Auth


class TestSparqlViews(OsfTestCase):
    def setUp(self):
        super(TestSparqlViews, self).setUp()
        self.user = AuthUserFactory()
        self.auth = self.user.auth
        self.project = ProjectFactory(creator=self.user, is_public=True)
        self.node = NodeFactory(creator=self.user, parent=self.project)


    def test_addon_enable(self):
        set_url = self.project.api_url_for('node_choose_addons')
        view_url = self.project.api_url_for('view_project')
        self.app.post_json(set_url, {'sparql' : False}, auth=self.user.auth)
        res = self.app.get(view_url)
        jres = json.loads(res.text)
        assert 'sparql' not in jres['addons_enabled']
        self.app.post_json(set_url, {'sparql' : True}, auth=self.user.auth)
        res = self.app.get(view_url)
        jres = json.loads(res.text)
        assert 'sparql' in jres['addons_enabled']


    def test_addon_disable(self):
        set_url = self.project.api_url_for('node_choose_addons')
        view_url = self.project.api_url_for('view_project')
        self.app.post_json(set_url, {'sparql' : True}, auth=self.user.auth)
        res = self.app.get(view_url)
        jres = json.loads(res.text)
        assert 'sparql' in jres['addons_enabled']
        self.app.post_json(set_url, {'sparql' : False}, auth=self.user.auth)
        res = self.app.get(view_url)
        jres = json.loads(res.text)
        assert 'sparql' not in jres['addons_enabled']


    def test_run_query_missing_query(self):
        url = self.project.api_url_for('run_query')
        res = self.app.post_json(url, {
            'url': 'http://ja.dbpedia.org',
            'format': 'html',
            'limit': '100'
        }, auth=self.user.auth)
        assert '"status_code": 400' in res.text
        assert '"text": "Missing fields"' in  res.text


    def test_run_query_missing_url(self):
        url = self.project.api_url_for('run_query')
        res = self.app.post_json(url, {
            'query' : 'select distinct * where { <http://ja.dbpedia.org/resource/東京都> ?p ?o .  }',
            'format': 'html',
            'limit': '100'
        }, auth=self.user.auth)
        assert '"status_code": 400' in res.text
        assert '"text": "Missing fields"' in  res.text


    def test_run_query_missing_format(self):
        url = self.project.api_url_for('run_query')
        res = self.app.post_json(url, {
            'query' : 'select distinct * where { <http://ja.dbpedia.org/resource/東京都> ?p ?o .  }',
            'url': 'http://ja.dbpedia.org',
            'limit': '100'
        }, auth=self.user.auth)
        assert '"status_code": 400' in res.text
        assert '"text": "Missing fields"' in  res.text


    def test_run_query_missing_limit(self):
        url = self.project.api_url_for('run_query')
        res = self.app.post_json(url, {
            'query' : 'select distinct * where { <http://ja.dbpedia.org/resource/東京都> ?p ?o .  }',
            'url': 'http://ja.dbpedia.org',
            'format': 'html'
        }, auth=self.user.auth)
        assert '"status_code": 400' in res.text
        assert '"text": "Missing fields"' in  res.text


    def test_run_query_invalid_format(self):
        url = self.project.api_url_for('run_query')
        res = self.app.post_json(url, {
            'query' : 'select distinct * where { <http://ja.dbpedia.org/resource/東京都> ?p ?o .  }',
            'url': 'http://ja.dbpedia.org',
            'format': 'unsupported_format',
            'limit': '100'
        }, auth=self.user.auth)
        assert '"status_code": 400' in res.text
        assert '"text": "Invalid file format"' in  res.text


    def test_run_query_html(self):
        url = self.project.api_url_for('run_query')
        res = self.app.post_json(url, {
            'query' : 'select distinct * where { <http://ja.dbpedia.org/resource/東京都> ?p ?o .  }',
            'url': 'http://ja.dbpedia.org',
            'format': 'html',
            'limit': '100'
        }, auth=self.user.auth)
        assert '"status_code": 200' in res.text
        assert '<table class=\\"sparql\\"' in res.text


    def test_use_form_limit_first(self):
        url = self.project.api_url_for('run_query')
        res = self.app.post_json(url, {
            'query' : 'select distinct * where { <http://ja.dbpedia.org/resource/東京都> ?p ?o .  }  LIMIT 100',
            'url': 'http://ja.dbpedia.org',
            'format': 'html',
            'limit': '1'
        }, auth=self.user.auth)
        assert '"status_code": 200' in res.text
        assert res.text.count('<tr>') == 2
        res = self.app.post_json(url, {
            'query' : 'select distinct * where { <http://ja.dbpedia.org/resource/東京都> ?p ?o .  } LIMIT 1',
            'url': 'http://ja.dbpedia.org',
            'format': 'html',
            'limit': '3'
        }, auth=self.user.auth)
        assert '"status_code": 200' in res.text
        assert res.text.count('<tr>') == 4


    @mock.patch('addons.sparql.views._save_result')
    def test_run_query_non_html(self, save_result_mock):
        url = self.project.api_url_for('run_query')
        res = self.app.post_json(url, {
            'query' : 'select distinct * where { <http://ja.dbpedia.org/resource/東京都> ?p ?o .  }',
            'url': 'http://ja.dbpedia.org',
            'format': 'xml',
            'limit': '100'
        }, auth=self.user.auth)
        save_result_mock.delay.assert_called()
        assert '"status_code": 200' in res.text

