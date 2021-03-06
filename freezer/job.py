"""
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

import sys

from freezer import utils
from freezer import backup
from freezer import exec_cmd
from freezer import restore
from freezer import tar
from freezer import winutils
import os

import logging


class Job:
    """
    :type storage: freezer.storage.Storage
    """

    def __init__(self, conf_dict):
        self.conf = conf_dict
        self.storage = conf_dict.storage

    def execute(self):
        logging.info('[*] Action not implemented')

    def get_metadata(self):
        return None

    @staticmethod
    def executemethod(func):
        def wrapper(self):
            self.start_time = utils.DateTime.now()
            logging.info('[*] Job execution Started at: {0}'.
                         format(self.start_time))

            retval = func(self)

            end_time = utils.DateTime.now()
            logging.info('[*] Job execution Finished, at: {0}'.
                         format(end_time))
            logging.info('[*] Job time Elapsed: {0}'.
                         format(end_time - self.start_time))
            return retval
        return wrapper


class InfoJob(Job):
    @Job.executemethod
    def execute(self):
        self.storage.info()


class BackupJob(Job):
    @Job.executemethod
    def execute(self):
        try:
            (out, err) = utils.create_subprocess('sync')
            if err:
                logging.error('Error while sync exec: {0}'.format(err))
        except Exception as error:
            logging.error('Error while sync exec: {0}'.format(error))
        self.conf.storage.prepare()

        if self.conf.mode == 'fs':
            backup.backup(self.conf, self.storage)
        elif self.conf.mode == 'mongo':
            backup.backup_mode_mongo(self.conf)
        elif self.conf.mode == 'mysql':
            backup.backup_mode_mysql(self.conf)
        elif self.conf.mode == 'sqlserver':
            backup.backup_mode_sql_server(self.conf)
        else:
            raise ValueError('Please provide a valid backup mode')

    def get_metadata(self):
        metadata = {
            'current_level': self.conf.curr_backup_level,
            'fs_real_path': (self.conf.lvm_auto_snap or
                             self.conf.path_to_backup),
            'vol_snap_path':
                self.conf.path_to_backup if self.conf.lvm_auto_snap else '',
            'client_os': sys.platform,
            'client_version': self.conf.__version__
        }
        fields = ['action', 'always_level', 'backup_media', 'backup_name',
                  'container', 'container_segments', 'curr_backup_level',
                  'dry_run', 'hostname', 'path_to_backup', 'max_level',
                  'mode', 'meta_data_file', 'backup_name', 'hostname',
                  'time_stamp', 'curr_backup_level']
        for field_name in fields:
            metadata[field_name] = self.conf.__dict__.get(field_name, '')
        return metadata


class RestoreJob(Job):
    @Job.executemethod
    def execute(self):
        conf = self.conf
        logging.info('[*] Executing FS restore...')
        restore_timestamp = None
        if conf.restore_from_date:
            restore_timestamp = utils.date_to_timestamp(conf.restore_from_date)
        restore_abs_path = conf.restore_abs_path
        if conf.backup_media == 'fs':
            builder = tar.TarCommandRestoreBuilder(conf.tar_path,
                                                   restore_abs_path)
            if conf.dry_run:
                builder.set_dry_run()
            if winutils.is_windows():
                builder.set_windows()
                os.chdir(conf.restore_abs_path)
            if conf.encrypt_pass_file:
                builder.set_encryption(conf.openssl_path,
                                       conf.encrypt_pass_file)

            conf.storage.restore_from_date(conf.hostname_backup_name,
                                           restore_abs_path,
                                           builder,
                                           restore_timestamp)
            return

        res = restore.RestoreOs(conf.client_manager, conf.container)
        if conf.backup_media == 'nova':
            res.restore_nova(conf.nova_inst_id, restore_timestamp)
        elif conf.backup_media == 'cinder':
            res.restore_cinder_by_glance(conf.cinder, restore_timestamp)
        elif conf.backup_media == 'cindernative':
            res.restore_cinder(conf.cinder_vol_id, restore_timestamp)
        else:
            raise Exception("unknown backup type: %s" % conf.backup_media)


class AdminJob(Job):
    @Job.executemethod
    def execute(self):
        timestamp = utils.date_to_timestamp(self.conf.remove_from_date)
        self.storage.remove_older_than(timestamp,
                                       self.conf.hostname_backup_name)


class ExecJob(Job):
    @Job.executemethod
    def execute(self):
        logging.info('[*] exec job....')
        if self.conf.command:
            logging.info('[*] Executing exec job....')
            exec_cmd.execute(self.conf.command)
        else:
            logging.warning(
                '[*] No command info options were set. Exiting.')
            return False
        return True


def create_job(conf):
    if conf.action == 'backup':
        return BackupJob(conf)
    if conf.action == 'restore':
        return RestoreJob(conf)
    if conf.action == 'info':
        return InfoJob(conf)
    if conf.action == 'admin':
        return AdminJob(conf)
    if conf.action == 'exec':
        return ExecJob(conf)
    raise Exception('Action "{0}" not supported'.format(conf.action))
