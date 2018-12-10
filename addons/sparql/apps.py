from addons.base.apps import BaseAddonAppConfig


class SparqlAddonAppConfig(BaseAddonAppConfig):

    name = 'addons.sparql'
    label = 'addons_sparql'
    full_name = 'SPARQL'
    short_name = 'sparql'
    owners = ['node']
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
