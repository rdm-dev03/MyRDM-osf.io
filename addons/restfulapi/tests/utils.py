# -*- coding: utf-8 -*-
import json


class MockResponse:
    def __init__(self, json_data, status_code):
        self.text = None if json_data is None else json.dumps(json_data)
        self.status_code = status_code
