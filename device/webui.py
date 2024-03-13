import logging
import json
import asyncio

import tinyweb
from config import Configuration

_logger = logging.getLogger(__name__)
_app = tinyweb.webserver()
_shutdown_event = asyncio.Event()


# Gzipped css resources
@_app.route("/css/<fn>")
async def _files_css(req, resp, fn):
    await resp.send_file(
        "static/css/{}".format(fn),
        content_type="test/css",
        content_encoding="gzip",
    )

class _Configuration:
    def get(self, data, name) -> dict:
        return Configuration.load(f"{name}").json_obj

    def post(self, data, name) -> None:
        Configuration(json.loads(data['textarea-configuration'])).save(f"{name}")
        return {"locations": ["/", f"api/v1/configurations/{name}"]}, 300


# Index page
@_app.route("/")
async def _index(request: tinyweb.request, response: tinyweb.response):
    with open("static/index.html", "r") as f:
        await response.start_html()
        for line in f:
            line = line.strip()
            if line == "{:config}":
                line = json.dumps(_Configuration().get({}, Configuration.default_config_name))
            await response.send(line)



@_app.route("/shutdown")
async def _shutdown(_, response: tinyweb.response):
    await response.send_file("static/shutdown.html")
    _shutdown_event.set()


async def serve(host="0.0.0.0", port=80):
    _logger.info("Starting...")
    _app.add_resource(_Configuration, "/api/v1/configurations/<name>")
    _app.run(host=host, port=port, loop_forever=False)
    await _shutdown_event.wait()
    _app.shutdown()
    _logger.info("Shutdown")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(serve(port=8081))
