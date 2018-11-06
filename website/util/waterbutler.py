# -*- coding: utf-8 -*-

import requests
import os
from api.base.utils import waterbutler_api_url_for


def upload_folder_recursive(osf_cookie, pid, local_path, dest_path):
    '''
    Upload all the content (files and folders) inside a folder.
    '''
    count = {
        'fail_file': 0,
        'fail_folder': 0
    }
    content_list = os.listdir(local_path)

    for item_name in content_list:
        full_path = os.path.join(local_path, item_name)

        # Upload folder
        if os.path.isdir(full_path):
            folder_response = create_folder(osf_cookie, pid, item_name, dest_path)
            if folder_response.status_code == requests.codes.created:
                folder_id = folder_response.json()['data']['id']
                rec_response = upload_folder_recursive(osf_cookie, pid, full_path, folder_id)
                count['fail_file'] += rec_response['fail_file']
                count['fail_folder'] += rec_response['fail_folder']
            else:
                count['fail_folder'] += 1

        # Upload file
        else:
            file_response = upload_file(osf_cookie, pid, full_path, item_name, dest_path)
            if file_response.status_code != requests.codes.created:
                count['fail_file'] += 1

    return count

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
    return response

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
