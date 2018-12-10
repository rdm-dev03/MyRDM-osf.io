var FtpWidget = require('./js/ftpWidget.js');

var url = window.contextVars.node.urls.api + 'ftp/';
// #ftpScope will only be in the DOM if the addon is properly configured
if ($('#ftpScope')[0]) {
    new FtpWidget('#ftpScope', url);
}

