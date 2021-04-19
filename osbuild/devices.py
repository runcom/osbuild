"""
Device Handling for pipeline stages
"""

import hashlib
import importlib
import json
import os
import subprocess


from typing import Dict, Tuple


class Device:
    """
    TODO
    """

    def __init__(self, info, options: Dict):
        self.info = info
        self.options = options or {}
        self.id = self.calc_id()

    @property
    def name(self) -> str:
        return self.info.name

    def calc_id(self):
        m = hashlib.sha256()
        m.update(json.dumps(self.name, sort_keys=True).encode())
        m.update(json.dumps(self.options, sort_keys=True).encode())
        return m.hexdigest()

    def run(self, buildroot: "BuildRoot", tree: str) -> Tuple[Dict]:
        name = self.info.name
        msg = {
            # global options
            "dev": buildroot.dev,
            "tree": tree,

            # per device options
            "options": self.options,
        }

        # We want the `osbuild` python package that contains this
        # very module, which might be different from the system wide
        # installed one, to be accessible to the Input programs so
        # we detect our origin and set the `PYTHONPATH` accordingly
        modorigin = importlib.util.find_spec("osbuild").origin
        modpath = os.path.dirname(modorigin)
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(modpath)

        r = subprocess.run([self.info.path, "open"],
                           env=env,
                           input=json.dumps(msg),
                           stdout=subprocess.PIPE,
                           encoding="utf-8",
                           check=False)

        try:
            reply = json.loads(r.stdout)
        except ValueError:
            raise RuntimeError(f"{name}: error: {r.stderr}") from None

        if "error" in reply:
            raise RuntimeError(f"{name}: " + reply["error"])

        if r.returncode != 0:
            raise RuntimeError(f"{name}: error {r.returncode}")

        buildroot.atclose(lambda: self.close(reply))

        return reply

    def close(self, options):
        name = self.info.name
        msg = {
            # open device options
            "options": options,
        }

        # We want the `osbuild` python package that contains this
        # very module, which might be different from the system wide
        # installed one, to be accessible to the Input programs so
        # we detect our origin and set the `PYTHONPATH` accordingly
        modorigin = importlib.util.find_spec("osbuild").origin
        modpath = os.path.dirname(modorigin)
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(modpath)

        r = subprocess.run([self.info.path, "close"],
                           env=env,
                           input=json.dumps(msg),
                           stdout=subprocess.PIPE,
                           encoding="utf-8",
                           check=False)

        try:
            reply = json.loads(r.stdout)
        except ValueError:
            raise RuntimeError(f"{name}: error: {r.stderr}") from None

        if "error" in reply:
            raise RuntimeError(f"{name}: " + reply["error"])

        if r.returncode != 0:
            raise RuntimeError(f"{name}: error {r.returncode}")
