var RestfulapiWidget = require('./js/restfulapiWidget.js');


var url = window.contextVars.node.urls.api + 'restfulapi/';
// #restfulapiScope will only be in the DOM if the addon is properly configured
if ($('#restfulapiScope')[0]) {
    new RestfulapiWidget('#restfulapiScope', url);
}
