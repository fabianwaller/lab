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

"""
A module for running Fast Downward experiments.
"""

from collections import defaultdict, OrderedDict
import logging
import os.path

from lab.experiment import Run, Experiment, get_default_data_dir

from downward import suites

from downward.experiment import FastDownwardExperiment
from downward.experiment import FastDownwardRun

from fai.compatible_cached_revision import CompatibleCachedRevision


DIR = os.path.dirname(os.path.abspath(__file__))
DOWNWARD_SCRIPTS_DIR = os.path.join(DIR, 'scripts')

def _get_solver_resource_name(cached_rev):
    return "fast_downward_" + cached_rev.name

class CompatibleFastDownwardRun(FastDownwardRun):
    def __init__(self, exp, algo, task):
        Run.__init__(self, exp)
        self.algo = algo
        self.task = task

        self._set_properties()

        # Linking to instead of copying the PDDL files makes building
        # the experiment twice as fast.
        self.add_resource(
            'domain', self.task.domain_file, 'domain.pddl', symlink=True)
        self.add_resource(
            'problem', self.task.problem_file, 'problem.pddl', symlink=True)

        self.add_command(
            'planner',
            ['{' + _get_solver_resource_name(algo.cached_revision) + '}'] +
            algo.driver_options + ['{domain}', '{problem}'] + algo.component_options,
            time_limit=algo.time_limit, memory_limit=algo.memory_limit)

        # old driver does not delete output files; preprocessor + translator
        self.add_command('remove-output', ['rm', '-f', 'output'])
        self.add_command('remove-output-sas', ['rm', '-f', 'output.sas'])

        # old driver does not validate
        self.add_command('validate-plan', ['validate', 'domain.pddl', 'problem.pddl', 'sas_plan'], memory_limit=4096)


class _CompatibleDownwardAlgorithm(object):
    def __init__(self, name, cached_revision, driver_options, component_options, time_limit, memory_limit):
        self.name = name
        self.cached_revision = cached_revision
        self.driver_options = driver_options
        self.component_options = component_options
        self.time_limit = time_limit
        self.memory_limit = memory_limit


class CompatibleFastDownwardExperiment(FastDownwardExperiment):
    """Conduct a Fast Downward experiment.

    The most important methods for customizing an experiment are
    :meth:`.add_algorithm`, :meth:`.add_suite`, :meth:`.add_parser`,
    :meth:`.add_step` and :meth:`.add_report`.

    .. note::

        To build the experiment, execute its runs and fetch the results,
        add the following steps (previous Lab versions added these steps
        automatically):

        >>> exp = FastDownwardExperiment()
        >>> exp.add_step('build', exp.build)
        >>> exp.add_step('start', exp.start_runs)
        >>> exp.add_fetcher(name='fetch')

    .. note::

        By default, "output.sas" translator output files are deleted
        after the driver exits. To keep these files use ``del
        exp.commands['remove-output-sas']`` in your experiment script.

    """

    def __init__(self, path=None, environment=None, revision_cache=None):
        """
        See :class:`lab.experiment.Experiment` for an explanation of
        the *path* and *environment* parameters.

        *revision_cache* is the directory for caching Fast Downward
        revisions. It defaults to ``<scriptdir>/data/revision-cache``.
        This directory can become very large since each revision uses
        about 30 MB.

        >>> from lab.environments import BaselSlurmEnvironment
        >>> env = BaselSlurmEnvironment(email="my.name@unibas.ch")
        >>> exp = FastDownwardExperiment(environment=env)

        You can add parsers with :meth:`.add_parser()`. See
        :ref:`parsing` for how to write custom parsers and
        :ref:`downward-parsers` for the list of built-in parsers. Which
        parsers you should use depends on the algorithms you're running.
        For single-search experiments, we recommend adding the following
        parsers in this order:

        >>> exp.add_parser(exp.EXITCODE_PARSER)
        >>> exp.add_parser(exp.TRANSLATOR_PARSER)
        >>> exp.add_parser(exp.SINGLE_SEARCH_PARSER)
        >>> exp.add_parser(exp.PLANNER_PARSER)

        """
        # only default initialization for now
        FastDownwardExperiment.__init__(self, path=path, environment=environment, revision_cache=revision_cache)


    def add_compatible_algorithm(self, name, repo, rev, component_options,
                                 build_options=None, driver_options=None, python2_translator=True):
        """
        Add a Fast Downward algorithm to the experiment, i.e., a
        planner configuration in a given repository at a given
        revision.

        *name* is a string describing the algorithm (e.g.
        ``"issue123-lmcut"``).

        *repo* must be a path to a Fast Downward repository.

        *rev* must be a valid revision in the given repository (e.g.,
        ``"default"``, ``"tip"``, ``"issue123"``).

        *component_options* must be a list of strings. By default these
        options are passed to the search component. Use
        ``"--translate-options"``, ``"--preprocess-options"`` or
        ``"--search-options"`` within the component options to override
        the default for the following options, until overridden again.

        If given, *build_options* must be a list of strings. They will
        be passed to the ``build.py`` script. Options can be build names
        (e.g., ``"release32"``, ``"debug64"``), ``build.py`` options
        (e.g., ``"--debug"``) or options for Make. If *build_options* is
        omitted, the ``"release32"`` version is built.

        If given, *driver_options* must be a list of strings. They will
        be passed to the ``fast-downward.py`` script. See
        ``fast-downward.py --help`` for available options. The list is
        always prepended with ``["--validate", "--overall-time-limit",
        "30m", "--overall-memory-limit', "3584M"]``. Specifying custom
        limits overrides the default limits.

        Example experiment setup:

        >>> import os.path
        >>> exp = FastDownwardExperiment()
        >>> repo = os.environ["DOWNWARD_REPO"]

        Test iPDB in the latest revision on the default branch:

        >>> exp.add_algorithm(
        ...     "ipdb", repo, "default",
        ...     ["--search", "astar(ipdb())"])

        Test LM-Cut in an issue experiment:

        >>> exp.add_algorithm(
        ...     "issue123-v1-lmcut", repo, "issue123-v1",
        ...     ["--search", "astar(lmcut())"])

        Run blind search in debug mode:

        >>> exp.add_algorithm(
        ...     "blind", repo, "default",
        ...     ["--search", "astar(blind())"],
        ...     build_options=["--debug"],
        ...     driver_options=["--debug"])

        Run FF in 64-bit mode:

        >>> exp.add_algorithm(
        ...     "ff", repo, "default",
        ...     ["--search", "lazy_greedy([ff()])"],
        ...     build_options=["release64"],
        ...     driver_options=["--build", "release64"])

        Run LAMA-2011 with custom planner time limit:

        >>> exp.add_algorithm(
        ...     "lama", repo, "default",
        ...     [],
        ...     driver_options=[
        ...         "--alias", "seq-saq-lama-2011",
        ...         "--overall-time-limit", "5m"])

        """
        if not isinstance(name, str):
            logging.critical('Algorithm name must be a string: {}'.format(name))
        if name in self._algorithms:
            logging.critical('Algorithm names must be unique: {}'.format(name))
        build_options = build_options or []
        driver_options = ([
            '--overall-time-limit', 1800,
            '--overall-memory-limit', 4096] +
            (driver_options or []))
        if (any(limit in driver_options for limit in ["--translate-time-limit", "--translate-memory-limit", "--search-time-limit", "--search-memory-limit"])):
            logging.warning("Component runtime and memory limits are not supported by the old driver script.")

        time_limit_str = driver_options[len(driver_options) - driver_options[::-1].index("--overall-time-limit")]
        memory_limit_str = driver_options[len(driver_options) - driver_options[::-1].index("--overall-memory-limit")]

        if time_limit_str is not None:
            try:
                time_limit = int(time_limit_str)
            except ValueError:
                logging.error("cannot parse --overall-time-limit; must be given as int in number of seconds")
        if memory_limit_str is not None:
            try:
                memory_limit = int(memory_limit_str)
            except ValueError:
                logging.error("cannot parse --overall-memory-limit; must be given as int in number of MiB")      

        # the limits can be defined more than once, so "while" not "if"
        while ("--overall-time-limit" in driver_options):
            i = driver_options.index("--overall-time-limit")
            del driver_options[i+1]
            del driver_options[i]
        while ("--overall-memory-limit" in driver_options):
            i = driver_options.index("--overall-memory-limit")
            del driver_options[i+1]
            del driver_options[i]

        self._algorithms[name] = _CompatibleDownwardAlgorithm(
            name, CompatibleCachedRevision(repo, rev, build_options, python2_translator),
            driver_options, component_options, time_limit=time_limit, memory_limit=memory_limit)

    def _add_code(self):
        """Add the compiled code to the experiment."""
        for cached_rev in self._get_unique_cached_revisions():
            cache_path = os.path.join(self.revision_cache, cached_rev.name)
            dest_path = "code-" + cached_rev.name
            self.add_resource("", cache_path, dest_path)
            if (isinstance(cached_rev, CompatibleCachedRevision)):
                fd_file = 'src/fast-downward.py'
            else:
                fd_file = 'fast-downward.py'
            # Overwrite the script to set an environment variable.
            self.add_resource(
                _get_solver_resource_name(cached_rev),
                os.path.join(cache_path, fd_file),
                os.path.join(dest_path, fd_file))

    def _add_runs(self):
        for algo in self._algorithms.values():
            for task in self._get_tasks():
                if (isinstance(algo, _CompatibleDownwardAlgorithm)):
                    self.add_run(CompatibleFastDownwardRun(self, algo, task))
                else:
                    self.add_run(FastDownwardRun(self, algo, task))
