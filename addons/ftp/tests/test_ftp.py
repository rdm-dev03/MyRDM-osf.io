# -*- coding: utf-8 -*-
import os
import pytest
import ftplib
from pytest_sftpserver.sftp.server import SFTPServer
from pytest_localftpserver import plugin
from addons.ftp import utils


class TestSFTPList():
    def test_sftp_list_root(self, sftpserver):
        with sftpserver.serve_content({'foo_dir' : {}, 'bar.txt' : ''}):
            args = {
                'host' : sftpserver.host,
                'port' : sftpserver.port,
                'username' : 'user',
                'password' : 'pw!',
                'key' : None}
            f_list = utils.sftp_list(**args)
            assert len(f_list) == 2
            assert f_list[0]['filename'] == 'foo_dir'
            assert f_list[0]['is_directory'] == True
            assert f_list[1]['filename'] == 'bar.txt'
            assert f_list[1]['is_directory'] == False
            assert f_list[1]['size'] == 0


    def test_sftp_list_specific_dir(self, sftpserver):
        with sftpserver.serve_content({'foo_dir' : {
                    'inner_dir' : {},
                    'inner_txt.txt' : 'test'},
                'bar.txt' : ''}):
            args = {
                'host' : sftpserver.host,
                'port' : sftpserver.port,
                'username' : 'user',
                'password' : 'pw!',
                'key' : None,
                'path' : 'foo_dir'}
            f_list = utils.sftp_list(**args)
            assert len(f_list) == 2
            assert f_list[0]['filename'] == 'inner_dir'
            assert f_list[0]['is_directory'] == True
            assert f_list[1]['filename'] == 'inner_txt.txt'
            assert f_list[1]['is_directory'] == False
            assert f_list[1]['size'] == 4


class TestFTPList:
    def _create_test_files(self, path):
        try:
            os.mkdir(path + '/foo_dir')
            os.mkdir(path + '/foo_dir/inner_dir')
            t01 = open(path + '/test01.txt', 'a')
            t01.write('test')
            t01.close()
            open(path + '/bar.txt', 'a').close()
            open(path + '/foo_dir/inner_txt.txt', 'a').close()
        except OSError:
            pass


    def test_ftp_list_root(self, ftpserver):
        self._create_test_files(ftpserver.server_home)
        args = {
            'host' : 'localhost',
            'port' : ftpserver.server_port,
            'username' : 'fakeusername',
            'password' : 'qweqwe',
            'protocol' : 'ftp',
            'key' : None}
        f_list = utils.ftp_list(**args)
        assert len(f_list) == 3
        assert f_list[0]['filename'] == 'bar.txt'
        assert f_list[0]['is_directory'] == False
        assert f_list[1]['filename'] == 'foo_dir'
        assert f_list[1]['is_directory'] == True
        assert f_list[2]['filename'] == 'test01.txt'
        assert f_list[2]['is_directory'] == False
        assert f_list[2]['size'] == 4


    def test_ftp_list_specific_dir(self, ftpserver):
        self._create_test_files(ftpserver.server_home)
        args = {
            'host' : 'localhost',
            'port' : ftpserver.server_port,
            'username' : 'fakeusername',
            'password' : 'qweqwe',
            'protocol' : 'ftp',
            'path' : 'foo_dir',
            'key' : None}
        f_list = utils.ftp_list(**args)
        assert len(f_list) == 2
        assert f_list[0]['filename'] == 'inner_dir'
        assert f_list[0]['is_directory'] == True
        assert f_list[1]['filename'] == 'inner_txt.txt'
        assert f_list[1]['is_directory'] == False

