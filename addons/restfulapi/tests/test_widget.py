# -*- coding: utf-8 -*-
import mock
import pytest
from tests.base import OsfTestCase
from osf_tests.factories import AuthUserFactory, ProjectFactory
from framework.auth import Auth
from addons.restfulapi import views
from .utils import MockResponse
from api.base.settings.defaults import OSF_URL

class TestRestfulapiWidget(OsfTestCase):
    def setUp(self):
        super(TestRestfulapiWidget, self).setUp()
        self.user = AuthUserFactory()
        self.auth = Auth(user=self.user)
        self.project = ProjectFactory(creator=self.user)


    @mock.patch('addons.restfulapi.views.get_files')
    def test_valid_input(self, get_files_mock):
        url = self.project.api_url_for('restfulapi_download')
        response = self.app.post_json(url, {
            'url': OSF_URL,
            'recursive': False,
            'interval': False,
            'intervalValue': '3000',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }, auth=self.user.auth)

        get_files_mock.delay.assert_called()
        assert response.status_code == 200
        assert response.json['status'] == 'OK'


    @mock.patch('addons.restfulapi.views.get_files')
    def test_url_with_unnecessary_part(self, get_files_mock):
        url = self.project.api_url_for('restfulapi_download')
        response = self.app.post_json(url, {
            'url': OSF_URL + ' --spider --force-html -i',
            'recursive': False,
            'interval': False,
            'intervalValue': '3000',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }, auth=self.user.auth)

        get_files_mock.delay.assert_called()
        assert response.status_code == 200
        assert response.json['status'] == 'OK'


    @mock.patch('addons.restfulapi.views.get_files')
    def test_missing_url(self, get_files_mock):
        url = self.project.api_url_for('restfulapi_download')
        response = self.app.post_json(url, {
            'url': '',
            'recursive': False,
            'interval': False,
            'intervalValue': '3000',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }, auth=self.user.auth)

        assert not get_files_mock.delay.called
        assert response.status_code == 200
        assert response.json['status'] == 'Failed'
        assert response.json['message'] == 'Please specify an URL.'


    @mock.patch('addons.restfulapi.views.get_files')
    def test_missing_destination(self, get_files_mock):
        url = self.project.api_url_for('restfulapi_download')
        response = self.app.post_json(url, {
            'url': OSF_URL,
            'recursive': False,
            'interval': False,
            'intervalValue': '3000',
            'pid': '',
            'folderId': ''
        }, auth=self.user.auth)

        assert not get_files_mock.delay.called
        assert response.status_code == 200
        assert response.json['status'] == 'Failed'
        assert response.json['message'] == 'Please specify the destination to save the file(s).'


    @mock.patch('addons.restfulapi.views.get_files')
    def test_url_not_exists(self, get_files_mock):
        url = self.project.api_url_for('restfulapi_download')
        response = self.app.post_json(url, {
            'url': 'http://www.google.com/pagenotexists',
            'recursive': False,
            'interval': False,
            'intervalValue': '3000',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }, auth=self.user.auth)

        assert not get_files_mock.delay.called
        assert response.status_code == 200
        assert response.json['status'] == 'Failed'
        assert response.json['message'] == 'URL returned an invalid response.'


    @mock.patch('addons.restfulapi.views.get_files')
    def test_domain_cannot_resolve(self, get_files_mock):
        url = self.project.api_url_for('restfulapi_download')
        response = self.app.post_json(url, {
            'url': 'http://site.that.dont.exist',
            'recursive': False,
            'interval': False,
            'intervalValue': '3000',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }, auth=self.user.auth)

        assert not get_files_mock.delay.called
        assert response.status_code == 200
        assert response.json['status'] == 'Failed'
        assert response.json['message'] == 'An error ocurred while accessing the URL.'


class TestMainTask(OsfTestCase):
    def setUp(self):
        super(TestMainTask, self).setUp()
        self.user = AuthUserFactory()
        self.auth = Auth(user=self.user)
        self.project = ProjectFactory(creator=self.user)

    @mock.patch('addons.restfulapi.views.shutil')
    @mock.patch('addons.restfulapi.views.upload_folder_content')
    @mock.patch('addons.restfulapi.views.subprocess')
    @mock.patch('addons.restfulapi.views.create_tmp_folder')
    def test_succeed_task_no_options(self, create_tmp_folder_mock, subprocess_mock, upload_folder_content_mock, shutil):
        tmp_path = 'tmp/restfulapi/%s_12345' % self.user._id
        osf_cookie = 'chocolate_cookie'
        data = {
            'url': 'example.com/hello_world.json',
            'recursive': False,
            'interval': False,
            'intervalValue': '30',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }

        create_tmp_folder_mock.return_value = tmp_path
        subprocess_mock.call.return_value = 0
        upload_folder_content_mock.return_value = True
        shutil.rmtree.return_value = True

        return_value = views.main_task(osf_cookie, self.user.auth, data)

        create_tmp_folder_mock.assert_called_with(self.user.auth)
        subprocess_mock.call.assert_called_with(['wget', '-P', tmp_path, data['url']])
        upload_folder_content_mock.assert_called_with(
            osf_cookie, self.project._id, tmp_path, data['folderId']
        )
        assert return_value


    @mock.patch('addons.restfulapi.views.shutil')
    @mock.patch('addons.restfulapi.views.upload_folder_content')
    @mock.patch('addons.restfulapi.views.subprocess')
    @mock.patch('addons.restfulapi.views.create_tmp_folder')
    def test_succeed_task_with_options(self, create_tmp_folder_mock, subprocess_mock, upload_folder_content_mock, shutil):
        tmp_path = 'tmp/restfulapi/%s_12345' % self.user._id
        osf_cookie = 'chocolate_cookie'
        data = {
            'url': 'example.com/hello_world.json',
            'recursive': True,
            'interval': True,
            'intervalValue': '30',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }

        create_tmp_folder_mock.return_value = tmp_path
        subprocess_mock.call.return_value = 0
        upload_folder_content_mock.return_value = True
        shutil.rmtree.return_value = True

        return_value = views.main_task(osf_cookie, self.user.auth, data)

        create_tmp_folder_mock.assert_called_with(self.user.auth)
        subprocess_mock.call.assert_called_with(
            ['wget', '-P', tmp_path, '-r', '-w', data['intervalValue'], data['url']]
        )
        upload_folder_content_mock.assert_called_with(
            osf_cookie, self.project._id, tmp_path, data['folderId']
        )
        assert return_value

