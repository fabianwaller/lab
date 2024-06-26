#! /usr/bin/env python3

# Solve some tasks with A* and the LM-Cut heuristic.

from fai.experiment import SimpleFDExperiment
import fai.suites as suites
from lab.environments import FAISlurmEnvironment

# adapt paths as necessary
REPO = '/data/eifler/planner/downward'
BENCHMARKS_DIR = '/data/eifler/downward-benchmarks'

# fai0x -> fai01-fai08
# fai1x -> fai11-13
# fai14 -> fai14
# fai-all -> fai01-fai14
# fai0x-quick : testing setup, has timelimit of 5 min
exp = SimpleFDExperiment(environment=FAISlurmEnvironment(
    email="eifler@cs.uni-saarland.de",
    partition="fai0x",
    memory_per_cpu="3872M",
    extra_options="#SBATCH -t 0-2:30:0", # set time limit to 2 hours and 30 minutes
))

exp.add_suite(BENCHMARKS_DIR, suites.suite_optimal_strips())
exp.add_algorithm('lmcut', REPO, 'main', ['--search', 'astar(lmcut())'])

# Parse the commandline and show or run experiment steps.
exp.run_steps()
