#
#  Copyright EndlessOS Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  Authors:
#        Daniel Garcia <danigm@endlessos.org>

import os
import sqlite3
import shutil
import contextlib
import urllib.request
import json
from buildstream import Source, SourceError, utils, Consistency

STUDIO = 'https://studio.learningequality.org'
API = '/api/public/v1/channels/lookup/'


class KolibriChannelSource(Source):
    def configure(self, node):
        self.node_validate(node, ['token', 'id', 'version'] +
                           Source.COMMON_CONFIG_KEYS)

        self.load_ref(node)
        self.channel_id = self.node_get_member(node, str, 'id', None)
        self.token = self.node_get_member(node, str, 'token', None)
        if self.channel_id is None and self.token is None:
            raise SourceError(f'{self}: Missing token or id')

        self.version = self.node_get_member(node, int, 'version', 1)

    def preflight(self):
        pass

    def get_unique_key(self):
        return [self.channel_id, self.version]

    def load_ref(self, node):
        self.channel_id = self.node_get_member(node, str, 'id', None)
        self.version = self.node_get_member(node, int, 'version', 1)

    def get_ref(self):
        if self.channel_id is None or self.version is None:
            return None
        return {
            'id': self.channel_id,
            'version': self.version,
        }

    def set_ref(self, ref, node):
        node['id'] = self.channel_id = ref['id']
        node['version'] = self.version = ref['version']

    def track(self):
        lookup = self.channel_id or self.token
        studio_api = STUDIO + API + lookup

        request = urllib.request.Request(studio_api)
        request.add_header('Accept', '*/*')
        request.add_header('User-Agent', 'BuildStream/1')
        urlopen = urllib.request.urlopen(request)

        payload = json.loads(urlopen.read())

        channel = payload[0]
        if not channel:
            raise SourceError(
                f'{self}: Cannot find any channel for {lookup}')

        return channel

    def _download_content(self, path, dst):
        url = f'{STUDIO}/content{path}'

        default_name = os.path.basename(url)
        request = urllib.request.Request(url)
        request.add_header('Accept', '*/*')
        request.add_header('User-Agent', 'BuildStream/1')

        urlopen = urllib.request.urlopen(request)
        with contextlib.closing(urlopen) as response:
            info = response.info()
            filename = info.get_filename(default_name)
            filename = os.path.basename(filename)
            if not os.path.exists(dst):
                os.makedirs(dst)
            local_file = os.path.join(dst, filename)
            with open(local_file, 'wb') as dest:
                shutil.copyfileobj(response, dest)

    def fetch(self):
        mirror = self._get_mirror_dir()
        databases = os.path.join(mirror, 'databases')
        storage = os.path.join(mirror, 'storage')
        if not os.path.isdir(databases):
            os.makedirs(databases)
        if not os.path.isdir(storage):
            os.makedirs(storage)

        path = f'/databases/{self.channel_id}.sqlite3'
        try:
            self._download_content(path, databases)
        except (urllib.error.URLError,
                urllib.error.ContentTooShortError,
                OSError) as e:
            raise SourceError(f"{self}: Error mirroring {path}: {e}") from e

        database = os.path.join(databases, f'{self.channel_id}.sqlite3')
        with sqlite3.connect(database) as db:
            cur = db.cursor()
            cur.execute('select id, extension from content_localfile')
            for row in cur:
                id = row[0]
                filename = f'{id}.{row[1]}'
                path = f'/storage/{id[0]}/{id[1]}/{filename}'
                dst = os.path.join(storage, id[0], id[1])

                try:
                    self._download_content(path, dst)
                except (urllib.error.URLError,
                        urllib.error.ContentTooShortError,
                        OSError) as e:
                    raise SourceError(f"{self}: Error mirroring {path}: {e}") from e

    def stage(self, directory):
        mirror = self._get_mirror_dir()
        databases = os.path.join(mirror, 'databases')
        storage = os.path.join(mirror, 'storage')

        dbdir = os.path.join(directory, 'databases')
        if not os.path.exists(dbdir):
            os.makedirs(dbdir)

        database = os.path.join(databases, f'{self.channel_id}.sqlite3')
        shutil.copy(database, dbdir)

        self.debug(storage)
        for root, dirs, files in os.walk(storage):
            for name in files:
                self.debug(name)
                file = os.path.join(storage, name[0], name[1], name)
                dst = os.path.join(directory, 'storage', name[0], name[1])
                if not os.path.exists(dst):
                    os.makedirs(dst)
                shutil.copy(database, dst)

    def get_consistency(self):
        if self.channel_id is None or self.version is None:
            return Consistency.INCONSISTENT


        if os.path.isdir(self._get_mirror_dir()):
            return Consistency.CACHED
        return Consistency.RESOLVED

    def _get_mirror_dir(self):
        return os.path.join(self.get_mirror_directory(),
                            utils.url_directory_name(self.name),
                            f'{self.channel_id}.{self.version}')


def setup():
    return KolibriChannelSource
