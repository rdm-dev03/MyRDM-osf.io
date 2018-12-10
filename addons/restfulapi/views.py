# -*- coding: utf-8 -*-

import requests
import time
import os
import shutil
import subprocess
from celery.result import AsyncResult
from celery.exceptions import SoftTimeLimitExceeded
from framework.celery_tasks import app as celery_app
from framework.sessions import session
from framework.auth import Auth
from osf.models import AbstractNode, OSFUser
from flask import request
from website.util import waterbutler
from website.project.decorators import (
    must_be_contributor_or_public,
    must_have_addon,
    must_be_valid_project,
    must_not_be_retracted_registration,
)


@must_be_valid_project
@must_be_contributor_or_public
@must_have_addon('restfulapi', 'node')
@must_not_be_retracted_registration
def restfulapi_download(auth, **kwargs):
    node = kwargs.get('node')
    pid = kwargs.get('pid')
    uid = auth.user._id
    request_info = {
        'node_id': node._id,
        'pid': pid,
        'uid': uid
    }
    data = request.get_json()

    prevalidation_result = prevalidate_data(data)
    if not prevalidation_result['valid']:
        return {
            'status': 'Failed',
            'message': prevalidation_result['message']
        }

    # Clean up input
    data['url'] = data['url'].strip().split(' ')[0]
    postvalidation_result = postvalidate_data(data)
    if not postvalidation_result['valid']:
        return {
            'status': 'Failed',
            'message': postvalidation_result['message']
        }

    if u'restfulapi' not in session.data:
        session.data[u'restfulapi'] = {}
    if u'task_list' not in session.data[u'restfulapi']:
        session.data[u'restfulapi'][u'task_list'] = []

    # Clear finished tasks
    for task_id in session.data[u'restfulapi'][u'task_list']:
        task = AsyncResult(task_id)
        if task.ready():
            session.data[u'restfulapi'][u'task_list'].remove(task_id)

    task = main_task.delay(request.cookies.get('osf'), data, request_info)
    session.data[u'restfulapi'][u'task_list'].append(task.task_id)
    session.save()

    # Recent activity log
    node.add_log(
        action='restfulapi_submit',
        params={
            'node': pid,
            'project': pid
        },
        auth=auth
    )

    return {
        'status': 'OK',
    }

@must_be_valid_project
@must_be_contributor_or_public
@must_have_addon('restfulapi', 'node')
@must_not_be_retracted_registration
def restfulapi_cancel(auth, **kwargs):
    if u'restfulapi' not in session.data:
        session.data[u'restfulapi'] = {}
    if u'task_list' not in session.data[u'restfulapi']:
        session.data[u'restfulapi'][u'task_list'] = []

    cancel_count = 0
    for task_id in session.data[u'restfulapi'][u'task_list']:
        task = AsyncResult(task_id)
        if not task.ready():
            # Raise SoftTimeLimitExceeded exception on the task
            task.revoke(terminate=True, signal='SIGUSR1')
            cancel_count += 1

    session.data[u'restfulapi'][u'task_list'] = []
    session.save()

    if cancel_count == 0:
        return {
            'status': 'No download tasks',
            'message': 'There are no active download tasks.'
        }

    # Recent activity log
    node = kwargs.get('node')
    pid = kwargs.get('pid')
    node.add_log(
        action='restfulapi_cancel',
        params={
            'node': pid,
            'project': pid
        },
        auth=auth
    )

    return {
        'status': 'OK',
        'message': 'Download task has been cancelled.'
    }

def prevalidate_data(data):
    '''
    Check if the required fields are filled.
    '''
    if not data['url']:
        return {
            'valid': False,
            'message': 'Please specify an URL.'
        }
    if not data['pid']:
        return {
            'valid': False,
            'message': 'Please specify the destination to save the file(s).'
        }
    return {
        'valid': True,
    }

def postvalidate_data(data):
    '''
    Check if URL responds to requests.
    '''
    response = None
    try:
        response = requests.head(data['url'], allow_redirects=True)
    except Exception:
        return {
            'valid': False,
            'message': 'An error ocurred while accessing the URL.'
        }
    # Sometimes there are false negatives (status code 500)
    # Likely such requests are not implemented on servers
    if response.status_code >= 400 and response.status_code != 500:
        return {
            'valid': False,
            'message': 'URL returned an invalid response.'
        }
    return {
        'valid': True,
    }

@celery_app.task
def main_task(osf_cookie, data, request_info):
    '''
    Creates a temporary folder to download the files from the inputted URL,
    downloads from it, uploads to the selected storage and deletes the temporary
    files.
    '''
    try:
        tmp_path = create_tmp_folder(request_info['uid'])
        if not tmp_path:
            raise OSError('Could not create temporary folder.')

        download_process = get_files(tmp_path, data)
        download_process.communicate()  # Wait for the process to finish
        if download_process.poll() != 0:  # Checks the return_code
            raise RuntimeError('wget command returned a non-success code.')

        dest_path = 'osfstorage/' if 'folderId' not in data else data['folderId']
        uploaded = waterbutler.upload_folder_recursive(osf_cookie, data['pid'], tmp_path, dest_path)
        shutil.rmtree(tmp_path)

        # Variables for logging into recent activity
        node = AbstractNode.load(request_info['node_id'])
        user = OSFUser.load(request_info['uid'])
        auth = Auth(user=user)

        if uploaded['fail_file'] > 0 or uploaded['fail_folder'] > 0:
            # Recent activity log
            node.add_log(
                action='restfulapi_upload_fail',
                params={
                    'node': request_info['node_id'],
                    'project': request_info['pid'],
                    'filecount': uploaded['fail_file'],
                    'foldercount': uploaded['fail_folder']
                },
                auth=auth
            )

            # Exception
            fails = []
            if uploaded['fail_file'] > 0:
                fails.append('%s file(s)' % uploaded['fail_file'])
            if uploaded['fail_folder'] > 0:
                fails.append('%s folder(s)' % uploaded['fail_folder'])
            message = 'Failed to upload %s to storage.' % (
                ' and '.join(fails)
            )
            raise RuntimeError(message)

        node.add_log(
            action='restfulapi_upload_success',
            params={
                'node': request_info['node_id'],
                'project': request_info['pid'],
            },
            auth=auth
        )
    except SoftTimeLimitExceeded:
        download_process = download_process if 'download_process' in locals() else None
        tmp_path = tmp_path if 'tmp_path' in locals() else None
        fail_cleanup(download_process, tmp_path)
    except Exception:
        download_process = download_process if 'download_process' in locals() else None
        tmp_path = tmp_path if 'tmp_path' in locals() else None
        fail_cleanup(download_process, tmp_path)
        raise

    return True

def fail_cleanup(download_process, tmp_path):
    # If download haven't finished, cancel it
    if download_process and download_process.poll() is None:
        download_process.kill()
    # Remove temporary files
    if tmp_path and os.path.isdir(tmp_path):
        shutil.rmtree(tmp_path)

def create_tmp_folder(uid):
    '''
    Creates a temporary folder to download the files into.
    '''
    full_path = None
    try:
        if not os.path.isdir('tmp'):
            os.mkdir('tmp')
        if not os.path.isdir('tmp/restfulapi'):
            os.mkdir('tmp/restfulapi')
        count = 1
        folder_name = '%s_%s' % (uid, int(time.time()))
        while os.path.isdir('tmp/restfulapi/' + folder_name):
            count += 1
            folder_name = '%s_%s_%s' % (uid, int(time.time()), count)
        full_path = 'tmp/restfulapi/' + folder_name
        os.mkdir(full_path)
    except OSError:
        full_path = None
    return full_path

def get_files(tmp_path, data):
    '''
    Download the files from the RESTfulAPI URL provided by the user.
    '''
    command = ['wget', '-P', tmp_path]
    if data['recursive']:
        command.append('-r')
    if data['interval']:
        command += ['-w', data['intervalValue']]
    command.append(data['url'])
    return subprocess.Popen(command)
