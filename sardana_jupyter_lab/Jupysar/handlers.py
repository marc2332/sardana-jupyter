import json

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado

class RouteHandler(APIHandler):
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "data": "This is /Jupysar/get_example endpoint"
        }))

def setup_handlers(web_app):
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]

    route_pattern_exemple = url_path_join(base_url, "Jupysar", "get_example")

    handlers = [(route_pattern_exemple, RouteHandler)]

    web_app.add_handlers(host_pattern, handlers)
