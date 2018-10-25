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


function ViewModel(url) {
    var self = this;

    self.url = ko.observable('');
    self.recursive = ko.observable(false);
    self.interval = ko.observable(false);
    self.intervalValue = ko.observable(3000);

    self.cancel = function () {
        $.ajax({
            url: url + 'cancel/',
            type: 'POST',
            success: function (response) {
                $osf.growl('RESTfulAPI', response.message, response.status == 'OK' ? 'success' : 'danger');
            },
            error: function () {
                $osf.growl('RESTfulAPI', 'There was an error while processing your request.', 'danger');
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

    self.submit = function () {
        if (!self.url()) {
            $osf.growl('RESTfulAPI', 'Please type the URL.', 'danger');
            return false;
        }

        var selectedItem = filebrowser.grid.multiselected()[0];
        if (!selectedItem) {
            $osf.growl('RESTfulAPI', 'Please choose a directory to save the file(s).', 'danger');
            return false;
        }

        $.ajax({
            url: url + 'download/',
            type: 'POST',
            data: ko.toJSON(
                $.extend({
                    'pid': selectedItem.data.nodeId,
                    'folderId': selectedItem.data.id
                }, self)
            ),
            contentType: 'application/json',
            dataType: 'json',
            success: function (response) {
                if (response.status == 'OK') {
                    $osf.growl('RESTfulAPI', 'File is being uploaded to storage!', 'success');
                    itemsToRefresh.push(filebrowser.grid.multiselected()[0]);
                    setTimeout(function () {
                        refreshItems(itemsToRefresh);
                    }, 2000);
                } else {
                    $osf.growl('RESTfulAPI', response['message'], 'danger');
                }
            },
            error: function () {
                $osf.growl('RESTfulAPI', 'There was an error while processing your request.', 'danger');
            }
        });
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


function RestfulapiWidget(selector, url) {
    var self = this;
    self.viewModel = new ViewModel(url);
    $osf.applyBindings(self.viewModel, selector);

    // Treebeard Files view
    var urlFilesGrid = nodeApiUrl + 'files/grid/';
    var promise = m.request({ method: 'GET', config: $osf.setXHRAuthorization, url: urlFilesGrid});
    promise.then(function (response) {
        var fangornOpts = {
            divID: 'restfulapiTreeGrid',
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
                if(tb.isMultiselected(item.id)){
                    item.css = 'fangorn-selected';
                }
                if(item.data.permissions && !item.data.permissions.view){
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

module.exports = RestfulapiWidget;
