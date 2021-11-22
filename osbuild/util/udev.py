"""userspace /dev device manager (udev) utilities"""

import os
import pathlib


class UdevLock:
    """Lock udev block devices via a custom locking mechanism

    This utility emulates systemd's Locking Block Device Access
    mechanism (see [1]) for devices that do not support it,
    like Device Mapper based devices such as luks2 devices.

    This is the osbuild side of the custom mechanism, which
    creates a lock file for the device that should be locked.
    A custom udev rule set[2] checks for the said lock file
    and opts out of certain further processing rules. See the
    aforementioned rules file for more information.

    [1] https://systemd.io/BLOCK_DEVICE_LOCKING/
    [2] 10-osbuild-lock.rules
    """

    def __init__(self, path: pathlib.Path):
        self.path = path

    def lock(self) -> None:
        self.path.touch()

    def unlock(self) -> None:
        self.path.unlink()

    @property
    def locked(self) -> bool:
        return self.path.exists()

    @classmethod
    def lock_dm_name(cls, name, lockdir="/run/osbuild/locks"):
        """Lock a Device Mapper device with the given name"""
        os.makedirs(lockdir, exist_ok=True)
        path = pathlib.Path(lockdir, f"dm-{name}")
        lock = cls(path)
        lock.lock()
        return lock
