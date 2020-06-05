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

import logging
import os.path
import subprocess

from lab import tools

from downward.cached_revision import CachedRevision


class CompatibleCachedRevision(CachedRevision):
    """This class represents Fast Downward checkouts.

    It provides methods for caching and compiling given revisions.
    """

    def __init__(self, repo, rev, build_options):
        """
        * *repo*: Path to Fast Downward repository.
        * *rev*: Fast Downward revision.
        * *build_options*: List of build.py options.
        """
        CachedRevision.__init__(
            self, repo, rev, ["./build_all"] + build_options, ["experiments", "misc", "benchmarks"]
        )
        self.build_options = build_options

    def _compile(self):
        if not os.path.exists(os.path.join(self.path, "src", "build_all")):
            logging.critical("build_all not found.")
        retcode = tools.run_command(self.build_cmd, cwd=os.path.join(self.path, "src"))
        if retcode == 0:
            tools.write_file(self._get_sentinel_file(), "")
        else:
            logging.critical(f"Build failed in {self.path}")

    def _cleanup(self):
        # Remove unneeded files.
        tools.remove_path(os.path.join(self.path, "src/build_all"))
        tools.remove_path(os.path.join(self.path, "src/cleanup"))
        if (os.path.exists(os.path.join(self.path, "src/validate"))):
            tools.remove_path(os.path.join(self.path, "src/validate"))
        # Remove unneeded folder.
        if (os.path.exists(os.path.join(self.path, "src/VAL/"))):
            tools.remove_path(os.path.join(self.path, "src/VAL/"))
        # Remove .obj files.
        if (os.path.exists(os.path.join(self.path, "src/preprocess/.obj/"))):
            tools.remove_path(os.path.join(self.path, "src/preprocess/.obj/"))
        tools.remove_path(os.path.join(self.path, "src/search/.obj/"))

        # Strip binaries.
        if ("--debug" in self.build_options):
            binaries = [os.path.join(self.path, "src", "preprocess", "preprocess-debug"),
                        os.path.join(self.path, "src", "search", "downward-debug")]
        else:
            binaries = [os.path.join(self.path, "src", "preprocess", "preprocess"),
                        os.path.join(self.path, "src", "search", "downward-release")]
        subprocess.call(['strip'] + binaries)
