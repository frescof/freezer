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

Freezer restore modes related functions
"""

import logging
from freezer import utils


class RestoreOs:
    def __init__(self, client_manager, container):
        self.client_manager = client_manager
        self.container = container

    def _get_backups(self, path, restore_from_timestamp):
        """
        :param path:
        :type path: str
        :param restore_from_timestamp:
        :type restore_from_timestamp: int
        :return:
        """
        swift = self.client_manager.get_swift()
        info, backups = swift.get_container(self.container, path=path)
        backups = sorted(map(lambda x: int(x["name"].rsplit("/", 1)[-1]),
                             backups))
        backups = filter(lambda x: x >= restore_from_timestamp, backups)

        if not backups:
            msg = "Cannot find backups for path: %s" % path
            logging.error(msg)
            raise BaseException(msg)
        return backups[-1]

    def _create_image(self, path, restore_from_timestamp):
        """
        :param path:
        :param restore_from_timestamp:
        :type restore_from_timestamp: int
        :return:
        """
        swift = self.client_manager.get_swift()
        glance = self.client_manager.get_glance()
        backup = self._get_backups(path, restore_from_timestamp)
        stream = swift.get_object(
            self.container, "%s/%s" % (path, backup), resp_chunk_size=10000000)
        length = int(stream[0]["x-object-meta-length"])
        logging.info("[*] Creation glance image")
        image = glance.images.create(
            data=utils.ReSizeStream(stream[1], length, 1),
            container_format="bare",
            disk_format="raw")
        return stream[0], image

    def restore_cinder(self, restore_from_date, volume_id):
        """
        Restoring cinder backup using
        :param volume_id:
        :return:
        """
        cinder = self.client_manager.get_cinder()
        backups = cinder.backups.findall(volume_id=volume_id,
                                         status='available')
        backups = [x for x in backups if x.created_at >= restore_from_date]
        if not backups:
            logging.error("no available backups for cinder volume")
        else:
            backup = min(backups, key=lambda x: x.created_at)
            cinder.restores.restore(backup_id=backup.id)

    def restore_cinder_by_glance(self, restore_from_timestamp, volume_id):
        """
        1) Define swift directory
        2) Download and upload to glance
        3) Create volume from glance
        4) Delete
        :param restore_from_timestamp:
        :type restore_from_timestamp: int
        :param volume_id - id of attached cinder volume
        """
        (info, image) = self._create_image(volume_id, restore_from_timestamp)
        length = int(info["x-object-meta-length"])
        gb = 1073741824
        size = length / gb
        if length % gb > 0:
            size += 1
        logging.info("[*] Creation volume from image")
        self.client_manager.get_cinder().volumes.create(size,
                                                        imageRef=image.id)
        logging.info("[*] Deleting temporary image")
        self.client_manager.get_glance().images.delete(image)

    def restore_nova(self, restore_from_timestamp, instance_id):
        """
        :param restore_from_timestamp:
        :type restore_from_timestamp: int
        :param instance_id: id of attached nova instance
        :return:
        """
        (info, image) = self._create_image(instance_id, restore_from_timestamp)
        nova = self.client_manager.get_nova()
        flavor = nova.flavors.get(info['x-object-meta-tenant-id'])
        logging.info("[*] Creation an instance")
        nova.servers.create(info['x-object-meta-name'], image, flavor)
