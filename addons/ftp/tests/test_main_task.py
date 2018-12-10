# -*- coding: utf-8 -*-
import os
import json
import pytest
import mock
from tests.base import OsfTestCase
from osf_tests.factories import AuthUserFactory, ProjectFactory, NodeFactory
from framework.auth import Auth
from addons.ftp import views
from pytest_sftpserver.sftp.server import SFTPServer


class TestFtpMainTask(OsfTestCase):
    def setUp(self):
        super(TestFtpMainTask, self).setUp()
        self.user = AuthUserFactory()
        self.auth = self.user.auth
        self.project = ProjectFactory(creator=self.user, is_public=True)
        self.node = NodeFactory(creator=self.user, parent=self.project)
        set_url = self.project.api_url_for('node_choose_addons')
        self.app.post_json(set_url, {'ftp' : True}, auth=self.user.auth)
        self.sftpserver = SFTPServer()
        self.sftpserver.start()


    def tearDown(self):
        if self.sftpserver.is_alive():
            self.sftpserver.shutdown()


    @mock.patch('website.util.waterbutler.upload_folder_recursive')
    def test_task_succeed(self, upload_mock):
        upload_mock.return_value = {
            'fail_file' : 0,
            'fail_folder' : 0}
        url = self.project.api_url_for('ftp_download')
        with self.sftpserver.serve_content({'foo_dir' : {}, 'bar.txt' : 'test'}):
            data = {
                'host' : self.sftpserver.host,
                'port' : self.sftpserver.port,
                'username' : 'user',
                'password' : 'pw!',
                'key' : None,
                'protocol' : 'sftp',
                'passMethod' : 'plaintext',
                'path' : '/',
                'files' : [{'name' : 'bar.txt', 'type' : 'file'}],
                'destPid' : self.project._id}
            res = self.app.post_json(url, data, auth=self.user.auth)
            upload_mock.delay.assert_called()
            assert res.status == '200 OK'
            assert '"status": "OK"' in res.text


    def test_download_failed(self):
        with pytest.raises(RuntimeError) as ex:
            with self.sftpserver.serve_content({'foo_dir' : {}, 'bar.txt' : 'test'}):
                data = {
                    'host' : self.sftpserver.host,
                    'port' : self.sftpserver.port,
                    'username' : 'user',
                    'password' : 'pw!',
                    'key' : None,
                    'protocol' : 'sftp',
                    'passMethod' : 'plaintext',
                    'path' : '/',
                    'files' : [{'name' : 'fileNotExists', 'type' : 'file'}],
                    'destPid' : self.project._id}
                req_info = {
                    'uid' : self.user._id,
                    'pid' : self.project._id,
                    'node_id' : self.node._id}
                res = views.main_task('', data, req_info)
        assert 'Could not download the file(s) from the FTP server.' in str(ex)


    @mock.patch('addons.ftp.views.create_tmp_folder')
    def test_create_tmp_folder_failed(self, create_folder_mock):
        with pytest.raises(OSError) as ex:
            create_folder_mock.return_value = 0
            with self.sftpserver.serve_content({'foo_dir' : {}, 'bar.txt' : 'test'}):
                data = {
                    'host' : self.sftpserver.host,
                    'port' : self.sftpserver.port,
                    'username' : 'user',
                    'password' : 'pw!',
                    'key' : None,
                    'protocol' : 'sftp',
                    'passMethod' : 'plaintext',
                    'path' : '/',
                    'files' : [{'name' : 'bar.txt', 'type' : 'file'}],
                    'destPid' : self.project._id}
                req_info = {
                    'uid' : self.user._id,
                    'pid' : self.project._id,
                    'node_id' : self.node._id}
                res = views.main_task('', data, req_info)
        create_folder_mock.delay.assert_called()
        assert 'Could not create temporary folder.' in str(ex)


    @mock.patch('website.util.waterbutler.upload_folder_recursive')
    def test_upload_file_failed(self, upload_mock):
        upload_mock.return_value = {
            'fail_file' : 1,
            'fail_folder' : 0}
        with pytest.raises(RuntimeError) as ex:
            with self.sftpserver.serve_content({'foo_dir' : {'1' : '', '2' : ''}, 'bar.txt' : 'test'}):
                data = {
                    'host' : self.sftpserver.host,
                    'port' : self.sftpserver.port,
                    'username' : 'user',
                    'password' : 'pw!',
                    'key' : None,
                    'protocol' : 'sftp',
                    'passMethod' : 'plaintext',
                    'path' : '/',
                    'files' : [{'name' : 'bar.txt', 'type' : 'file'}],
                    'destPid' : self.project._id}
                req_info = {
                    'uid' : self.user._id,
                    'pid' : self.project._id,
                    'node_id' : self.node._id}
                res = views.main_task('', data, req_info)
        upload_mock.delay.assert_called()
        assert 'Failed to upload 1 file(s) to storage.' in str(ex)


    @mock.patch('website.util.waterbutler.upload_folder_recursive')
    def test_upload_folder_failed(self, upload_mock):
        upload_mock.return_value = {
            'fail_file' : 0,
            'fail_folder' : 1}
        with pytest.raises(RuntimeError) as ex:
            with self.sftpserver.serve_content({'foo_dir' : {}, 'bar.txt' : 'test'}):
                data = {
                    'host' : self.sftpserver.host,
                    'port' : self.sftpserver.port,
                    'username' : 'user',
                    'password' : 'pw!',
                    'key' : None,
                    'protocol' : 'sftp',
                    'passMethod' : 'plaintext',
                    'path' : '/',
                    'files' : [{'name' : 'foo_dir', 'type' : 'folder'}],
                    'destPid' : self.project._id}
                req_info = {
                    'uid' : self.user._id,
                    'pid' : self.project._id,
                    'node_id' : self.node._id}
                res = views.main_task('', data, req_info)
        upload_mock.delay.assert_called()
        assert 'Failed to upload 1 folder(s) to storage.' in str(ex)


    @mock.patch('website.util.waterbutler.upload_folder_recursive')
    def test_upload_file_and_folder_failed(self, upload_mock):
        upload_mock.return_value = {
            'fail_file' : 2,
            'fail_folder' : 1}
        with pytest.raises(RuntimeError) as ex:
            with self.sftpserver.serve_content({'foo_dir' : {'1' : '','2' : ''}, 'bar.txt' : 'test'}):
                data = {
                    'host' : self.sftpserver.host,
                    'port' : self.sftpserver.port,
                    'username' : 'user',
                    'password' : 'pw!',
                    'key' : None,
                    'protocol' : 'sftp',
                    'passMethod' : 'plaintext',
                    'path' : '/',
                    'files' : [{'name' : 'foo_dir', 'type' : 'folder'}],
                    'destPid' : self.project._id}
                req_info = {
                    'uid' : self.user._id,
                    'pid' : self.project._id,
                    'node_id' : self.node._id}
                res = views.main_task('', data, req_info)
        upload_mock.delay.assert_called()
        assert 'Failed to upload 2 file(s) and 1 folder(s) to storage.' in str(ex)


