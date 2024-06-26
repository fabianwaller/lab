#! /usr/bin/env python3

from fai.experiment import SimpleFDExperiment
from lab.environments import FAISlurmEnvironment
from downward.reports.absolute import AbsoluteReport

REPO = '/data/eisenhut/planning/downward'  # https://github.com/aibasel/downward/
BENCHMARKS_DIR = '/data/eisenhut/planning/downward-benchmarks'  # https://github.com/aibasel/downward-benchmarks.git

commit = 'main'

exp = SimpleFDExperiment(environment=FAISlurmEnvironment())
suite = ["grid:prob01.pddl", "gripper:prob01.pddl"]

exp.add_suite(BENCHMARKS_DIR, suite)
exp.add_algorithm('astar-lmcut', REPO, commit, ['--search', 'astar(lmcut())'])

exp.add_report(AbsoluteReport(format='tex', attributes=['coverage', 'error', 'search_time', 'total_time']))

exp.run_steps()
