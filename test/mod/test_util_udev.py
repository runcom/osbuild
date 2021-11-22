#
# Test for the util.udev module
#

from tempfile import TemporaryDirectory

import pytest

from osbuild.util.udev import UdevLock


@pytest.fixture(name="tempdir")
def tempdir_fixture():
    with TemporaryDirectory(prefix="udev-") as tmp:
        yield tmp


def test_udev_locking(tempdir):
    lock = UdevLock.lock_dm_name("test", lockdir=tempdir)
    assert lock.locked

    lock.unlock()
    assert not lock.locked
