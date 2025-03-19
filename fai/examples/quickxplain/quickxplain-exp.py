#! /usr/bin/env python3

from fai.experiment import SimpleFDExperiment
from lab.environments import FAISlurmEnvironment, LocalEnvironment
from downward.reports.absolute import AbsoluteReport

# REPO = '/Users/fabianwaller/Developer/symbolic-xaip'  # https://github.com/aibasel/downward/
# BENCHMARKS_DIR = '/Users/fabianwaller/planning.domains/classical'# https://github.com/aibasel/downward-benchmarks.git

REPO = '/data/waller/symbolic-xaip'
BENCHMARKS_DIR = '/data/waller/classical-domains/classical'

commit = 'quickxplain'

# exp = SimpleFDExperiment(environment=LocalEnvironment())

exp = SimpleFDExperiment(environment=FAISlurmEnvironment(
    email="fawa00001@stud.uni-saarland.de",
    partition="fai0x",
    memory_per_cpu="3872M",
    extra_options="#SBATCH -t 0-4:30:0", # set time limit to 4 hours and 30 minutes
))

suite = ['mystery:prob05.pddl:14', 'logistics98:prob20.pddl:96', 'mprime:prob16.pddl:4', 'logistics98:prob10.pddl:75', 'gripper:prob09.pddl:44', 'mystery:prob16.pddl:13', 'gripper:prob06.pddl:31', 'gripper:prob01.pddl:8', 'movie:prob24.pddl:5', 'logistics98:prob06.pddl:52', 'gripper:prob10.pddl:49', 'gripper:prob14.pddl:67', 'movie:prob09.pddl:5', 'movie:prob23.pddl:5', 'mystery:prob28.pddl:5', 'logistics98:prob08.pddl:30', 'movie:prob03.pddl:5', 'gripper:prob02.pddl:13', 'logistics98:prob27.pddl:98', 'mprime:prob02.pddl:5', 'logistics98:prob02.pddl:24', 'mprime:prob06.pddl:8', 'movie:prob28.pddl:5', 'mprime:prob24.pddl:6', 'gripper:prob05.pddl:26', 'logistics98:prob16.pddl:39', 'logistics98:prob13.pddl:50', 'movie:prob06.pddl:5', 'logistics98:prob14.pddl:62', 'logistics98:prob12.pddl:30', 'logistics98:prob24.pddl:28', 'logistics98:prob22.pddl:186', 'logistics98:prob01.pddl:20', 'logistics98:prob09.pddl:59', 'movie:prob18.pddl:5', 'movie:prob05.pddl:5', 'mprime:prob11.pddl:5', 'movie:prob16.pddl:5', 'logistics98:prob03.pddl:40', 'logistics98:prob15.pddl:64', 'logistics98:prob11.pddl:22', 'logistics98:prob07.pddl:24', 'logistics98:prob19.pddl:96', 'movie:prob12.pddl:5', 'movie:prob13.pddl:5', 'logistics98:prob25.pddl:129', 'mystery:prob11.pddl:5', 'logistics98:prob26.pddl:131', 'movie:prob01.pddl:5', 'movie:prob20.pddl:5', 'movie:prob21.pddl:5', 'gripper:prob13.pddl:62', 'mystery:prob02.pddl:5', 'gripper:prob18.pddl:85', 'movie:prob17.pddl:5', 'mystery:prob09.pddl:6', 'gripper:prob04.pddl:22', 'mystery:prob24.pddl:18', 'mprime:prob29.pddl:3', 'logistics98:prob21.pddl:70', 'gripper:prob07.pddl:35', 'movie:prob08.pddl:5', 'logistics98:prob05.pddl:16', 'mprime:prob09.pddl:6', 'logistics98:prob31.pddl:10', 'movie:prob19.pddl:5', 'movie:prob26.pddl:5', 'mprime:prob28.pddl:5', 'movie:prob11.pddl:5', 'logistics98:prob32.pddl:15', 'movie:prob14.pddl:5', 'mprime:prob27.pddl:4', 'mystery:prob27.pddl:4', 'movie:prob02.pddl:5', 'mprime:prob14.pddl:8', 'logistics98:prob23.pddl:76', 'mystery:prob06.pddl:8', 'gripper:prob11.pddl:53', 'mystery:prob13.pddl:11', 'mystery:prob14.pddl:8', 'logistics98:prob29.pddl:210', 'mystery:prob29.pddl:3', 'mprime:prob30.pddl:7', 'movie:prob15.pddl:5', 'mprime:prob05.pddl:8', 'logistics98:prob17.pddl:32', 'logistics98:prob33.pddl:20', 'movie:prob10.pddl:5', 'logistics98:prob04.pddl:41', 'movie:prob22.pddl:5', 'gripper:prob08.pddl:40', 'gripper:prob19.pddl:89', 'logistics98:prob34.pddl:34', 'logistics98:prob28.pddl:179', 'movie:prob25.pddl:5', 'gripper:prob03.pddl:17', 'logistics98:prob30.pddl:92', 'mprime:prob13.pddl:8', 'gripper:prob17.pddl:80', 'movie:prob04.pddl:5', 'gripper:prob15.pddl:71', 'gripper:prob16.pddl:76', 'logistics98:prob18.pddl:115', 'movie:prob27.pddl:5', 'movie:prob29.pddl:5', 'movie:prob07.pddl:5', 'gripper:prob12.pddl:58']

exp.add_suite(BENCHMARKS_DIR, suite)

driver_options=["--build", "release64"]

exp.add_algorithm('weakening', REPO, commit, component_options=['--search', 'sfw(non_stop=true, bound=10, all_soft_goals=true, weakening=true, quickxplain=false)'],build_options=[], driver_options=driver_options)

exp.add_algorithm('strengthening', REPO, commit, component_options=['--search', 'sfw(non_stop=true, bound=10, all_soft_goals=true, weakening=false, quickxplain=false)'],build_options=[], driver_options=driver_options)

exp.add_algorithm('quickxplain 1', REPO, commit, component_options=['preferences_1.json', '--search', 'sfw(non_stop=true, bound=10, all_soft_goals=true, quickxplain=true)'],build_options=[], driver_options=driver_options)

exp.add_algorithm('quickxplain 2', REPO, commit, component_options=['preferences_2.json', '--search', 'sfw(non_stop=true, bound=10, all_soft_goals=true, quickxplain=true)'],build_options=[], driver_options=driver_options)

exp.add_algorithm('quickxplain 3', REPO, commit, component_options=['preferences_3.json', '--search', 'sfw(non_stop=true, bound=10, all_soft_goals=true, quickxplain=true)'],build_options=[], driver_options=driver_options)

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

all_attributes = ['coverage', 'error', 'exit_code', 'search_time', 'total_time', 'number_mugs']

exp.add_report(BaseReport(attributes=all_attributes), outfile="base_report.html")

# exp.add_report(AbsoluteReport(format='tex', attributes=all_attributes))

exp.run_steps()
