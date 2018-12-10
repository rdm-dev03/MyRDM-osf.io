# -*- coding: utf-8 -*-
import sys
import datetime
import requests
import logging
from framework.celery_tasks import app as celery_app
from framework.auth import Auth
from osf.models import AbstractNode, OSFUser
from flask import request
from api.base.utils import waterbutler_api_url_for
from website.project.decorators import (
    must_be_contributor_or_public,
    must_have_addon,
    must_be_valid_project,
    must_not_be_retracted_registration,
)
import utils


logger = logging.getLogger()


@must_be_valid_project
@must_be_contributor_or_public
@must_have_addon('sparql', 'node')
@must_not_be_retracted_registration
def sparql_widget(auth, **kwargs):
    return {
        'status': 'OK',
    }


@must_be_valid_project
@must_be_contributor_or_public
@must_have_addon('sparql', 'node')
@must_not_be_retracted_registration
def run_query(auth, **kwargs):
    node = kwargs.get('node')
    pid = kwargs.get('pid')
    uid = auth.user._id
    request_info = {
        'node_id': node._id,
        'pid': pid,
        'uid': uid
    }
    osf_cookie = request.cookies.get('osf')
    data = request.get_json()

    # Check input
    if 'query' not in data or 'url' not in data or 'format' not in data or 'limit' not in data:
        return {
            'status_code': 400,
            'text': 'Missing fields'
        }
    if data['format'] not in utils.RESULTS_FORMAT_MAP:
        return {
            'status_code': 400,
            'text': 'Invalid file format'
        }

    # Remove limit added manually to the query
    data['query'] = data['query'].split(' ')
    lowercase_query = [item.lower() for item in data['query']]
    if 'limit' in lowercase_query:
        limit_index = lowercase_query.index('limit')
        data['query'].pop(limit_index)
        if len(data['query']) > limit_index:
            data['query'].pop(limit_index)

    # Add limit from the dropdown to the query
    if data['limit']:
        data['query'].append('LIMIT')
        data['query'].append(data['limit'])

    data['query'] = ' '.join(data['query'])

    # Process query
    res = utils.send_sparql(data['query'], data['url'], data['format'])

    response = {'status_code': res.status_code}
    if res.status_code == 200:
        if data['format'] == 'html':
            response['text'] = res.text
        else:
            _save_result.delay(res.text, data['format'], request_info, osf_cookie)

        # Recent activity log
        node.add_log(
            action='sparql_runquery',
            params={
                'node': node._id,
                'project': pid
            },
            auth=auth
        )

    return response


@celery_app.task
def _save_result(query_result, file_format, request_info, osf_cookie):
    # Prevent errors when query_result has japanese characters
    reload(sys)
    sys.setdefaultencoding('utf-8')

    now = datetime.datetime.now()
    file_name = 'sparql_%s.%s' % (
        now.strftime('%Y-%m-%d_%H-%M-%S'),
        utils.FORMAT_EXTENSION[file_format]
    )

    # Variables for logging into recent activity
    node = AbstractNode.load(request_info['node_id'])
    user = OSFUser.load(request_info['uid'])
    auth = Auth(user=user)

    try:
        response = requests.put(
            waterbutler_api_url_for(
                request_info['pid'], 'osfstorage', name=file_name, kind='file', _internal=True
            ),
            data=query_result,
            cookies={
                'osf': osf_cookie
            }
        )
    except requests.ConnectionError:
        node.add_log(
            action='sparql_upload_fail',
            params={
                'node': request_info['node_id'],
                'project': request_info['pid']
            },
            auth=auth
        )
        raise

    action = None
    if response.status_code == requests.codes.created:
        action = 'sparql_upload_success'
    else:
        action = 'sparql_upload_fail'

    node.add_log(
        action=action,
        params={
            'node': request_info['node_id'],
            'project': request_info['pid']
        },
        auth=auth
    )
    return response
