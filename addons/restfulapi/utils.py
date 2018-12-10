# -*- coding: utf-8 -*-
def serialize_restfulapi_widget(node):
    node_addon = node.get_addon('restfulapi')
    restfulapi_widget_data = {
        'complete': True,
        'more': True,
    }
    restfulapi_widget_data.update(node_addon.config.to_json())
    return restfulapi_widget_data
