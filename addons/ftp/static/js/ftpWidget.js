'use strict';
var $ = require('jquery');
var ko = require('knockout');
var $osf = require('js/osfHelpers');
var m = require('mithril');
var Fangorn = require('js/fangorn').Fangorn;
var Raven = require('raven-js');

var nodeApiUrl = window.contextVars.node.urls.api;
var filebrowser;
var itemsToRefresh = [];


function NodeViewModel(data) {
    var self = this;

    self.type = ko.observable(data['type']);
    self.name = ko.observable(data['name']);
    self.size = ko.observable(data['size']);
    self.selected = ko.observable(false);
}


function ViewModel(url) {
    var self = this;

    self.protocol = ko.observable('ftp');
    self.host = ko.observable('');
    self.username = ko.observable('');
    self.password = ko.observable('');
    self.passMethod = ko.observable('plaintext');
    self.connected = ko.observable(false);
    self.connecting = ko.observable(false);
    self.key = null;

    self.browserPath = ko.observable('');
    self.browserFileList = ko.observableArray([]);
    self.selectedIndex = null;

    self.loadFile = function (file) {
        if (!file) {
            return;
        }

        // Do not let huge files be sent
        if (file.size < 10000) {
            var reader = new FileReader();
            reader.onload = function (e) {
                self.key = e.target.result;
            };
            reader.readAsText(file);
        } else {
            self.key = null;
            $osf.growl('FTP', 'Selected file is too big and won\' t be sent to server.', 'danger');
        }
    };

    self.connect = function () {
        self.host(self.host().trim());
        if (!self.host()) {
            $osf.growl('FTP', 'Host is a required field.', 'danger');
            return false;
        }

        self.connecting(true);
        retrieveFiles('/', 'connect', function () {
            // Success
            self.connecting(false);
            self.browserPath('/');
            $osf.growl('FTP', 'Successfully connected to FTP server.', 'success');
        }, function () {
            // Fail
            self.connecting(false);
        });
    };

    self.disconnect = function () {
        self.browserFileList([]);
        $('#ftpScope #ftp-browser .tb-header-row').css('visibility', 'hidden');
        self.connected(false);

        $.ajax({
            url: url + 'disconnect/',
            type: 'POST',
            success: function (response) {
                if (response.status == 'OK') {
                    $osf.growl('FTP', response.message, 'success');
                } else {
                    $osf.growl('FTP', response.message, 'danger');
                }
            },
            error: function () {
                $osf.growl('FTP', 'There was an error while processing your request.', 'danger');
            }
        });
    };

    self.changeFolder = function (node) {
        var pathArr = self.browserPath().split('/');
        pathArr.pop();  // Pop because of the last slash

        if (node.type() == 'back') {
            pathArr.pop();
        } else { // folder
            pathArr.push(node.name());
        }

        var path = pathArr.join('/') + '/';
        retrieveFiles(path, 'change_folder', function () {
            self.browserPath(path);
        });
    };

    self.selectNode = function (node, event) {
        var i;

        // Ignore 'Parent directory' nodes
        if (node.type() == 'back') {
            return;
        }

        // First selected node or reference node for when selecting with shift
        var index = ko.contextFor(event.target).$index();
        if (self.selectedIndex === null || (!event.ctrlKey && !event.shiftKey)) {
            self.selectedIndex = index;
        }

        // Unselect all
        if (!event.ctrlKey) {
            for (i = 0; i < self.browserFileList().length; i++) {
                self.browserFileList()[i].selected(false);
            }
        }

        // Select node
        if (event.ctrlKey) {
            node.selected(!node.selected());
        } else if (event.shiftKey) {
            var fromIndex, toIndex;
            if (index > self.selectedIndex) {
                fromIndex = self.selectedIndex;
                toIndex = index;
            } else {
                fromIndex = index;
                toIndex = self.selectedIndex;
            }
            // Select fromIndex toIndex
            for (i = fromIndex; i <= toIndex; i++) {
                self.browserFileList()[i].selected(true);
            }
        } else {
            node.selected(true);
        }
    };

    self.download = function () {
        self.host(self.host().trim());
        if (!self.host()) {
            $osf.growl('FTP', 'Host is a required field.', 'danger');
            return false;
        }

        var selectedFiles = self.browserFileList().reduce(function (accumulator, current) {
            if (current.selected()) {
                accumulator.push({
                    name: current.name(),
                    type: current.type()
                });
            }
            return accumulator;
        }, []);

        if (selectedFiles.length == 0) {
            $osf.growl('FTP', 'Please choose the file(s) to be copied.', 'danger');
            return false;
        }

        var selectedDestination = filebrowser.grid.multiselected()[0];
        if (!selectedDestination) {
            $osf.growl('FTP', 'Please choose a directory to save the file(s).', 'danger');
            return false;
        }

        var hostArr = self.host().split(':');
        var host = hostArr[0];
        var port = hostArr[1];

        $.ajax({
            url: url + 'download/',
            type: 'POST',
            data: ko.toJSON({
                protocol: self.protocol,
                host: host,
                port: port,
                username: self.username,
                password: self.password,
                passMethod: self.passMethod,
                key: self.key,
                path: self.browserPath,
                files: selectedFiles,
                destPid: selectedDestination.data.nodeId,
                destFolderId: selectedDestination.data.id
            }),
            contentType: 'application/json',
            dataType: 'json',
            success: function (response) {
                if (response.status == 'OK') {
                    $osf.growl('FTP', response.message, 'success');
                    itemsToRefresh.push(filebrowser.grid.multiselected()[0]);
                    setTimeout(function () {
                        refreshItems(itemsToRefresh);
                    }, 2000);
                } else {
                    $osf.growl('FTP', response.message, 'danger');
                }
            },
            error: function () {
                $osf.growl('FTP', 'There was an error while processing your request.', 'danger');
            }
        });
    };

    self.cancel = function () {
        $.ajax({
            url: url + 'cancel/',
            type: 'POST',
            success: function (response) {
                $osf.growl('FTP', response.message, response.status == 'OK' ? 'success' : 'danger');
            },
            error: function () {
                $osf.growl('FTP', 'There was an error while processing your request.', 'danger');
            }
        });
    };

    self.refresh = function () {
        var selectedItem = filebrowser.grid.multiselected()[0];
        if (selectedItem) {
            refreshItems([selectedItem]);
        }
        refreshItems(itemsToRefresh);
    };

    var retrieveFiles = function (path, info, success, fail) {
        var hostArr = self.host().split(':');
        var host = hostArr[0];
        var port = hostArr[1];

        $.ajax({
            url: url + 'list/',
            type: 'POST',
            data: ko.toJSON({
                protocol: self.protocol,
                host: host,
                port: port,
                username: self.username,
                password: self.password,
                passMethod: self.passMethod,
                key: self.key,
                path: path,
                info: info
            }),
            contentType: 'application/json',
            dataType: 'json',
            success: function (response) {
                if (response.status == 'OK') {
                    updateFileList(response.file_list, path);
                    success();
                } else {
                    $osf.growl('FTP', response.status, 'danger');
                    fail();
                }
            },
            error: function () {
                $osf.growl('FTP', 'There was an error while processing your request.', 'danger');
                if (fail) {
                    fail();
                }
            }
        });
    };

    var updateFileList = function (fileList, path) {
        self.browserFileList([]);

        if (path !== '/') {
            self.browserFileList.push(new NodeViewModel({
                type: 'back',
                name: 'Parent directory',
                size: 0
            }));
        }

        for (var i = 0; i < fileList.length; i++) {
            self.browserFileList.push(new NodeViewModel({
                type: fileList[i].is_directory ? 'folder' : 'file',
                name: fileList[i].filename,
                size: fileList[i].size
            }));
        }

        $('#ftpScope #ftp-browser .tb-header-row').css('visibility', 'visible');
        self.browserPath(path);
        self.connected(true);
    };
}

function refreshItems(items) {
    var item;
    for (var i = 0; i < items.length; i++) {
        item = items[i];
        var icon = $('.tb-row[data-id="' + item.id + '"]').find('.tb-toggle-icon');
        if (icon.get(0)) {
            m.render(icon.get(0), filebrowser.options.resolveRefreshIcon());
        }
        $osf.ajaxJSON(
            'GET',
            '/api/v1/project/' + item.data.nodeId + '/files/grid/'
        ).done(function(response) {
            var data = response.data[0].children;
            filebrowser.grid.updateFolder(data, item);
            filebrowser.grid.redraw();
        }).fail(function(xhr) {
            item.notify.update('Unable to retrieve components.', 'danger', undefined, 3000);
            item.open = false;
            Raven.captureMessage('Unable to retrieve components for node ' + item.data.nodeID, {
                extra: {
                    xhr: xhr
                }
            });
        });
    }
}

function FtpWidget(selector, url) {
    var self = this;

    self.viewModel = new ViewModel(url);
    $osf.applyBindings(self.viewModel, selector);

    // Treebeard Files view
    var urlFilesGrid = nodeApiUrl + 'files/grid/';
    var promise = m.request({ method: 'GET', config: $osf.setXHRAuthorization, url: urlFilesGrid});
    promise.then(function (response) {
        var fangornOpts = {
            divID: 'ftpTreeGrid',
            filesData: response.data,
            allowMove: false,
            uploads: false,
            multiselect : true, // must be true to singleselect work
            singleselect : true,
            showFilter : false,
            toolbarComponent : {
                controller : function(args) {
                    var self = this;
                    self.tb = args.treebeard;
                    self.tb.toolbarMode = function () {};
                    self.items = args.treebeard.multiselected;
                    self.mode = self.tb.toolbarMode;
                    self.isUploading = args.treebeard.isUploading;
                    self.helpText = m.prop('');
                    self.dismissToolbar = function () {};
                    self.createFolder = function () {};
                    self.nameData = m.prop('');
                    self.renameId = m.prop('');
                    self.renameData = m.prop('');
                },
                view: function () {
                    return m('.no-tool-bar', []);
                }
            },
            placement: 'dashboard',
            title : undefined,
            xhrconfig: $osf.setXHRAuthorization,
            columnTitles : function () {
                return [
                    {
                        title: 'Name',
                        width : '70%',
                        sort : true,
                        sortType : 'text'
                    },
                    {
                        title: 'Modified',
                        width : '30%',
                        sort : true,
                        sortType : 'text'
                    }
                ];
            },
            resolveRows : function (item) {
                var tb = this;
                item.css = '';
                if (tb.isMultiselected(item.id)){
                    item.css = 'fangorn-selected';
                }
                if (item.data.permissions && !item.data.permissions.view){
                    item.css += ' tb-private-row';
                }
                var defaultColumns = [
                    {
                        data: 'name',
                        folderIcons: true,
                        filter: true,
                        custom: Fangorn.DefaultColumns._fangornTitleColumn},
                    {
                        data: 'modified',
                        folderIcons: false,
                        filter: false,
                        custom: Fangorn.DefaultColumns._fangornModifiedColumn
                    }];
                if (item.parentID) {
                    item.data.permissions = item.data.permissions || item.parent().data.permissions;
                    if (item.data.kind === 'folder') {
                        item.data.accept = item.data.accept || item.parent().data.accept;
                    }
                }
                if(item.data.uploadState && (item.data.uploadState() === 'pending' || item.data.uploadState() === 'uploading')){
                    return Fangorn.Utils.uploadRowTemplate.call(tb, item);
                }

                var configOption = Fangorn.Utils.resolveconfigOption.call(this, item, 'resolveRows', [item]);
                return configOption || defaultColumns;
            }
        };
        filebrowser = new Fangorn(fangornOpts);
        return promise;
    }, function(xhr, textStatus, error) {
        Raven.captureMessage('Error retrieving filebrowser', {extra: {url: urlFilesGrid, textStatus: textStatus, error: error}});
    });
}

module.exports = FtpWidget;
