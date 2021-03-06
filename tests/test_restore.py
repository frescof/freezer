"""Freezer restore.py related tests

Copyright 2014 Hewlett-Packard

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This product includes cryptographic software written by Eric Young
(eay@cryptsoft.com). This product includes software written by Tim
Hudson (tjh@cryptsoft.com).
========================================================================

"""
import unittest

from freezer import restore
import commons


class TestRestore(unittest.TestCase):

    def test_restore_cinder_by_glance(self):
        backup_opt = commons.BackupOpt1()
        ros = restore.RestoreOs(backup_opt.client_manager, backup_opt.container)
        ros.restore_cinder_by_glance(35, 34)

    def test_restore_cinder(self):
        backup_opt = commons.BackupOpt1()
        ros = restore.RestoreOs(backup_opt.client_manager, backup_opt.container)
        ros.restore_cinder(35, 34)

    def test_restore_nova(self):
        backup_opt = commons.BackupOpt1()
        ros = restore.RestoreOs(backup_opt.client_manager, backup_opt.container)
        ros.restore_nova(35, 34)
