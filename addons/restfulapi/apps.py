from addons.base.apps import BaseAddonAppConfig


class RestfulapiAddonAppConfig(BaseAddonAppConfig):

    name = 'addons.restfulapi'
    label = 'addons_restfulapi'
    full_name = 'RESTful API'
    short_name = 'restfulapi'
    owners = ['node']
    added_default = ['node']
    added_mandatory = []
    views = ['widget']
    configs = []
    categories = ['other']
    include_js = {
        'widget': [],
    }
    include_css = {
        'widget': [],
    }

    @property
    def routes(self):
        from . import routes
        return [routes.widget_routes, routes.api_routes]

    @property
    def node_settings(self):
        return self.get_model('NodeSettings')
