# -*- coding: utf-8 -*-
"""
Routes for the ftp addon.
"""

from framework.routing import Rule, json_renderer
from . import views


widget_routes = {
    'rules': [],
    'prefix': '/api/v1'
}

api_routes = {
    'rules': [
        Rule(
            [
                '/project/<pid>/ftp/list/'
            ],
            ['post'],
            views.ftp_list,
            json_renderer
        ),
        Rule(
            [
                '/project/<pid>/ftp/download/'
            ],
            ['post'],
            views.ftp_download,
            json_renderer
        ),
        Rule(
            [
                '/project/<pid>/ftp/cancel/'
            ],
            'post',
            views.ftp_cancel,
            json_renderer
        ),
        Rule(
            [
                '/project/<pid>/ftp/disconnect/'
            ],
            'post',
            views.ftp_disconnect,
            json_renderer
        )
    ],
    'prefix': '/api/v1'
}
