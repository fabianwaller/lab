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

import os

from lab import tools


def find_domain_file(benchmarks_dir, domain, problem):
    """
    Search for domain file in the directory *benchmarks_dir*/*domain*.
    Check the following names: 'domain.pddl', 'pXX-domain.pddl', or the
    full problem name preceeded by 'domain_'.
    """
    domain_basenames = [
        "domain.pddl",
        "domain.hddl",
        problem[:3] + "-domain.pddl",
        problem[:3] + "-domain.hddl",
        "domain_" + problem,
        "domain-" + problem,
    ]
    domain_dir = os.path.join(benchmarks_dir, domain)
    return tools.find_file(domain_basenames, domain_dir)

def find_explanation_settings_files(benchmarks_dir, domain, problem):
    """
    Return array of paths for the preferences files in the directory *benchmarks_dir*/*domain*
    that match the pattern: {problem_name_without_extension}-preferences-*.json
    """
    problem_base = os.path.splitext(problem)[0]
    
    pattern = f"{problem_base}-preferences-"
    
    domain_dir = os.path.join(benchmarks_dir, domain)
    
    if not os.path.isdir(domain_dir):
        return []
    
    matching_files = []
    for filename in os.listdir(domain_dir):
        if filename.startswith(pattern) and filename.endswith(".json"):
            matching_files.append(os.path.join(domain_dir, filename))
    
    return sorted(matching_files)

def get_problem(benchmarks_dir, domain_name, problem_name, cost_bound=None):
    problem_file = os.path.join(benchmarks_dir, domain_name, problem_name)
    domain_file = None
    if problem_file.endswith(".pddl") or problem_file.endswith(".hddl"):
        domain_file = find_domain_file(benchmarks_dir, domain_name, problem_name)
    explanation_settings_files = find_explanation_settings_files(benchmarks_dir, domain_name, problem_name)
    return Problem(
        domain_name, problem_name, problem_file=problem_file, domain_file=domain_file, explanation_settings_files=explanation_settings_files, cost_bound=cost_bound
    )


class Domain:
    def __init__(self, benchmarks_dir, domain):
        self.domain = domain
        directory = os.path.join(benchmarks_dir, domain)
        problem_files = tools.natural_sort(
            [
                p
                for p in os.listdir(directory)
                if "domain" not in p and not p.endswith(".py")
            ]
        )
        self.problems = [
            get_problem(benchmarks_dir, domain, problem) for problem in problem_files
        ]

    def __str__(self):
        return self.domain

    def __repr__(self):
        return f"<Domain {self.domain}>"

    def __hash__(self):
        return hash(self.domain)

    def __eq__(self, other):
        return self.domain == other.domain

    def __iter__(self):
        return iter(self.problems)


class Problem:
    def __init__(
        self, domain, problem, problem_file, domain_file=None, properties=None, explanation_settings_files=[], cost_bound=None
    ):
        """
        *domain* and *problem* are the display names of the domain and
        problem, *domain_file* and *problem_file* are paths to the
        respective files on the disk. If *domain_file* is not given,
        assume that *problem_file* is a SAS task.

        *properties* may be a dictionary of entries that should be
        added to the properties file of each run that uses this
        problem. ::

            suite = [
                Problem('gripper-original', 'prob01.pddl',
                    problem_file='/path/to/original/problem.pddl',
                    domain_file='/path/to/original/domain.pddl',
                    properties={'relaxed': False}),
                Problem('gripper-relaxed', 'prob01.pddl',
                    problem_file='/path/to/relaxed/problem.pddl',
                    domain_file='/path/to/relaxed/domain.pddl',
                    properties={'relaxed': True}),
                Problem('gripper', 'prob01.pddl', '/path/to/prob01.pddl')
            ]
        """
        self.domain = domain
        self.problem = problem
        self.problem_file = problem_file
        self.domain_file = domain_file
        self.explanation_settings_files = explanation_settings_files
        self.cost_bound = cost_bound

        self.properties = properties or {}
        self.properties.setdefault("domain", self.domain)
        self.properties.setdefault("problem", self.problem)
        self.properties.setdefault("explanation_settings_files", self.explanation_settings_files)
        self.properties.setdefault("cost_bound", self.cost_bound)

    def __str__(self):
        return (
            f"<Problem {self.domain}({self.domain_file}):{self.problem}"
            f"({self.problem_file}):{self.properties}>"
        )


def _generate_problems(benchmarks_dir, description):
    """
    Descriptions are either domains (e.g., "gripper") or problems
    (e.g., "gripper:prob01.pddl").
    """
    if isinstance(description, Problem):
        yield description
    elif isinstance(description, Domain):
        yield from description
    elif ":" in description:
        domain_name, problem_name, cost_bound = description.split(":", 2)
        if not cost_bound:
            raise ValueError(f"No cost bound given in problem description: {description}")
        yield get_problem(benchmarks_dir, domain_name, problem_name, cost_bound)
    else:
        yield from Domain(benchmarks_dir, description)


def build_suite(benchmarks_dir, descriptions):
    """
    *descriptions* must be a list of domain or problem descriptions::

        build_suite(benchmarks_dir, ["gripper", "grid:prob01.pddl"])

    """
    result = []
    for description in descriptions:
        result.extend(_generate_problems(benchmarks_dir, description))
    return result
