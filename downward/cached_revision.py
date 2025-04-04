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
import os.path
import subprocess

from lab import tools
from lab.cached_revision import CachedRevision
from lab.environments import FAISlurmEnvironment, FAICondorEnvironment, within_slurm_job, within_condor_job


class CachedFastDownwardRevision(CachedRevision):
    """This class represents Fast Downward checkouts.

    It provides methods for caching and compiling given revisions.
    """

    def __init__(self, repo, rev, build_options, python2_translator=False):
        """
        * *repo*: Path to Fast Downward repository.
        * *rev*: Fast Downward revision.
        * *build_options*: List of build.py options.
        """
        build_cmd = ["./build.py"] + build_options
        if within_condor_job():
            build_cmd.extend(["-j", str(FAICondorEnvironment.EXTRA_STEP_CPUS)])
        if within_slurm_job():
            build_cmd.extend(["-j", str(FAISlurmEnvironment.EXTRA_STEP_CPUS)])
        CachedRevision.__init__(self, repo, rev, build_cmd, ["experiments", "misc"])
        self.build_options = build_options
        self.python2_translator = python2_translator

    def _compile(self):
        CachedRevision._compile(self)
        # force translator to explicitly use python2
        if self.python2_translator:
            tools.run_command(["sed", "-i.bak", "1s/python/python2/", "translate.py"], cwd=os.path.join(self.path, "src", "translate"))

    def _cleanup(self):
        # Only keep the bin directories in "builds" dir.
        for path in glob.glob(os.path.join(self.path, "builds", "*", "*")):
            if os.path.basename(path) != "bin":
                tools.remove_path(path)

        # Remove unneeded files.
        tools.remove_path(os.path.join(self.path, "build.py"))

        # Strip binaries.
        binaries = []
        for path in glob.glob(os.path.join(self.path, "builds", "*", "bin", "*")):
            if os.path.basename(path) in ["downward", "preprocess"]:
                binaries.append(path)
        subprocess.call(["strip"] + binaries)

        # Compress src directory.
        subprocess.call(
            ["tar", "-cf", "src.tar", "--remove-files", "src"], cwd=self.path
        )
        subprocess.call(["xz", "src.tar"], cwd=self.path)
