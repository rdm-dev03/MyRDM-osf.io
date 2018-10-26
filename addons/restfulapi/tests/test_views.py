# -*- coding: utf-8 -*-
import json
import pytest
from tests.base import OsfTestCase
from osf_tests.factories import AuthUserFactory, ProjectFactory, NodeFactory
from framework.auth import Auth


class TestRestfulViews(OsfTestCase):
    def setUp(self):
        super(TestRestfulViews, self).setUp()
        self.user = AuthUserFactory()
        self.auth = self.user.auth
        self.project = ProjectFactory(creator=self.user, is_public=True)
        self.node = NodeFactory(creator=self.user, parent=self.project)


    def test_addon_enable(self):
        set_url = self.project.api_url_for('node_choose_addons')
        view_url = self.project.api_url_for('view_project')
        self.app.post_json(set_url, {'restfulapi' : False}, auth=self.user.auth)
        res = self.app.get(view_url)
        jres = json.loads(res.text)
        assert 'restfulapi' not in jres['addons_enabled']
        self.app.post_json(set_url, {'restfulapi' : True}, auth=self.user.auth)
        res = self.app.get(view_url)
        jres = json.loads(res.text)
        assert 'restfulapi' in jres['addons_enabled']


    def test_addon_disable(self):
        set_url = self.project.api_url_for('node_choose_addons')
        view_url = self.project.api_url_for('view_project')
        self.app.post_json(set_url, {'restfulapi' : True}, auth=self.user.auth)
        res = self.app.get(view_url)
        jres = json.loads(res.text)
        assert 'restfulapi' in jres['addons_enabled']
        self.app.post_json(set_url, {'restfulapi' : False}, auth=self.user.auth)
        res = self.app.get(view_url)
        jres = json.loads(res.text)
        assert 'restfulapi' not in jres['addons_enabled']

