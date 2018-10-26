# -*- coding: utf-8 -*-
"""
Routes for the restfulapi addon.
"""

from framework.routing import Rule, json_renderer
from . import views


widget_routes = {
    'rules': [
        Rule(
            [
                '/project/<pid>/restfulapi/download/'
            ],
            'post',
            views.restfulapi_download,
            json_renderer
        ),
        Rule(
            [
                '/project/<pid>/restfulapi/cancel/'
            ],
            'post',
            views.restfulapi_cancel,
            json_renderer
        )
    ],
    'prefix': '/api/v1'
}

api_routes = {
    'rules': [],
    'prefix': '/api/v1'
}
