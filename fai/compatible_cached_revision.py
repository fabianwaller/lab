# -*- coding: utf-8 -*-
#
# Downward Lab uses the Lab package to conduct experiments with the
# Fast Downward planning system.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import glob
import hashlib
import logging
import os.path
import shutil
import subprocess

from lab import tools

from downward.cached_revision import *


_HG_ID_CACHE = {}



class CompatibleCachedRevision(CachedRevision):
    """This class represents Fast Downward checkouts.

    It provides methods for caching and compiling given revisions.
    """
    def __init__(self, repo, local_rev, build_options):
        """
        * *repo*: Path to Fast Downward repository.
        * *local_rev*: Fast Downward revision.
        * *build_options*: List of build.py options.
        """
        # only default initialization for now
        CachedRevision.__init__(self, repo=repo, local_rev=local_rev, build_options=build_options)
        
    def cache(self, revision_cache):
        super().cache(revision_cache, ["benchmarks"])

    def _compile(self):
        if not os.path.exists(os.path.join(self.path, "src", 'build_all')):
            logging.critical('build_all not found.')
        retcode = tools.run_command(
            ['./build_all'] + self.build_options, cwd=os.path.join(self.path, "src/"))
        if retcode == 0:
            tools.write_file(self._get_sentinel_file(), '')
        else:
            logging.critical('Build failed in {}'.format(self.path))

    def _cleanup(self):
        # Remove unneeded files.
        tools.remove_path(self.get_cached_path("src/build_all"))
        tools.remove_path(self.get_cached_path("src/cleanup"))
        if (os.path.exists(self.get_cached_path("src/validate"))):
            tools.remove_path(self.get_cached_path("src/validate"))
        # Remove unneeded folder.
        if (os.path.exists(self.get_cached_path("src/VAL/"))):
            tools.remove_path(self.get_cached_path("src/VAL/"))
        # Remove .obj files.
        if (os.path.exists(self.get_cached_path("src/preprocess/.obj/"))):
            tools.remove_path(self.get_cached_path("src/preprocess/.obj/"))
        tools.remove_path(self.get_cached_path("src/search/.obj/"))

        # Strip binaries.
        if ("--debug" in self.build_options):
            binaries = [os.path.join(self.path, "src", "preprocess", "preprocess-debug"),
                        os.path.join(self.path, "src", "search", "downward-debug")]
        else:
            binaries = [os.path.join(self.path, "src", "preprocess", "preprocess"),
                        os.path.join(self.path, "src", "search", "downward-release")]
        subprocess.call(['strip'] + binaries)
