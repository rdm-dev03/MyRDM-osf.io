<div id="ftpScope">

    <form>
        <div class="row form-group">
            <label class="col-xs-2 col-form-label">Protocol</label>
            <div class="col-xs-10">
                <label class="radio-inline"><input data-bind="checked: protocol, enable: !connected()" type="radio" name="protocol" value="ftp">FTP </label>
                <label class="radio-inline"><input data-bind="checked: protocol, enable: !connected()" type="radio" name="protocol" value="ftps">FTPS </label>
                <label class="radio-inline"><input data-bind="checked: protocol, enable: !connected()" type="radio" name="protocol" value="sftp">SFTP </label>
            </div>
        </div>

        <div class="row form-group">
            <label for="host" class="col-xs-2 col-form-label" style="margin-top: 5px;">Host</label>
            <div class="col-xs-10">
                <input data-bind="value: host, enable: !connected()" type="text" class="form-control" placeholder="mytcpserver.com:21">
            </div>
        </div>

        <div class="row form-group">
            <label for="user" class="col-xs-2 col-form-label" style="margin-top: 5px;">User</label>
            <div class="col-xs-10">
                <input data-bind="value: username, enable: !connected()" type="text" class="form-control" placeholder="username">
            </div>
        </div>

        <div class="row form-group">
            <label for="passphrase" class="col-xs-2 col-form-label" style="margin-top: 5px;">Passphrase</label>
            <div class="col-xs-10">
                <input data-bind="value: password, enable: !connected()" type="password" class="form-control" placeholder="secret">
            </div>
        </div>

        <div class="row">
            <div class="col-xs-12">
                <label><input data-bind="checked: passMethod, enable: !connected()" type="radio" name="passMethod" value="plaintext"> Plaintext</label>
            </div>
        </div>

        <div class="row">
            <div class="col-xs-12">
                <label><input data-bind="checked: passMethod, enable: !connected()" type="radio" name="passMethod" value="key"> RSA/DSA keys</label>
            </div>
        </div>

        <div class="row form-group">
            <div class="col-xs-12">
                <input data-bind="event: { change: function () { loadFile($element.files[0]) } }, enable: !connected() && passMethod() == 'key'" type="file" class="form-control-file">
            </div>
        </div>

        <div class="row form-group" style="margin-bottom: 5px;">
            <div class="col-xs-12">
                <div class="pull-right">
                    <button data-bind="click: disconnect, enable: connected()" class="btn btn-sm btn-default" type="button">Disconnect</button>
                    <button data-bind="click: connect, enable: !connected()" class="btn btn-sm btn-default" type="button">Connect</button>
                </div>
            </div>
        </div>

        <label style="margin-top: 5px;">Remote</label>
        <div class="row form-group">
            <div class="col-xs-12">

                <div data-bind="visible: connecting()" class="spinner-loading-wrapper">
                    <div class="logo-spin logo-lg"></div>
                    <p class="m-t-sm fg-load-message">Connecting ...</p>
                </div>

                <div data-bind="visible: !connecting()" id="ftp-browser">
                    <div class="row tb-header-row" style="visibility: hidden;">
                        <span style="font-weight: bold; margin: 6px;">Path:</span>
                        <span data-bind="text: browserPath"></span>
                    </div>

                    <div data-bind="foreach: browserFileList" id="ftp-browser-listing">
                        <div data-bind="css: { 'selected-node': selected() }, click: $root.selectNode" class="tb-row">

                            <span class="clickable" data-bind="visible: type() == 'back', click: $root.changeFolder, clickBubble: false">
                                <span class="tb-td-first">
                                    <span class="tb-expand-icon-holder clickable">
                                        <i class="fa fa-arrow-left"> </i>
                                    </span>
                                </span>
                                <span data-bind="text: name"></span>
                            </span>

                            <span class="clickable" data-bind="visible: type() == 'folder', click: $root.changeFolder, clickBubble: false">
                                <span class="tb-td-first">
                                    <span class="tb-expand-icon-holder clickable">
                                        <i class="fa fa-folder"> </i>
                                    </span>
                                </span>
                                <span data-bind="text: name"></span>
                            </span>

                            <span data-bind="visible: type() == 'file'">
                                <span class="tb-td-first">
                                    <span class="tb-expand-icon-holder">
                                        <div class="file-extension _txt"></div>
                                    </span>
                                </span>
                                <span data-bind="text: name" style="cursor: default;"></span>
                            </span>

                        </div>
                    </div>

                </div>
            </div>
        </div>

        <label style="margin-top: 5px;">Files</label>
        <div class="row form-group">
            <div class="col-xs-12">
                <div id="ftpTreeGrid">
                    <div class="spinner-loading-wrapper">
                        <div class="logo-spin logo-lg"></div>
                        <p class="m-t-sm fg-load-message"> Loading files...  </p>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-xs-12">
                <div class="pull-right">
                    <button data-bind="click: cancel" class="btn btn-sm btn-default" type="button">Cancel</button>
                    <button data-bind="click: refresh" class="btn btn-sm btn-default" type="button">Refresh</button>
                    <button data-bind="click: download, enable: connected()" class="btn btn-sm btn-default" type="button">Download</button>
                </div>
            </div>
        </div>
    </form>
</div>

<style type="text/css">
#ftpScope .spinner-loading-wrapper {
    border: 1px solid #CCC;
    height: 245px;
    padding-top: 80px;
}

#ftp-browser {
    border: 1px solid #CCC;
}

#ftp-browser .clickable {
    cursor: pointer;
}

#ftp-browser .tb-header-row {
    padding: 6px;
    margin: 0;
    border-bottom: #CCC solid 1px;
}

#ftp-browser .tb-row {
    padding: 4px 8px;
}

#ftp-browser .tb-row:hover {
    background: #E0EBF3;
}

#ftp-browser .tb-row.selected-node {
    background: #337AB7;
    color: #FFF;
}

#ftp-browser .tb-row.selected-node:hover {
    background: #337AB7;
}

#ftp-browser-listing {
    height: 210px;
    overflow-y: auto;
}
</style>
