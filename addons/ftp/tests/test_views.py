# -*- coding: utf-8 -*-
import os
import json
import pytest
from tests.base import OsfTestCase
from osf_tests.factories import AuthUserFactory, ProjectFactory, NodeFactory
from framework.auth import Auth
from addons.ftp import views
from pytest_sftpserver.sftp.server import SFTPServer
from pytest_localftpserver.plugin import ProcessFTPServer


class TestFtpViews(OsfTestCase):
    def setUp(self):
        super(TestFtpViews, self).setUp()
        self.user = AuthUserFactory()
        self.auth = self.user.auth
        self.project = ProjectFactory(creator=self.user, is_public=True)
        self.node = NodeFactory(creator=self.user, parent=self.project)


    def test_addon_enable(self):
        set_url = self.project.api_url_for('node_choose_addons')
        view_url = self.project.api_url_for('view_project')
        self.app.post_json(set_url, {'ftp' : False}, auth=self.user.auth)
        res = self.app.get(view_url)
        jres = json.loads(res.text)
        assert 'ftp' not in jres['addons_enabled']
        self.app.post_json(set_url, {'ftp' : True}, auth=self.user.auth)
        res = self.app.get(view_url)
        jres = json.loads(res.text)
        assert 'ftp' in jres['addons_enabled']


    def test_addon_disable(self):
        set_url = self.project.api_url_for('node_choose_addons')
        view_url = self.project.api_url_for('view_project')
        self.app.post_json(set_url, {'ftp' : True}, auth=self.user.auth)
        res = self.app.get(view_url)
        jres = json.loads(res.text)
        assert 'ftp' in jres['addons_enabled']
        self.app.post_json(set_url, {'ftp' : False}, auth=self.user.auth)
        res = self.app.get(view_url)
        jres = json.loads(res.text)
        assert 'ftp' not in jres['addons_enabled']


class TestFtpViewsSFtp(OsfTestCase):
    def setUp(self):
        super(TestFtpViewsSFtp, self).setUp()
        self.user = AuthUserFactory()
        self.auth = self.user.auth
        self.project = ProjectFactory(creator=self.user, is_public=True)
        self.node = NodeFactory(creator=self.user, parent=self.project)
        self.sftpserver = SFTPServer()
        self.sftpserver.start()


    def tearDown(self):
        if self.sftpserver.is_alive():
            self.sftpserver.shutdown()


    def test_sftp_list(self):
        url = self.project.api_url_for('ftp_list')
        with self.sftpserver.serve_content({'foo_dir' : {}, 'bar.txt' : ''}):
            data = {
                'host' : self.sftpserver.host,
                'port' : self.sftpserver.port,
                'username' : 'user',
                'password' : 'pw!',
                'key' : None,
                'protocol' : 'sftp'}
            res = self.app.post_json(url, data, auth=self.user.auth)
            assert res.status == '200 OK'
            assert '"status": "OK"' in res.text
            assert '"filename": "foo_dir"' in res.text


    def test_sftp_list_path_is_not_directory(self):
        url = self.project.api_url_for('ftp_list')
        with self.sftpserver.serve_content({'foo_dir' : {}, 'bar.txt' : ''}):
            data = {
                'host' : self.sftpserver.host,
                'port' : self.sftpserver.port,
                'username' : 'user',
                'password' : 'pw!',
                'key' : None,
                'protocol' : 'sftp',
                'path' : 'bar.txt'}
            res = self.app.post_json(url, data, auth=self.user.auth)
            assert res.status == '200 OK'
            assert 'Path is not a directory.' in res.text


    def test_sftp_list_connection_error(self):
        url = self.project.api_url_for('ftp_list')
        with self.sftpserver.serve_content({'foo_dir' : {}, 'bar.txt' : ''}):
            data = {
                'host' : self.sftpserver.host,
                'port' : 1234,
                'username' : 'user',
                'password' : 'pw!',
                'key' : None,
                'protocol' : 'sftp'}
            res = self.app.post_json(url, data, auth=self.user.auth)
            assert res.status == '200 OK'
            assert 'Connection Error.' in res.text



class TestFtpViewsFtp(OsfTestCase):
    def setUp(self):
        super(TestFtpViewsFtp, self).setUp()
        self.user = AuthUserFactory()
        self.auth = self.user.auth
        self.project = ProjectFactory(creator=self.user, is_public=True)
        self.node = NodeFactory(creator=self.user, parent=self.project)
        self.ftpserver = ProcessFTPServer('fakeusername', 'qweqwe', '', 0)
        self.ftpserver.demon = True
        self.ftpserver.start()
	path = self.ftpserver.server_home
	os.mkdir(path + '/foo_dir')
        os.mkdir(path + '/foo_dir/inner_dir')
        t01 = open(path + '/test01.txt', 'a')
        t01.write('test')
        t01.close()
        open(path + '/bar.txt', 'a').close()
        open(path + '/foo_dir/inner_txt.txt', 'a').close()


    def tearDown(self):
        self.ftpserver.stop()


    def test_ftp_list(self):
	data = {
            'host' : 'localhost',
            'port' : self.ftpserver.server_port,
            'username' : 'fakeusername',
            'password' : 'qweqwe',
            'protocol' : 'ftp',
            'key' : None}
        url = self.project.api_url_for('ftp_list')
        res = self.app.post_json(url, data, auth=self.user.auth)
        assert res.status == '200 OK'
        assert '{"size": 4, "is_directory": false, "filename": "test01.txt"}' in res.text


    def test_ftp_list_inner_directory(self):
	data = {
            'host' : 'localhost',
            'port' : self.ftpserver.server_port,
            'username' : 'fakeusername',
            'password' : 'qweqwe',
            'protocol' : 'ftp',
            'key' : None,
            'path' : 'foo_dir'}
        url = self.project.api_url_for('ftp_list')
        res = self.app.post_json(url, data, auth=self.user.auth)
        assert res.status == '200 OK'
        assert '"filename": "inner_txt.txt"' in res.text


    def test_ftp_list_auth_failed(self):
	data = {
            'host' : 'localhost',
            'port' : self.ftpserver.server_port,
            'username' : 'username',
            'password' : 'password',
            'protocol' : 'ftp',
            'key' : None,
            'path' : 'foo_dir'}
        url = self.project.api_url_for('ftp_list')
        res = self.app.post_json(url, data, auth=self.user.auth)
        assert res.status == '200 OK'
        assert 'Authentication failed.' in res.text

