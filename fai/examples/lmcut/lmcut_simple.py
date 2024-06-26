#! /usr/bin/env python3

# Solve some tasks with A* and the LM-Cut heuristic.

import fai.environments
from fai.experiment import SimpleFDExperiment
# the downward-benchmarks repository must be in your PYTHONPATH to use fai.suites
# see https://github.com/aibasel/downward-benchmarks
import fai.suites as suites

# adapt paths as necessary
REPO = '/data/fickert/fast-downward'
BENCHMARKS_DIR = '/data/fickert/downward-benchmarks'

# runs the experiment on fai01-fai08, use get_fai1x_env() to use fai11-fai14 instead
exp = SimpleFDExperiment(environment=fai.environments.get_fai0x_env())

exp.add_suite(BENCHMARKS_DIR, suites.suite_optimal_strips())
exp.add_algorithm('lmcut', REPO, 'master', ['--search', 'astar(lmcut())'])

# Parse the commandline and show or run experiment steps.
exp.run_steps()
