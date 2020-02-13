import os

from downward.experiment import FastDownwardExperiment
from downward.reports.absolute import AbsoluteReport
from lab.experiment import _get_default_experiment_name


def get_default_report_attributes():
    return ['coverage', 'error', 'expansions', 'search_time', 'total_time']


class SimpleFDExperiment(FastDownwardExperiment):
    def __init__(self,
                 path=None,
                 revision_cache=None,
                 add_default_parsers=True,
                 add_default_steps=True,
                 default_report_attributes=get_default_report_attributes(),
                 **kwargs
    ):
        if path is None and 'LAB_EXPERIMENTS' in os.environ:
            path = os.path.join(os.environ['LAB_EXPERIMENTS'], _get_default_experiment_name())
        if revision_cache is None and 'LAB_REVISION_CACHE' in os.environ:
            revision_cache = os.environ['LAB_REVISION_CACHE']
        FastDownwardExperiment.__init__(self, path=path, revision_cache=revision_cache, **kwargs)
        if add_default_parsers:
            self.add_parser(self.EXITCODE_PARSER)
            self.add_parser(self.TRANSLATOR_PARSER)
            self.add_parser(self.SINGLE_SEARCH_PARSER)
            self.add_parser(self.PLANNER_PARSER)
        if add_default_steps:
            self.add_step('build', self.build)
            self.add_step('start', self.start_runs)
            self.add_fetcher(name='fetch')
        if default_report_attributes is not None:
            self.add_report(AbsoluteReport(attributes=default_report_attributes),
                            outfile='report-{}.html'.format(_get_default_experiment_name()))

    # Forward all args to FastDownwardExperiment, but set default memory limit to 4GB.
    # Use no_default_driver_options=True to omit the default options (validate and time/memory limits).
    def add_algorithm(
        self,
        name,
        repo,
        rev,
        component_options,
        build_options=None,
        driver_options=None,
        no_default_driver_options=False
    ):
        driver_options = [
            '--overall-memory-limit',
            '4G',
        ] + (driver_options or [])
        FastDownwardExperiment.add_algorithm(self, name, repo, rev, component_options, build_options, driver_options)
        if no_default_driver_options:
            assert len(self._algorithms[name].driver_options) >= 7
            assert self._algorithms[name].driver_options[5:7] == driver_options[:2]
            self._algorithms[name].driver_options = self._algorithms[name].driver_options[7:]
