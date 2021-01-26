import os

from lab.experiment import Experiment, _get_default_experiment_name
from lab.fetcher import Fetcher
from lab.steps import Step


class AggregatingExperimentPart:
    def __init__(self, name):
        self.name = name
        self.fetch_dirs = []
        self.reports = []

    def add_fetcher(self, dir, **kwargs):
        # Use the old default behavior when merging results.
        if 'merge' not in kwargs:
            kwargs['merge'] = True
        self.fetch_dirs.append((dir, kwargs))

    def add_report(self, report, filename):
        self.reports.append((report, filename))


class AggregatingExperiment(Experiment):
    """Experiment class that aggregates multiple Lab experiments.

    This class can be used to simplify fetching results from multiple
    experiments and generate combined reports. The aggregating experiment
    consists of one or more parts, and each part can have multiple fetchers and
    reports. Each part has one step to run all of its fetchers and another step
    to generate all of its reports.

    Example:

    >>> exp = AggregatingExperiment()

    Create a new part for the experiment:

    >>> part = AggregatingExperimentPart('my_part')

    Add some fetchers:

    >>> part.add_fetcher('/path/to/some/experiment')
    >>> part.add_fetcher('/path/to/some/other/experiment')

    And some reports:

    >>> part.add_report(AbsoluteReport(...), 'report.html')

    Finally, add the part to the experiment:

    >>> exp.add_part(part)
    """

    def __init__(self, path=None, **kwargs):
        if path is None and 'LAB_EXPERIMENTS' in os.environ:
            path = os.path.join(os.environ['LAB_EXPERIMENTS'], _get_default_experiment_name())
        super().__init__(path=path, **kwargs)

    def add_part(self, part):
        eval_dir = os.path.join(self.eval_dir, part.name)

        def fetch_all():
            if not os.path.exists(eval_dir):
                os.makedirs(eval_dir)
            for path, kwargs in part.fetch_dirs:
                fetcher = Fetcher()
                fetcher(path, eval_dir, **kwargs)
        self.steps.append(Step(f'{part.name}-fetch-all', fetch_all))

        def create_reports():
            assert os.path.exists(eval_dir)
            for report, filename in part.reports:
                report(eval_dir, os.path.join(eval_dir, filename))
        self.steps.append(Step(f'{part.name}-create-reports', create_reports))
