'use strict'
var $ = require('jquery');
var ko = require('knockout');
var $osf = require('js/osfHelpers');


function ViewModel(url) {
    var self = this;

    self.url = ko.observable('http://ja.dbpedia.org');
    self.query = ko.observable('select distinct * where { <http://ja.dbpedia.org/resource/東京都> ?p ?o .  }');
    self.limit = ko.observable(10);
    self.format = ko.observable('html');

    self.runQuery = function () {
        var newWindow;

        $.ajax({
            url: url,
            type: 'POST',
            data: ko.toJSON(self),
            contentType: 'application/json',
            dataType: 'json',
            success: function (response) {
                if (response.status_code == 200) {
                    if (self.format() == 'html') {
                        newWindow = window.open('SPARQL Query preview');
                        newWindow.document.write(response.text);
                    } else {
                        $osf.growl('Sparql', 'The query result is being saved to storage.', 'success');
                    }
                } else {
                    $osf.growl('Sparql', 'There was an error while processing your request.', 'danger');
                }
            },
            error: function () {
                $osf.growl('Sparql', 'There was an error while processing your request.', 'danger');
            }
        });
    };
}

function SparqlWidget(selector, url) {
    var self = this;
    self.viewModel = new ViewModel(url);
    $osf.applyBindings(self.viewModel, selector);
}

module.exports = SparqlWidget;
