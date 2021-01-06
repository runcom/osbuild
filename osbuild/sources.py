import json
import os
import subprocess
import sys
from . import api
from .util import jsoncomm


class SourcesServer(api.BaseAPI):

    endpoint = "sources"

    def __init__(self, libdir, options, cache, output, *, socket_address=None):
        super().__init__(socket_address)
        self.libdir = libdir
        self.cache = cache
        self.output = output
        self.options = options or {}

    def _run_source(self, source, checksums):
        msg = {
            "options": self.options.get(source, {}),
            "cache": f"{self.cache}/{source}",
            "output": f"{self.output}/{source}",
            "checksums": checksums,
            "libdir": self.libdir
        }

        r = subprocess.run(
            [f"{self.libdir}/sources/{source}"],
            input=json.dumps(msg),
            stdout=subprocess.PIPE,
            encoding="utf-8",
            check=False)

        try:
            return json.loads(r.stdout)
        except ValueError:
            return {"error": f"source returned malformed json: {r.stdout}"}

    def _message(self, msg, fds, sock):
        reply = self._run_source(msg["source"], msg["checksums"])
        sock.send(reply)


def get(source, checksums, api_path="/run/osbuild/api/sources"):
    with jsoncomm.Socket.new_client(api_path) as client:
        msg = {
            "source": source,
            "checksums": checksums
        }
        client.send(msg)
        reply, _, _ = client.recv()
        if "error" in reply:
            raise RuntimeError(f"{source}: " + reply["error"])
        return reply


def download(store, libdir, sources_options):
    for source, options in sources_options.items():
        cache = os.path.join(store.store, "sources", source)

        msg = {
            "options": options,
            "cache": cache,
            "output": None,
            "checksums": [],
            "libdir": libdir
        }

        r = subprocess.run(
            [f"{libdir}/sources/{source}", "--fetch-only"],
            input=json.dumps(msg),
            stdout=subprocess.PIPE,
            encoding="utf-8",
            check=False)

        try:
            reply = json.loads(r.stdout)
        except ValueError:
            return {"error": f"source returned malformed json: {r.stdout}"}

        if "error" in reply:
            raise RuntimeError(f"{source}: " + reply["error"])

        if r.returncode != 0:
            raise RuntimeError(f"{source}: error {r.returncode}")
