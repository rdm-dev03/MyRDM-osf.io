# -*- coding: utf-8 -*-
import mock
import pytest
from tests.base import OsfTestCase
from osf_tests.factories import AuthUserFactory, ProjectFactory
from framework.auth import Auth
from addons.restfulapi import views
from .utils import MockResponse


class TestRestfulapiWidget(OsfTestCase):
    def setUp(self):
        super(TestRestfulapiWidget, self).setUp()
        self.user = AuthUserFactory()
        self.auth = Auth(user=self.user)
        self.project = ProjectFactory(creator=self.user)

    @mock.patch('addons.restfulapi.views.requests')
    @mock.patch('addons.restfulapi.views.main_task')
    def test_valid_input(self, main_task_mock, requests_mock):
        main_task_mock.delay.return_value = 'abcdefghijklmn'
        requests_mock.head.return_value = MockResponse({'data': {}}, 200)

        url = self.project.api_url_for('restfulapi_widget')
        response = self.app.post_json(url, {
            'url': 'example.com/hello_world.json',
            'recursive': False,
            'interval': False,
            'intervalValue': '3000',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }, auth=self.user.auth)

        main_task_mock.delay.assert_called()
        assert response.status_code == 200
        assert response.json['status'] == 'OK'

    @mock.patch('addons.restfulapi.views.requests')
    @mock.patch('addons.restfulapi.views.main_task')
    def test_missing_url(self, main_task_mock, requests_mock):
        main_task_mock.delay.return_value = 'abcdefghijklmn'
        requests_mock.head.return_value = MockResponse({'data': {}}, 404)

        url = self.project.api_url_for('restfulapi_widget')
        response = self.app.post_json(url, {
            'url': '',
            'recursive': False,
            'interval': False,
            'intervalValue': '3000',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }, auth=self.user.auth)

        assert not main_task_mock.delay.called
        assert response.status_code == 200
        assert response.json['status'] == 'Failed'
        assert response.json['message'] == 'Please specify an URL.'

    @mock.patch('addons.restfulapi.views.requests')
    @mock.patch('addons.restfulapi.views.main_task')
    def test_missing_destination(self, main_task_mock, requests_mock):
        main_task_mock.delay.return_value = 'abcdefghijklmn'
        requests_mock.head.return_value = MockResponse({'data': {}}, 404)

        url = self.project.api_url_for('restfulapi_widget')
        response = self.app.post_json(url, {
            'url': 'example.com/hello_world.json',
            'recursive': False,
            'interval': False,
            'intervalValue': '3000',
            'pid': '',
            'folderId': ''
        }, auth=self.user.auth)

        assert not main_task_mock.delay.called
        assert response.status_code == 200
        assert response.json['status'] == 'Failed'
        assert response.json['message'] == 'Please specify the destination to save the file(s).'

    @mock.patch('addons.restfulapi.views.requests')
    @mock.patch('addons.restfulapi.views.main_task')
    def test_invalid_url(self, main_task_mock, requests_mock):
        main_task_mock.delay.return_value = 'abcdefghijklmn'
        requests_mock.head.return_value = MockResponse({'data': {}}, 404)

        url = self.project.api_url_for('restfulapi_widget')
        response = self.app.post_json(url, {
            'url': 'site.that.dont.exist',
            'recursive': False,
            'interval': False,
            'intervalValue': '3000',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }, auth=self.user.auth)

        assert not main_task_mock.delay.called
        assert response.status_code == 200
        assert response.json['status'] == 'Failed'
        assert response.json['message'] == 'URL returned an invalid response.'


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
