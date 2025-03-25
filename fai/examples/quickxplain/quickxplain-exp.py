#! /usr/bin/env python3

from fai.experiment import SimpleFDExperiment
from lab.environments import FAISlurmEnvironment, LocalEnvironment
from downward.reports.absolute import AbsoluteReport

# REPO = '/Users/fabianwaller/Developer/symbolic-xaip'  # https://github.com/aibasel/downward/
# BENCHMARKS_DIR = '/Users/fabianwaller/planning.domains/classical'# https://github.com/aibasel/downward-benchmarks.git
# SUITE= '/Users/fabianwaller/Developer/api-tools/suite.txt'

REPO = '/data/waller/symbolic-xaip'
BENCHMARKS_DIR = '/data/waller/classical-domains/classical'
SUITE= '/data/waller/suite75.txt'

commit = 'quickxplain'

# exp = SimpleFDExperiment(environment=LocalEnvironment())

exp = SimpleFDExperiment(environment=FAISlurmEnvironment(
    email="fawa00001@stud.uni-saarland.de",
    partition="fai0x",
    # memory_per_cpu="3872M",
    # extra_options="#SBATCH -t 0-4:30:0", # set time limit to 4 hours and 30 minutes
))


with open(SUITE, 'r') as suite_file:
    suite = [line.strip() for line in suite_file if line.strip()]

exp.add_suite(BENCHMARKS_DIR, suite)

driver_options=["--build", "release64"]

exp.add_algorithm('weakening', REPO, commit, component_options=['--search', 'sfw(non_stop=true, bound=10, all_soft_goals=true, weakening=true, quickxplain=false)'],build_options=[], driver_options=driver_options)

exp.add_algorithm('strengthening', REPO, commit, component_options=['--search', 'sfw(non_stop=true, bound=10, all_soft_goals=true, weakening=false, quickxplain=false)'],build_options=[], driver_options=driver_options)

for i in range(5):
    exp.add_algorithm(f'quickxplain {i + 1}', REPO, commit, component_options=[f'preferences_{i+1}.json', '--search', 'sfw(non_stop=true, bound=10, all_soft_goals=true, quickxplain=true)'],build_options=[], driver_options=driver_options)

class BaseReport(AbsoluteReport):
    INFO_ATTRIBUTES = ["limit_search_time", "limit_search_memory", "algorithm"]
    ERROR_ATTRIBUTES = [
        "domain",
        "problem",
        "algorithm",
        "error",
        "unexplained_errors",
        "node"
    ]


all_attributes = ['coverage', 'error', 'exit_code', 'search_time', 'total_time', 'hard_goals_count', 'soft_goals_count', 'mugs_count', 'mugs_computation_time', 'solver_calls_count', 'scc_count', 'average_scc_size']

# advanced version that enumerates mugs can show found mugs over time

exp.add_report(BaseReport(attributes=all_attributes), outfile="base_report.html")

# exp.add_report(AbsoluteReport(format='tex', attributes=all_attributes))

exp.run_steps()
