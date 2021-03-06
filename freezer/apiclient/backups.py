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

import json
import requests

import exceptions


class BackupsManager(object):

    def __init__(self, client):
        self.client = client
        self.endpoint = self.client.endpoint + '/v1/backups/'

    @property
    def headers(self):
        return {'X-Auth-Token': self.client.auth_token}

    def create(self, backup_metadata):
        r = requests.post(self.endpoint,
                          data=json.dumps(backup_metadata),
                          headers=self.headers)
        if r.status_code != 201:
            raise exceptions.ApiClientException(r)
        backup_id = r.json()['backup_id']
        return backup_id

    def delete(self, backup_id):
        endpoint = self.endpoint + backup_id
        r = requests.delete(endpoint, headers=self.headers)
        if r.status_code != 204:
            raise exceptions.ApiClientException(r)

    def list(self, limit=10, offset=0, search=None):
        """
        Retrieves a list of backup infos

        :param limit: number of result to return (optional, default 10)
        :param offset: order of first document (optional, default 0)
        :param search: structured query (optional)
                       can contain:
                       * "time_before": timestamp
                       * "time_after": timestamp
                       Example:
                       { "time_before": 1428529956 }
        """
        data = json.dumps(search) if search else None
        query = {'limit': int(limit), 'offset': int(offset)}
        r = requests.get(self.endpoint, headers=self.headers,
                         params=query, data=data)
        if r.status_code != 200:
            raise exceptions.ApiClientException(r)

        return r.json()['backups']

    def get(self, backup_id):
        endpoint = self.endpoint + backup_id
        r = requests.get(endpoint, headers=self.headers)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return None
        raise exceptions.ApiClientException(r)
