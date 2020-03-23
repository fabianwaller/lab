import os

import suites
# avoid recursive self-imports if suites is not found in PYTHONPATH
if os.path.abspath(suites.__file__) == os.path.abspath(__file__):
    raise ImportError('Failed to import suites, check if downward-benchmarks in your PYTHONPATH.')


def _mystery_unsolvable():
    return ['mystery:prob{:02d}.pddl'.format(x) for x in [4, 5, 7, 8, 12, 16, 18, 21, 22, 23, 24]]

def _mystery_solvable():
    return [problem for problem in ['mystery:prob{:02d}.pddl'.format(x) for x in range(1, 31)]
            if problem not in _mystery_unsolvable()]

def fix_mystery(suite):
    if not 'mystery' in suite:
        return suite
    return sorted([domain for domain in suite if domain != 'mystery'] + _mystery_solvable())


def fix_duplicates(suite):
    def get_ipc11_redundant_domain(domain, ipc08_track, ipc11_track, new_instances=None):
        ipc08_domain = '{}-{}08-strips'.format(domain, ipc08_track)
        ipc11_domain = '{}-{}11-strips'.format(domain, ipc11_track)
        replacement = [ipc08_domain]
        if new_instances:
            replacement += ['{}:p{:02d}.pddl'.format(ipc11_domain, instance) for instance in new_instances]
        return [ipc08_domain, ipc11_domain], replacement

    # pairs of (combination of domains containing duplicate instances, replacement)
    redundant_domains = (
        # fully redundant IPC'11 domains (optimal track)
        [get_ipc11_redundant_domain(domain, '', 'opt') for domain in
            ['parcprinter', 'scanalyzer']] +
        [get_ipc11_redundant_domain(domain, 'opt', 'opt') for domain in
            ['elevators', 'openstacks', 'sokoban', 'woodworking']] +
        # partially redundant IPC'11 domains (optimal track)
        [get_ipc11_redundant_domain('pegsol', '', 'opt', [1, 5, 6, 7, 9, 12])] +
        [get_ipc11_redundant_domain('transport', 'opt', 'opt', range(7, 17))] +
        # other redundancies (optimal track)
        [(['tidybot-opt11-strips', 'tidybot-opt14-strips'],
          ['tidybot-opt11-strips'] + ['tidybot-opt14-strips:p{:02d}.pddl'.format(x) for x in range(1, 11)])] +
        [(['visitall-opt11-strips', 'visitall-opt14-strips'],
          ['visitall-opt11-strips'] + ['visitall-opt14-strips:{}'.format(instance) for instance in [
            'p-1-12.pddl',
            'p-1-13.pddl',
            'p-1-14.pddl',
            'p-1-15.pddl',
            'p-1-16.pddl',
            'p-1-17.pddl',
            'p-1-18.pddl',
            'p-05-5.pddl',
            'p-05-6.pddl',
            'p-05-7.pddl',
            'p-05-8.pddl',
            'p-05-9.pddl',
            'p-05-10.pddl']])] +
        # fully redundant IPC'11 domains (satisficing track)
        [get_ipc11_redundant_domain('scanalyzer', '', 'sat')] +
        [get_ipc11_redundant_domain('sokoban', 'sat', 'sat')] +
        # partially redundant IPC'11 domains (satisficing track)
        [get_ipc11_redundant_domain(domain, 'sat', 'sat', range(11, 21)) for domain in
            ['elevators', 'openstacks', 'transport', 'woodworking']] +
        [get_ipc11_redundant_domain('parcprinter', '', 'sat', range(11, 21))] +
        [get_ipc11_redundant_domain('pegsol', '', 'sat', range(4, 9))] +
        # other redundancies (satisficing track)
        [(['visitall-sat11-strips', 'visitall-sat14-strips'],
          ['visitall-sat11-strips'] + ['visitall-sat14-strips:pfile{:02d}.pddl'.format(x) for x in ([31, 33] + list(range(51, 66)))])]
    )

    redundant_instances = [
        ('scanalyzer-08-strips', ['scanalyzer-08-strips:p{:02d}.pddl'.format(x) for x in range(1, 31) if x not in [23, 24]]),
        ('transport-opt14-strips', ['transport-opt14-strips:p{:02d}.pddl'.format(x) for x in range(1, 20)])
    ]

    for domains, replacement in redundant_domains:
        if all(domain in suite for domain in domains):
            suite = [domain for domain in suite if domain not in domains]
            suite += replacement
    for domain, replacement in redundant_instances:
        if domain in suite:
            suite.remove(domain)
            suite += replacement
    return sorted(suite)


def suite_optimal_strips():
    return fix_mystery(fix_duplicates(suites.suite_optimal_strips()))


def suite_optimal():
    return fix_mystery(fix_duplicates(suites.suite_optimal()))


def suite_satisficing_strips():
    return fix_mystery(fix_duplicates(suites.suite_satisficing_strips()))


def suite_satisficing():
    return fix_mystery(fix_duplicates(suites.suite_satisficing()))
