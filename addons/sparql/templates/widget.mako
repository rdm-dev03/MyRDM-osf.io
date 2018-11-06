<div id="sparqlScope">
    <form>
        <div class="row form-group">

            <label for="url" class="col-xs-2 col-form-label" style="margin-top: 5px;">URL</label>
            <div class="col-xs-10">
                <input data-bind="value: url" type="text" class="form-control" id="url" placeholder="SPARQL endpoint URL">
            </div>

        </div>
        <div class="row form-group">

            <label for="query" class="col-xs-2 col-form-label" style="margin-top: 5px;">Query</label>
            <div class="col-xs-10">
                <textarea data-bind="value: query" class="form-control" rows="10" id="query" placeholder="" style="resize: vertical; min-height: 100px; max-height: 800px;"></textarea>
            </div>

        </div>
        <div class="row form-group">
            <div class="col-xs-2" style="margin-top: 5px; padding-right: 0;">
                <label for="fileSelect">File Format</label>
            </div>
            <div class="col-xs-10">
                <select data-bind="value: format" class="form-control" id="fileSelect">
                    <option value="html">HTML</option>
                    <option value="html (basic browsing links)">HTML (Basic Browsing Links)</option>
                    <option value="spreadsheet">Spreadsheet</option>
                    <option value="xml">XML</option>
                    <option value="json">JSON</option>
                    <option value="javascript">Javascript</option>
                    <option value="turtle">Turtle</option>
                    <option value="rdf/xml">RDF/XML</option>
                    <option value="n-triples">N-Triples</option>
                    <option value="csv">CSV</option>
                    <option value="tsv">TSV</option>
                </select>
            </div>
        </div>

        <div class="row form-group">
            <div class="col-xs-2" style="margin-top: 5px;">
                <label for="limitSelect">LIMIT</label>
            </div>
            <div class="col-xs-4">
                <select data-bind="value: limit" class="form-control" id="limitSelect">
                    <option value="5">5</option>
                    <option value="10">10</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                    <option value="">No Limit</option>
                </select>
            </div>
        </div>

        <div class="pull-right">
            <button data-bind="click: runQuery" class="btn btn-sm btn-default" type="button">Run Query</button>
        </div>

    </form>
</div>

<%def name="javascript_bottom()">
    ${parent.javascript_bottom()}
    <script type="text/javascript" src=${"/static/public/js/sparql/widget-cfg.js" | webpack_asset}></script>
</%def>
