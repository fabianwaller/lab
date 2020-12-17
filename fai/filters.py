def _rename_domain(run, domain):
    run['problem'] = '%s-%s' % (run['domain'], run['problem'])
    run['domain'] = domain
    run['id'][1] = run['domain']
    run['id'][2] = run['problem']
    run['id_string'] = ':'.join(run['id'])
    return run

def rename_domains(run):
    domain_paper_names = {
        'airport'                  : 'Airport',
        'agricola-opt18-strips'    : 'Agricola',
        'agricola-sat18-strips'    : 'Agricola',
        'assembly'                 : 'Assembly',
        'barman-opt11-strips'      : 'Barman',
        'barman-opt14-strips'      : 'Barman',
        'barman-sat11-strips'      : 'Barman',
        'barman-sat14-strips'      : 'Barman',
        'blocks'                   : 'Blocks',
        'cavediving-14-adl'        : 'Cavediving',
        'caldera-opt18-adl'        : 'Caldera',
        'caldera-sat18-adl'        : 'Caldera',
        'caldera-split-opt18-adl'  : 'Caldera-split',
        'caldera-split-sat18-adl'  : 'Caldera-split',
        'childsnack-opt14-strips'  : 'Childsnack',
        'childsnack-sat14-strips'  : 'Childsnack',
        'citycar-opt14-adl'        : 'CityCar',
        'citycar-sat14-adl'        : 'CityCar',
        'data-network-opt18-strips': 'DataNetwork',
        'data-network-sat18-strips': 'DataNetwork',
        'depot'                    : 'Depot',
        'driverlog'                : 'DriverLog',
        'elevators-opt08-strips'   : 'Elevators',
        'elevators-opt11-strips'   : 'Elevators',
        'elevators-sat08-strips'   : 'Elevators',
        'elevators-sat11-strips'   : 'Elevators',
        'flashfill-sat18-adl'      : 'Flashfill',
        'floortile-opt11-strips'   : 'Floortile',
        'floortile-opt14-strips'   : 'Floortile',
        'floortile-sat11-strips'   : 'Floortile',
        'floortile-sat14-strips'   : 'Floortile',
        'freecell'                 : 'Freecell',
        'ged-opt14-strips'         : 'GED',
        'ged-sat14-strips'         : 'GED',
        'grid'                     : 'Grid',
        'gripper'                  : 'Gripper',
        'hiking-opt14-strips'      : 'Hiking',
        'hiking-sat14-strips'      : 'Hiking',
        'logistics00'              : 'Logistics',
        'logistics98'              : 'Logistics',
        'maintenance-opt14-adl'    : 'Maintenance',
        'maintenance-sat14-adl'    : 'Maintenance',
        'miconic'                  : 'Miconic',
        'miconic-fulladl'          : 'Miconic',
        'miconic-simpleadl'        : 'Miconic',
        'movie'                    : 'Movie',
        'mprime'                   : 'Mprime',
        'mystery'                  : 'Mystery',
        'nomystery-opt11-strips'   : 'Nomystery',
        'nomystery-sat11-strips'   : 'Nomystery',
        'nurikabe-opt18-adl'       : 'Nurikabe',
        'nurikabe-sat18-adl'       : 'Nurikabe',
        'openstacks'               : 'Openstacks',
        'openstacks-strips'        : 'Openstacks',
        'openstacks-opt08-strips'  : 'Openstacks',
        'openstacks-opt11-strips'  : 'Openstacks',
        'openstacks-opt14-strips'  : 'Openstacks',
        'openstacks-sat08-adl'     : 'Openstacks',
        'openstacks-sat08-strips'  : 'Openstacks',
        'openstacks-sat11-strips'  : 'Openstacks',
        'openstacks-sat14-strips'  : 'Openstacks',
        'organic-synthesis-opt18-strips' : 'OrgSynth',
        'organic-synthesis-sat18-strips' : 'OrgSynth',
        'organic-synthesis-split-opt18-strips' : 'OrgSynth-split',
        'organic-synthesis-split-sat18-strips' : 'OrgSynth-split',
        'optical-telegraphs'       : 'Optical Telegraphs',
        'parcprinter-08-strips'    : 'Parcprinter',
        'parcprinter-opt11-strips' : 'Parcprinter',
        'parcprinter-sat11-strips' : 'Parcprinter',
        'parking-opt11-strips'     : 'Parking',
        'parking-opt14-strips'     : 'Parking',
        'parking-sat11-strips'     : 'Parking',
        'parking-sat14-strips'     : 'Parking',
        'pathways'                 : 'Pathways',
        'pathways-noneg'           : 'Pathways',
        'pegsol-08-strips'         : 'Pegsol',
        'pegsol-opt11-strips'      : 'Pegsol',
        'pegsol-sat11-strips'      : 'Pegsol',
        'petri-net-alignment-opt18-strips' : 'PNetAlignment',
        'philosophers'             : 'Philosophers',
        'pipesworld-notankage'     : 'Pipes-notank',
        'pipesworld-tankage'       : 'Pipes-tank',
        'psr-large'                : 'PSR',
        'psr-middle'               : 'PSR',
        'psr-small'                : 'PSR',
        'rovers'                   : 'Rovers',
        'satellite'                : 'Satellite',
        'scanalyzer-08-strips'     : 'Scanalyzer',
        'scanalyzer-opt11-strips'  : 'Scanalyzer',
        'scanalyzer-sat11-strips'  : 'Scanalyzer',
        'schedule'                 : 'Schedule',
        'settlers-opt18-adl'       : 'Settlers',
        'settlers-sat18-adl'       : 'Settlers',
        'snake-opt18-strips'       : 'Snake',
        'snake-sat18-strips'       : 'Snake',
        'sokoban-opt08-strips'     : 'Sokoban',
        'sokoban-opt11-strips'     : 'Sokoban',
        'sokoban-sat08-strips'     : 'Sokoban',
        'sokoban-sat11-strips'     : 'Sokoban',
        'spider-opt18-strips'      : 'Spider',
        'spider-sat18-strips'      : 'Spider',
        'storage'                  : 'Storage',
        'termes-opt18-strips'      : 'Termes',
        'termes-sat18-strips'      : 'Termes',
        'tetris-opt14-strips'      : 'Tetris',
        'tetris-sat14-strips'      : 'Tetris',
        'thoughtful-sat14-strips'  : 'Thoughtful',
        'tidybot-opt11-strips'     : 'Tidybot',
        'tidybot-opt14-strips'     : 'Tidybot',
        'tidybot-inv-opt11-strips' : 'Tidybot',
        'tidybot-inv-opt14-strips' : 'Tidybot',
        'tidybot-sat11-strips'     : 'Tidybot',
        'tpp'                      : 'TPP',
        'transport-opt08-strips'   : 'Transport',
        'transport-opt11-strips'   : 'Transport',
        'transport-opt14-strips'   : 'Transport',
        'transport-sat08-strips'   : 'Transport',
        'transport-sat11-strips'   : 'Transport',
        'transport-sat14-strips'   : 'Transport',
        'trucks'                   : 'Trucks',
        'trucks-strips'            : 'Trucks',
        'visitall-opt11-strips'    : 'VisitAll',
        'visitall-opt14-strips'    : 'VisitAll',
        'visitall-sat11-strips'    : 'VisitAll',
        'visitall-sat14-strips'    : 'VisitAll',
        'woodworking-opt08-strips' : 'Woodworking',
        'woodworking-opt11-strips' : 'Woodworking',
        'woodworking-sat08-strips' : 'Woodworking',
        'woodworking-sat11-strips' : 'Woodworking',
        'zenotravel'               : 'Zenotravel'}
    if not run['domain'] in domain_paper_names:
        print run['domain']
    assert run['domain'] in domain_paper_names
    return _rename_domain(run, domain_paper_names[run['domain']])

def get_group_domains_filter(domains):
    def group_domains(run):
        return run if run['domain'] not in domains else _rename_domain(run, 'Others')
    return group_domains
