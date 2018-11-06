# -*- coding: utf-8 -*-

import time
import os
import shutil
import utils
import ftplib
import paramiko
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
@must_have_addon('ftp', 'node')
@must_not_be_retracted_registration
def ftp_widget(auth, wname, path=None, **kwargs):
    ret = {
        'hello': 'world',
    }
    return ret


LIST_FUNCTIONS = {
    'sftp': utils.sftp_list,
    'ftp': utils.ftp_list,
    'ftps': utils.ftp_list
}

DOWNLOAD_FUNCTIONS = {
    'sftp': utils.sftp_download,
    'ftp': utils.ftp_download,
    'ftps': utils.ftp_download
}


@must_be_valid_project
@must_be_contributor_or_public
@must_have_addon('ftp', 'node')
@must_not_be_retracted_registration
def ftp_list(**kwargs):
    data = request.get_json()
    args = {
        'host': '',
        'port': '22' if data['protocol'] == 'sftp' else '21',
        'username': '',
        'password': '',
        'key': None,
        'path': '/'
    }

    args.update(data)
    try:
        file_list = LIST_FUNCTIONS[data['protocol']](**args)
    except paramiko.ssh_exception.SSHException:
        return {'status': 'Connection Error.'}
    except paramiko.ssh_exception.AuthenticationException:
        return {'status': 'Authentication failed.'}
    except IOError:
        return {'status': 'Path is not a directory.'}
    except ftplib.all_errors as ex:
        return {'status': str(ex)}

    # Recent activity log
    if 'info' in data and data['info'] == 'connect':
        node = kwargs['node']
        pid = kwargs.get('pid')
        auth = kwargs.get('auth')
        node.add_log(
            action='ftp_connect',
            params={
                'node': pid,
                'project': pid
            },
            auth=auth
        )

    return {
        'status': 'OK',
        'file_list': file_list
    }


@must_be_valid_project
@must_be_contributor_or_public
@must_have_addon('ftp', 'node')
@must_not_be_retracted_registration
def ftp_download(auth, **kwargs):
    node = kwargs.get('node')
    pid = kwargs.get('pid')
    uid = auth.user._id
    request_info = {
        'node_id': node._id,
        'pid': pid,
        'uid': uid
    }
    data = request.get_json()

    validation_result = validate_data(data)
    if not validation_result['valid']:
        return {
            'status': 'Failed',
            'message': validation_result['message']
        }

    if data['passMethod'] == 'plaintext':
        data['key'] = None

    args = {
        'host': '',
        'port': '22' if data['protocol'] == 'sftp' else '21',
        'username': '',
        'password': '',
        'key': None,
        'path': '/'
    }
    args.update(data)

    if u'ftp' not in session.data:
        session.data[u'ftp'] = {}
    if u'task_list' not in session.data[u'ftp']:
        session.data[u'ftp'][u'task_list'] = []

    # Clear finished tasks
    for task_id in session.data[u'ftp'][u'task_list']:
        task = AsyncResult(task_id)
        if task.ready():
            session.data[u'ftp'][u'task_list'].remove(task_id)

    task = main_task.delay(request.cookies.get('osf'), args, request_info)
    session.data[u'ftp'][u'task_list'].append(task.task_id)
    session.save()

    # Recent activity log
    node.add_log(
        action='ftp_download',
        params={
            'node': pid,
            'project': pid
        },
        auth=auth
    )

    return {
        'status': 'OK',
        'message': 'Selected files are being downloaded to storage.'
    }

@must_be_valid_project
@must_be_contributor_or_public
@must_have_addon('ftp', 'node')
@must_not_be_retracted_registration
def ftp_cancel(auth, **kwargs):
    if u'ftp' not in session.data:
        session.data[u'ftp'] = {}
    if u'task_list' not in session.data[u'ftp']:
        session.data[u'ftp'][u'task_list'] = []

    cancel_count = 0
    for task_id in session.data[u'ftp'][u'task_list']:
        task = AsyncResult(task_id)
        if not task.ready():
            # Raise SoftTimeLimitExceeded exception on the task
            task.revoke(terminate=True, signal='SIGUSR1')
            cancel_count += 1

    session.data[u'ftp'][u'task_list'] = []
    session.save()

    if cancel_count == 0:
        return {
            'status': 'No download tasks',
            'message': 'There are no active download tasks.'
        }

    # Recent activity log
    node = kwargs['node']
    pid = kwargs.get('pid')
    node.add_log(
        action='ftp_cancel',
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

@must_be_valid_project
@must_be_contributor_or_public
@must_have_addon('ftp', 'node')
@must_not_be_retracted_registration
def ftp_disconnect(auth, node, **kwargs):
    # Recent activity log
    pid = kwargs.get('pid')
    node.add_log(
        action='ftp_disconnect',
        params={
            'node': pid,
            'project': pid
        },
        auth=auth
    )

    return {
        'status': 'OK',
        'message': 'Disconnected from FTP server.'
    }

def validate_data(data):
    # Check presence of required fields
    if 'protocol' not in data or not data['protocol']:
        return {
            'valid': False,
            'message': 'Protocol is a required field.'
        }

    if 'host' not in data or not data['host']:
        return {
            'valid': False,
            'message': 'Host is a required field.'
        }

    if 'passMethod' not in data or not data['passMethod']:
        return {
            'valid': False,
            'message': 'Pass method is a required field.'
        }

    if 'path' not in data or not data['path']:
        return {
            'valid': False,
            'message': 'Path is a required field.'
        }

    if 'files' not in data or not data['files']:
        return {
            'valid': False,
            'message': 'One or more files must be selected.'
        }

    if 'destPid' not in data or not data['destPid']:
        return {
            'valid': False,
            'message': 'One or more files must be selected.'
        }

    # Check for valid values
    if data['protocol'] not in ['ftp', 'ftps', 'sftp']:
        return {
            'valid': False,
            'message': 'Invalid protocol.'
        }

    if data['passMethod'] not in ['plaintext', 'key']:
        return {
            'valid': False,
            'message': 'Invalid pass method.'
        }

    return {
        'valid': True
    }


@celery_app.task
def main_task(osf_cookie, data, request_info):
    '''
    Creates a temporary folder to download the files from the FTP server,
    downloads from it, uploads to the selected storage and deletes the temporary
    files.
    '''
    try:
        tmp_path = create_tmp_folder(request_info['uid'])
        if not tmp_path:
            raise OSError('Could not create temporary folder.')
        try:
            downloaded = DOWNLOAD_FUNCTIONS[data['protocol']](tmp_path, data)
            if not downloaded:
                raise RuntimeError('Could not download the file(s) from the FTP server.')
        except IOError:
            raise RuntimeError('Could not download the file(s) from the FTP server.')

        dest_path = 'osfstorage/' if 'destFolderId' not in data else data['destFolderId']
        uploaded = waterbutler.upload_folder_recursive(osf_cookie, data['destPid'], tmp_path, dest_path)
        shutil.rmtree(tmp_path)

        # Variables for logging into recent activity
        node = AbstractNode.load(request_info['node_id'])
        user = OSFUser.load(request_info['uid'])
        auth = Auth(user=user)

        if uploaded['fail_file'] > 0 or uploaded['fail_folder'] > 0:
            # Recent activity log
            node.add_log(
                action='ftp_upload_fail',
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
            action='ftp_upload_success',
            params={
                'node': request_info['node_id'],
                'project': request_info['pid'],
            },
            auth=auth
        )
    except SoftTimeLimitExceeded:
        tmp_path = tmp_path if 'tmp_path' in locals() else None
        fail_cleanup(tmp_path)
    except Exception:
        tmp_path = tmp_path if 'tmp_path' in locals() else None
        fail_cleanup(tmp_path)
        raise

    return True

def fail_cleanup(tmp_path):
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
        if not os.path.isdir('tmp/ftp'):
            os.mkdir('tmp/ftp')
        count = 1
        folder_name = '%s_%s' % (uid, int(time.time()))
        while os.path.isdir('tmp/ftp/' + folder_name):
            count += 1
            folder_name = '%s_%s_%s' % (uid, int(time.time()), count)
        full_path = 'tmp/ftp/' + folder_name
        os.mkdir(full_path)
    except Exception as exc:
        print(exc)
        full_path = None
    return full_path
