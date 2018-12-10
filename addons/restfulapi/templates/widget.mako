<div id="restfulapiScope">
    <div class="form-group row">
        <label class="col-xs-2" for="restfulapi-url">URL</label>
        <div class="col-xs-10">
            <input data-bind="value: url" class="form-control" type="text" id="restfulapi-url" placeholder="example.com" />
        </div>
    </div>
    <div class="form-group row">
        <label class="col-xs-2">Options</label>
        <div class="col-xs-3">
            <input data-bind="checked: recursive" class="form-check-input" type="checkbox" id="recursive" name="option" value="recursive" />
            <label for="recursive" style="font-weight: 500;">Recursive (-r)</label>
        </div>
        <div class="col-xs-6">
            <input data-bind="checked: interval" type="checkbox" id="interval" name="option" value="interval" />
            <label for="interval" style="font-weight: 500;">Interval (-w)</label>
            <select data-bind="value: intervalValue, enable: interval" name="intervalValue" id="intervalValue" style="margin-left: 6px;">
                <option value="3.0">3.0</option>
                <option value="1.0">1.0</option>
                <option value="0.5">0.5</option>
                <option value="0.1">0.1</option>
            </select>
            <label data-bind="style: { color: interval() ? '' : '#888' }" style="font-weight: 500;">second(s)</label>
        </div>
    </div>
    <label style="margin-top: 5px;">Files</label>
    <div class="row form-group">
        <div class="col-xs-12">
            <div id="restfulapiTreeGrid">
                <div class="spinner-loading-wrapper">
                    <div class="logo-spin logo-lg"></div>
                    <p class="m-t-sm fg-load-message"> Loading files...  </p>
                </div>
            </div>
        </div>
    </div>
    <div class="pull-right" style="margin-top: 10px;">
        <button data-bind="click: cancel" class="btn btn-sm btn-default" type="button">Cancel</button>
        <button data-bind="click: refresh" class="btn btn-sm btn-default" type="button">Refresh</button>
        <button data-bind="click: submit" class="btn btn-sm btn-default" type="button">Submit</button>
    </div>
</div>

<%def name="javascript_bottom()">
    ${parent.javascript_bottom()}
    <script type="text/javascript" src=${"/static/public/js/restfulapi/widget-cfg.js" | webpack_asset}></script>
</%def>
