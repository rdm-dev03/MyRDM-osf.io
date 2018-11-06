# -*- coding: utf-8 -*-
import requests

DEFAULT_SPARQL_URL = 'http://ja.dbpedia.org'

RESULTS_FORMAT_MAP = {
    'html': 'text/html',
    'html (basic browsing links)': 'text/x-html+tr',
    'spreadsheet': 'application/vnd.ms-excel',
    'xml': 'application/sparql-results+xml',
    'json': 'application/sparql-results+json',
    'javascript': 'application/javascript',
    'turtle': 'text/turtle',
    'rdf/xml': 'application/rdf+xml',
    'n-triples': 'text/plain',
    'csv': 'text/csv',
    'tsv': 'text/tab-separated-values'
}

FORMAT_EXTENSION = {
    'html': 'html',
    'html (basic browsing links)': 'html',
    'spreadsheet': 'xls',
    'xml': 'xml',
    'json': 'json',
    'javascript': 'js',
    'turtle': 'ttl',
    'rdf/xml': 'rdf',
    'n-triples': 'nt',
    'csv': 'csv',
    'tsv': 'tsv'
}


def serialize_sparql_widget(node):
    node_addon = node.get_addon('sparql')
    sparql_widget_data = {
        'complete': True,
        'more': True,
    }
    sparql_widget_data.update(node_addon.config.to_json())
    return sparql_widget_data


def send_sparql(query, url=DEFAULT_SPARQL_URL, file_format='html'):
    return requests.get(
        'http://ja.dbpedia.org/sparql',
        params={
            'default-graph-uri': url,
            'query': query,
            'format': RESULTS_FORMAT_MAP[file_format]
        }
    )
