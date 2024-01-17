#! /usr/bin/env python3

import os.path
import glob

from downward.reports.absolute import AbsoluteReport
from lab.experiment import Experiment
from lab.environments import FAISlurmEnvironment


class BaseReport(AbsoluteReport):
    INFO_ATTRIBUTES = ["time_limit", "memory_limit", "algorithm"]
    ERROR_ATTRIBUTES = [
        "domain",
        "problem",
        "algorithm",
        "error",
        "unexplained_errors",
        "node"
    ]


all_attributes = [
    "error",
    "exit_code",
]

exp_dir = os.path.dirname(os.path.realpath(__file__))
domain_dir = os.path.join(exp_dir, "files")
parser_path = os.path.join(exp_dir, "parser.py")
exe_path = os.path.join(exp_dir, "executable.py")


def get_input_files(domain_directory):
    files = sorted(glob.glob(os.path.join(domain_dir, "*.txt")))
    return files


def create_experiment(env):
    exp = Experiment(environment=env)
    exp.add_resource("executable", exe_path, symlink=True)
    exp.add_parser(parser_path)
    return exp


time_limit = 60
memory_limit = 1024


def add_runs(exp):
    for input_file in get_input_files(domain_dir):
        run = exp.add_run()
        problem = os.path.basename(input_file)
        run.add_resource("input_file", input_file, symlink=True)
        run.add_command("run", ["{executable}", "{input_file}"], 
                        time_limit=time_limit, memory_limit=memory_limit)
        run.set_property("domain", "dummy-domain")
        run.set_property("problem", problem)
        run.set_property("algorithm", "dummy-algorithm")
        run.set_property("time_limit", time_limit)
        run.set_property("memory_limit", memory_limit)
        run.set_property("id", [problem])


exp = create_experiment(FAISlurmEnvironment())
add_runs(exp)

exp.add_step("build", exp.build)
exp.add_step("start", exp.start_runs)
exp.add_parse_again_step()
exp.add_fetcher(name="fetch")
exp.add_report(BaseReport(attributes=all_attributes), outfile="base_report.html")

exp.run_steps()
