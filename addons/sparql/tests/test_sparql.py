# -*- coding: utf-8 -*-
import pytest
from tests.base import OsfTestCase
from osf_tests.factories import AuthUserFactory, ProjectFactory, NodeFactory
from framework.auth import Auth
from addons.sparql import utils

class TestSparqlApi(OsfTestCase):
    def setUp(self):
        super(TestSparqlApi, self).setUp()
        self.user = AuthUserFactory()
        self.auth = self.user.auth
        self.project = ProjectFactory(creator=self.user, is_public=True)
        self.node = NodeFactory(creator=self.user, parent=self.project)


    def test_query_html_format(self):
        query = 'select distinct * where { <http://ja.dbpedia.org/resource/国立情報学研究所> ?p ?o .  }'
        res = utils.send_sparql(query, file_format='html')
        assert res.status_code == 200
        assert '<table class="sparql"' in res.content
        assert 'こくりつじょうほうがくけんきゅうじょ' in res.content


    def test_query_non_html_format(self):
        query = 'select distinct * where { <http://ja.dbpedia.org/resource/東京都> ?p ?o .  }'
        res = utils.send_sparql(query, file_format='xml')
        assert res.status_code == 200
        assert '<sparql xmlns=' in res.content
        assert 'とうきょうと' in res.content

