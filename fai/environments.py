from lab.oracle_grid_environment import OracleGridEngineEnvironment


def get_env(hosts='@allhosts'):
    if not isinstance(hosts, list):
        hosts = [hosts]
    queues = ['all.q@{}'.format(host) for host in hosts]
    return OracleGridEngineEnvironment(queue=','.join(queues))

def get_fai0x_env():
    return get_env(hosts='@fai0x')

def get_fai1x_env():
    return get_env(hosts='@fai1x')
