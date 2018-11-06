from addons.base.apps import BaseAddonAppConfig


class FtpAddonAppConfig(BaseAddonAppConfig):

    name = 'addons.ftp'
    label = 'addons_ftp'
    full_name = 'FTP'
    short_name = 'ftp'
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
