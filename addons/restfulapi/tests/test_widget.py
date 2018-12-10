# -*- coding: utf-8 -*-
import subprocess
import mock
import pytest
from tests.base import OsfTestCase
from osf_tests.factories import AuthUserFactory, ProjectFactory
from framework.auth import Auth
from addons.restfulapi import views
from .utils import MockResponse

VALID_URL = 'https://www.nii.ac.jp/_img/_logo/mainLogo.gif'

class TestRestfulapiWidget(OsfTestCase):
    def setUp(self):
        super(TestRestfulapiWidget, self).setUp()
        self.user = AuthUserFactory()
        self.auth = Auth(user=self.user)
        self.project = ProjectFactory(creator=self.user)
        set_url = self.project.api_url_for('node_choose_addons')
        self.app.post_json(set_url, {'restfulapi' : True}, auth=self.user.auth)


    @mock.patch('addons.restfulapi.views.get_files')
    def test_valid_input(self, get_files_mock):
        get_files_mock.return_value.poll.return_value = 0

        url = self.project.api_url_for('restfulapi_download')
        response = self.app.post_json(url, {
            'url': VALID_URL,
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
        get_files_mock.return_value.poll.return_value = 0

        url = self.project.api_url_for('restfulapi_download')
        response = self.app.post_json(url, {
            'url': VALID_URL + ' --spider --force-html -i',
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
            'url': VALID_URL,
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
            'url': 'https://www.nii.ac.jp/pagenotexists',
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


    @mock.patch('addons.restfulapi.views.get_files')
    def test_succeed_task_no_options(self, get_files_mock):
        tmp_path = 'tmp/restfulapi/%s_12345' % self.user._id
        osf_cookie = 'chocolate_cookie'
        data = {
            'url': VALID_URL,
            'recursive': False,
            'interval': False,
            'intervalValue': '30',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }
        get_files_mock.return_value = subprocess.Popen(['exit', '0'], shell=True)
        request_info = {
            'node_id': self.project._id,
            'pid': self.project._id,
            'uid': self.user._id,
        }
        return_value = views.main_task(osf_cookie, data, request_info)

        get_files_mock.delay.assert_called()
        assert return_value


    @mock.patch('addons.restfulapi.views.get_files')
    def test_succeed_task_with_options(self, get_files_mock):
        tmp_path = 'tmp/restfulapi/%s_12345' % self.user._id
        osf_cookie = 'chocolate_cookie'
        data = {
            'url': VALID_URL,
            'recursive': True,
            'interval': True,
            'intervalValue': '30',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }
        get_files_mock.return_value = subprocess.Popen(['exit 0'], shell=True)
        request_info = {
            'node_id': self.project._id,
            'pid': self.project._id,
            'uid': self.user._id,
        }
        return_value = views.main_task(osf_cookie, data, request_info)

        get_files_mock.delay.assert_called()
        assert return_value


    @mock.patch('addons.restfulapi.views.create_tmp_folder')
    def test_main_task_create_tmp_folder_failed(self, create_tmp_folder_mock):
        create_tmp_folder_mock.return_value = 0
        tmp_path = 'tmp/restfulapi/%s_12345' % self.user._id
        osf_cookie = 'chocolate_cookie'
        data = {
            'url': VALID_URL,
            'recursive': True,
            'interval': True,
            'intervalValue': '30',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }
        request_info = {
            'node_id': self.project._id,
            'pid': self.project._id,
            'uid': self.user._id,
        }
        with pytest.raises(OSError) as ex:
            return_value = views.main_task(osf_cookie, data, request_info)
        create_tmp_folder_mock.delay.assert_called()
        assert 'Could not create temporary folder.' in str(ex)


    @mock.patch('addons.restfulapi.views.get_files')
    def test_main_task_wget_failed(self, get_files_mock):
        tmp_path = 'tmp/restfulapi/%s_12345' % self.user._id
        osf_cookie = 'chocolate_cookie'
        data = {
            'url': VALID_URL,
            'recursive': True,
            'interval': True,
            'intervalValue': '30',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }
        get_files_mock.return_value = subprocess.Popen(['exit 1'], shell=True)
        request_info = {
            'node_id': self.project._id,
            'pid': self.project._id,
            'uid': self.user._id,
        }
        with pytest.raises(RuntimeError) as ex:
            return_value = views.main_task(osf_cookie, data, request_info)

        get_files_mock.delay.assert_called()
        assert 'wget command returned a non-success code.' in str(ex)


    @mock.patch('website.util.waterbutler.upload_folder_recursive')
    @mock.patch('addons.restfulapi.views.get_files')
    def test_main_task_upload_file_failed(self, get_files_mock, upload_mock):
        get_files_mock.return_value = subprocess.Popen(['exit 0'], shell=True)
        upload_mock.return_value = {
            'fail_file': 2,
            'fail_folder': 0
        }
        tmp_path = 'tmp/restfulapi/%s_12345' % self.user._id
        osf_cookie = 'chocolate_cookie'
        data = {
            'url': VALID_URL,
            'recursive': True,
            'interval': True,
            'intervalValue': '30',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }
        request_info = {
            'node_id': self.project._id,
            'pid': self.project._id,
            'uid': self.user._id,
        }
        with pytest.raises(RuntimeError) as ex:
            return_value = views.main_task(osf_cookie, data, request_info)
        get_files_mock.delay.assert_called()
        upload_mock.delay.assert_called()
        assert 'Failed to upload 2 file(s) to storage.' in str(ex)


    @mock.patch('website.util.waterbutler.upload_folder_recursive')
    @mock.patch('addons.restfulapi.views.get_files')
    def test_main_task_upload_folder_failed(self, get_files_mock, upload_mock):
        get_files_mock.return_value = subprocess.Popen(['exit 0'], shell=True)
        upload_mock.return_value = {
            'fail_file': 0,
            'fail_folder': 1
        }
        tmp_path = 'tmp/restfulapi/%s_12345' % self.user._id
        osf_cookie = 'chocolate_cookie'
        data = {
            'url': VALID_URL,
            'recursive': True,
            'interval': True,
            'intervalValue': '30',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }
        request_info = {
            'node_id': self.project._id,
            'pid': self.project._id,
            'uid': self.user._id,
        }
        with pytest.raises(RuntimeError) as ex:
            return_value = views.main_task(osf_cookie, data, request_info)
        get_files_mock.delay.assert_called()
        upload_mock.delay.assert_called()
        assert 'Failed to upload 1 folder(s) to storage.' in str(ex)


    @mock.patch('website.util.waterbutler.upload_folder_recursive')
    @mock.patch('addons.restfulapi.views.get_files')
    def test_main_task_upload_file_and_folder_failed(self, get_files_mock, upload_mock):
        get_files_mock.return_value = subprocess.Popen(['exit 0'], shell=True)
        upload_mock.return_value = {
            'fail_file': 5,
            'fail_folder': 2
        }
        tmp_path = 'tmp/restfulapi/%s_12345' % self.user._id
        osf_cookie = 'chocolate_cookie'
        data = {
            'url': VALID_URL,
            'recursive': True,
            'interval': True,
            'intervalValue': '30',
            'pid': self.project._id,
            'folderId': '1234567890abcdef'
        }
        request_info = {
            'node_id': self.project._id,
            'pid': self.project._id,
            'uid': self.user._id,
        }
        with pytest.raises(RuntimeError) as ex:
            return_value = views.main_task(osf_cookie, data, request_info)
        get_files_mock.delay.assert_called()
        upload_mock.delay.assert_called()
        assert 'Failed to upload 5 file(s) and 2 folder(s) to storage.' in str(ex)

