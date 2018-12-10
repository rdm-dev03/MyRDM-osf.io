var SparqlWidget = require('./js/sparqlWidget.js');


var url = window.contextVars.node.urls.api + 'sparql/';
// #sparqlScope will only be in the DOM if the addon is properly configured
if ($('#sparqlScope')[0]) {
    new SparqlWidget('#sparqlScope', url);
}
