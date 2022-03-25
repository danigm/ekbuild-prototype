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
import shutil
import zipfile
import contextlib
import urllib.request
import json
from buildstream import Source, SourceError, utils, Consistency


class GithubReleaseSource(Source):
    def configure(self, node):
        self.node_validate(node, ['url', 'repo',
                                  'asset', 'asset_id',
                                  'unzip', 'rename'] +
                           Source.COMMON_CONFIG_KEYS)

        self.load_ref(node)
        self.repo = self.node_get_member(node, str, 'repo', None)
        self.asset = self.node_get_member(node, str, 'asset', None)
        if self.repo is None:
            raise SourceError(f'{self}: Missing repo')
        if self.asset is None:
            raise SourceError(f'{self}: Missing asset')

        self.unzip = self.node_get_member(node, bool, 'unzip', False)
        self.rename = self.node_get_member(node, str, 'rename', None)

    def preflight(self):
        pass

    def get_unique_key(self):
        return [self.original_url, self.asset_id]

    def load_ref(self, node):
        self.asset_id = self.node_get_member(node, str, 'asset_id', None)
        self.original_url = self.node_get_member(node, str, 'url', None)
        if self.original_url is not None:
            self.url = self.translate_url(self.original_url)
        else:
            self.url = None

    def get_ref(self):
        if self.original_url is None or self.asset_id is None:
            return None
        return {
            'url': self.original_url,
            'asset_id': self.asset_id,
        }

    def set_ref(self, ref, node):
        node['url'] = self.original_url = ref['url']
        node['asset_id'] = self.asset_id = ref['asset_id']

    def track(self):
        # https://api.github.com/repos/REPO/releases/latest
        github_api = f'https://api.github.com/repos/{self.repo}/releases/latest'  # noqa: E501
        payload = json.loads(
            urllib.request.urlopen(github_api).read()
        )
        release = payload['name']
        assets = payload['assets']
        if not release:
            raise SourceError(
                f'{self}: Cannot find any tracking for {self.name}')

        found_ref = None
        for asset in assets:
            if asset['name'] == self.asset:
                found_ref = {
                    'url': asset['browser_download_url'],
                    'asset_id': str(asset['id']),
                }

                break

        if found_ref is None:
            raise SourceError(
                f'{self}: Did not find any asset for {self.repo} {self.asset}')

        return found_ref

    def fetch(self):
        try:
            with self.tempdir() as tempdir:
                default_name = os.path.basename(self.url)
                request = urllib.request.Request(self.url)
                request.add_header('Accept', '*/*')
                request.add_header('User-Agent', 'BuildStream/1')

                urlopen = urllib.request.urlopen(request)
                with contextlib.closing(urlopen) as response:
                    info = response.info()
                    filename = info.get_filename(default_name)
                    filename = os.path.basename(filename)
                    local_file = os.path.join(tempdir, filename)
                    with open(local_file, 'wb') as dest:
                        shutil.copyfileobj(response, dest)

                if not os.path.isdir(self._get_mirror_dir()):
                    os.makedirs(self._get_mirror_dir())

                sha256 = utils.sha256sum(local_file)
                os.rename(local_file, self._get_mirror_file(sha256))
                return sha256

        except (urllib.error.URLError,
                urllib.error.ContentTooShortError,
                OSError) as e:
            raise SourceError(f"{self}: Error mirroring {self.url}: {e}",
                              temporary=True) from e

    def stage(self, directory):
        self.debug(f'UNZIP: {self.unzip}')
        if self.unzip:
            with zipfile.ZipFile(self._get_mirror_file(), mode='r') as zipf:
                zipf.extractall(path=directory)
        else:
            name = self.rename or self.asset
            shutil.copy(self._get_mirror_file(), os.path.join(directory, name))

    def get_consistency(self):
        if self.original_url is None or self.asset_id is None:
            return Consistency.INCONSISTENT

        if os.path.isfile(self._get_mirror_file()):
            return Consistency.CACHED
        return Consistency.RESOLVED

    def _get_mirror_file(self, sha=None):
        return os.path.join(self._get_mirror_dir(), self.asset_id)

    def _get_mirror_dir(self):
        return os.path.join(self.get_mirror_directory(),
                            utils.url_directory_name(self.name))


def setup():
    return GithubReleaseSource
