#
# Tests for the `osbuild.util.osrelease` module.
#

import os
import unittest

from osbuild.util import osrelease


class TestUtilOSRelease(unittest.TestCase):
    def test_non_existant(self):
        """Verify default os-release value, if no files are given."""
        self.assertEqual(osrelease.describe_os(), "linux")

    def test_describe_os(self):
        """Test host os detection. test/os-release contains the os-release files
        for all supported runners.
        """
        for entry in os.scandir("test/os-release"):
            with self.subTest(entry.name):
                self.assertEqual(osrelease.describe_os(entry.path), entry.name)