"""
Mount Handling for pipeline stages
"""

import hashlib
import json
import os
import subprocess


from typing import Dict, Tuple


class Mount:
    """
    TODO
    """

    def __init__(self, device, target):
        self.device = device
        self.target = target
        self.id = self.calc_id()

        self._mountpoint = None

    def calc_id(self):
        m = hashlib.sha256()
        m.update(json.dumps(self.device, sort_keys=True).encode())
        m.update(json.dumps(self.target, sort_keys=True).encode())
        return m.hexdigest()

    def mount(self, root, device) -> Tuple[Dict]:
        assert self._mountpoint is None

        mountpoint = os.path.join(root, self.target.lstrip("/"))
        args = []
        os.makedirs(mountpoint, exist_ok=True)
        subprocess.run(["mount"] + args + [device, mountpoint],
                       check=True)
        self._mountpoint = mountpoint

    def umount(self):
        if not self._mountpoint:
            return

        assert self._mountpoint is not None
        print(f"umounting {self.target}")
        subprocess.run(["umount", self._mountpoint],
                       check=True)
        self._mountpoint = None
