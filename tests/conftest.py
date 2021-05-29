import atexit
import multiprocessing
from os import path
from typing import Dict, Any

import pytest

_local_directory = path.dirname(path.abspath(__file__))
_test_files_directory = path.join(_local_directory, "test_files")


def render(req_path):
    path_to_file = path.realpath(path.join(_test_files_directory, req_path))
    if not path_to_file.startswith(_test_files_directory):
        raise RuntimeError("Path outside of _test_files_directory")

    with open(path_to_file, "r") as f:
        return f.read()


def _render_multidict(multidict) -> Dict[str, Any]:
    data = dict(multidict)
    for fname, fvalues in multidict.lists():
        if len(fvalues) > 1:
            data[fname] = fvalues

    return data


class LocalWebServer:
    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()

    def __init__(self, port):
        self.port = port

    def _start_local(self, parent_pipe, host, port):
        import json

        import flask

        self._parent_pipe = parent_pipe
        self._local_web_server = flask.Flask(__name__)

        @self._local_web_server.route("/html/<name>")
        def page(name):
            return render(name)

        @self._local_web_server.route("/form/<name>", methods=["GET", "POST"])
        def form(name):
            req = flask.request
            if req.method == "POST":
                data = _render_multidict(req.form)
                return (json.dumps(data), 200, {"Content-Type": "application/json"})
            else:
                return render(name)

        @self._local_web_server.route("/status")
        def status():
            return ""

        @self._local_web_server.route("/json")
        def json_request():
            req = flask.request
            return (
                json.dumps(_render_multidict(req.args)),
                200,
                {"Content-Type": "application/json"},
            )

        @self._local_web_server.route("/csv")
        def csv_document():
            return ("Col1,Col2\nVal1,Val2", 200, {"Content-Type": "text/csv"})

        self._local_web_server.run(host=host, port=port)

    def _await_remote_server_up(self, timeout):
        import time

        import requests

        for _ in range(timeout):
            try:
                if not self._serverthread.is_alive():
                    pytest.fail("Stub HTTP Server terminated unexpectedly")

                if requests.get(
                    "http://localhost:{port}/status".format(port=self.port)
                ).status_code in range(200, 300):
                    return
            except Exception as e:
                print(e)
                pass
            time.sleep(1)

        pytest.fail(
            "Timed out waiting {timeout} seconds for local web server to start".format(
                timeout=timeout
            )
        )

    def start_remote(self, timeout=10):
        self._remote_pipe = multiprocessing.Pipe()

        self._serverthread = multiprocessing.Process(
            target=self._start_local,
            kwargs={
                "parent_pipe": self._remote_pipe,
                "host": "127.0.0.1",
                "port": self.port,
            },
        )

        self._serverthread.start()
        atexit.register(self.stop)
        self._await_remote_server_up(timeout)

    def stop(self):
        self._serverthread.terminate()
        self._serverthread.join()

    def serve_forever(self):
        self.start_remote()
        try:
            self._serverthread.join()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()


@pytest.fixture(scope="session")
def localwebserver(request):
    lws = LocalWebServer(port=60123)
    request.addfinalizer(lws.stop)
    lws.start_remote()
    return lws


if __name__ == "__main__":
    with LocalWebServer(port=60123) as lws:
        lws.serve_forever()
