# -*- coding: utf-8 -*-

import os
import ftplib
import paramiko
import download_ftp_tree
from contextlib import closing
from StringIO import StringIO


def serialize_ftp_widget(node):
    node_addon = node.get_addon('ftp')
    ftp_widget_data = {
        'complete': True,
        'more': True,
    }
    ftp_widget_data.update(node_addon.config.to_json())
    return ftp_widget_data


def _is_directory(longname):
    return longname[0] == 'd'


def sftp_list(host, port, username, password=None, key=None, path='/', **kwargs):
    pkey = None
    if key:
        pkey = paramiko.RSAKey.from_private_key(StringIO(key))
    with closing(paramiko.Transport((host, int(port)))) as ts:
        ts.connect(username=username, password=password, pkey=pkey)
        sftp = paramiko.SFTPClient.from_transport(ts)
        attrs = sftp.listdir_attr(path)
        file_list = []
        for attr in attrs:
            file_list.append({
                'filename': attr.filename,
                'size': attr.st_size,
                'is_directory': _is_directory(attr.longname)})
        return file_list


def sftp_download(tmp_path, data, **kwargs):
    pkey = None
    if data['key']:
        pkey = paramiko.RSAKey.from_private_key(StringIO(data['key']))
    with closing(paramiko.Transport((data['host'], int(data['port'])))) as ts:
        ts.connect(username=data['username'], password=data['password'], pkey=pkey)
        sftp = paramiko.SFTPClient.from_transport(ts)
        for file_data in data['files']:
            path = data['path'] + file_data['name']
            if file_data['type'] == 'folder':
                sftp_get_recursive(path, tmp_path + '/' + file_data['name'], sftp)
            else:
                sftp.get(path, tmp_path + '/' + file_data['name'])
        return True


def sftp_get_recursive(path, dest, sftp):
    attrs = sftp.listdir_attr(path)

    if not os.path.isdir(dest):
        os.mkdir(dest)

    for attr in attrs:
        filename = attr.filename

        if _is_directory(attr.longname):
            sftp_get_recursive(path + '/' + filename, dest + '/' + filename, sftp)
        else:
            sftp.get(path + '/' + filename, dest + '/' + filename)


def _ftp_get_size(ftp, filename):
    try:
        ftp.voidcmd('TYPE I')
        return ftp.size(filename)
    except ftplib.error_perm:
        return ''


def _ftp_is_directory(ftp, path):
    try:
        ftp.cwd(path)
        ftp.cwd('..')
        return True
    except ftplib.error_perm:
        return False


def ftp_list(host, port, username, password, path='/', **kwargs):
    if kwargs['protocol'] == 'ftps':
        ftp = ftplib.FTP_TLS()
    else:
        ftp = ftplib.FTP()
    ftp.connect(host, int(port))
    ftp.login(username, password)
    if kwargs['protocol'] == 'ftps':
        ftp.prot_p()
    ftp.cwd(path)
    nlst = ftp.nlst()
    file_list = []
    for filename in nlst:
        file_list.append({
            'filename': filename,
            'size': _ftp_get_size(ftp, filename),
            'is_directory': _ftp_is_directory(ftp, filename)})
    return file_list


def ftp_download(tmp_path, data, **kwargs):
    if data['protocol'] == 'ftps':
        ftp = ftplib.FTP_TLS()
    else:
        ftp = ftplib.FTP()

    ftp.connect(data['host'], int(data['port']))
    ftp.login(data['username'], data['password'])

    if data['protocol'] == 'ftps':
        ftp.prot_p()

    for file_data in data['files']:
        path = data['path'] + file_data['name']
        if file_data['type'] == 'folder':
            download_ftp_tree.download_ftp_tree(
                ftp,
                path,
                tmp_path,
                overwrite=True,
                guess_by_extension=True
            )
        else:
            with open('%s/%s' % (tmp_path, file_data['name']), 'wb') as f:
                ftp.retrbinary('RETR ' + path, f.write)
    return True
