# -*- coding: utf-8 -*-

import requests
import os
from api.base.utils import waterbutler_api_url_for

def upload_folder_recursive(osf_cookie, pid, local_path, dest_path):
    '''
    Upload all the content (files and folders) inside a folder.
    '''
    content_list = os.listdir(local_path)

    for item_name in content_list:
        full_path = os.path.join(local_path, item_name)
        if os.path.isdir(full_path):  # Create directory
            folder = create_folder(osf_cookie, pid, item_name, dest_path)
            if folder['success']:
                upload_folder_recursive(osf_cookie, pid, full_path, folder['id'])
        else:  # File
            upload_file(osf_cookie, pid, full_path, item_name, dest_path)

    return True

def create_folder(osf_cookie, pid, folder_name, dest_path):
    dest_arr = dest_path.split('/')
    response = requests.put(
        waterbutler_api_url_for(
            pid, dest_arr[0], path='/' + os.path.join(*dest_arr[1:]),
            name=folder_name, kind='folder', meta='', _internal=True
        ),
        cookies={
            'osf': osf_cookie
        }
    )
    if response.status_code == requests.codes.created:
        data = response.json()
        return {
            'success': True,
            'id': data['data']['id']
        }
    return {
        'success': False
    }

def upload_file(osf_cookie, pid, file_path, file_name, dest_path):
    response = None
    dest_arr = dest_path.split('/')
    with open(file_path, 'r') as f:
        response = requests.put(
            waterbutler_api_url_for(
                pid, dest_arr[0], path='/' + os.path.join(*dest_arr[1:]),
                name=file_name, kind='file', _internal=True
            ),
            data=f,
            cookies={
                'osf': osf_cookie
            }
        )
    return response
