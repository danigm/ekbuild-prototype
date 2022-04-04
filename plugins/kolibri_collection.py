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
from hashlib import sha256
from dataclasses import dataclass
from buildstream import Source, SourceError, utils, Consistency
from .kolibri_channel import KolibriChannelSource, STUDIO, API, SourceFile


class KolibriCollectionSource(KolibriChannelSource):
    def configure(self, node):
        self.node_validate(node, ['token', 'ref', 'channels'] +
                           Source.COMMON_CONFIG_KEYS)

        self.load_ref(node)
        self.token = self.node_get_member(node, str, 'token', None)
        if self.token is None:
            raise SourceError(f'{self}: Missing token or id')

        self.ref = self.node_get_member(node, str, 'ref', None)
        self.channels = self.node_get_member(node, list, 'channels', None)

    def calculate_hash(self, channels):
        # The hash is a sha256sum of the string formed with all the
        # channels in this collection
        s = ','.join(['{id}.{version}'.format(**c) for c in channels])
        return sha256(s.encode()).hexdigest()

    def preflight(self):
        pass

    def get_unique_key(self):
        return [self.token, self.ref]

    def load_ref(self, node):
        self.ref = self.node_get_member(node, str, 'ref', None)
        self.channels = self.node_get_member(node, list, 'channels', None)

    def get_ref(self):
        if self.ref is None or self.channels is None:
            return None
        return {
            'ref': self.ref,
            'channels': self.channels,
        }

    def set_ref(self, ref, node):
        node['ref'] = self.ref = ref['ref']
        node['channels'] = self.channels = ref['channels']

    def track(self):
        studio_api = STUDIO + API + self.token

        request = urllib.request.Request(studio_api)
        request.add_header('Accept', '*/*')
        request.add_header('User-Agent', 'BuildStream/1')
        urlopen = urllib.request.urlopen(request)

        payload = json.loads(urlopen.read())
        if not payload:
            raise SourceError(
                f'{self}: Cannot find any collection for {lookup}')

        channels = []
        for c in payload:
            channel = { 'id': c['id'], 'version': c['version'] }
            channels.append(channel)

        return {
            'ref': self.calculate_hash(channels),
            'channels': channels,
        }

    def fetch(self):
        for channel in self.channels:
            self._fetch_db(channel['id'], channel['version'])
            self._fetch_files(channel['id'], channel['version'])

    def stage(self, directory):
        for channel in self.channels:
            self._stage_db(directory, channel['id'], channel['version'])
            self._stage_files(directory, channel['id'], channel['version'])

    def get_consistency(self):
        if self.ref is None:
            return Consistency.INCONSISTENT

        for c in self.channels:
            mirror = self._get_mirror_dir(c['id'], c['version'])
            if not os.path.isdir(mirror):
                return Consistency.RESOLVED

        return Consistency.CACHED


def setup():
    return KolibriCollectionSource
