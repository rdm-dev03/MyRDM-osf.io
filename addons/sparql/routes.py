# -*- coding: utf-8 -*-
"""
Routes for the sparql addon.
"""

from framework.routing import Rule, json_renderer
from . import views


api_routes = {
    'rules': [
        Rule(
            [
                '/project/<pid>/sparql/'
            ],
            ['post'],
            views.run_query,
            json_renderer
        )
    ],
    'prefix': '/api/v1'
}

widget_routes = {
    'rules': [
        Rule(
            [
                '/project/<pid>/sparql/widget'
            ],
            'post',
            views.sparql_widget,
            json_renderer
        )
    ],
    'prefix': '/api/v1'
}
