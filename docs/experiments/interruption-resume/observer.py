"""Supervisor-pinned bounded evidence predicates; no landing authority."""
import json
from pathlib import Path


def verify(directory):
    directory = Path(directory)
    physical = json.loads((directory / 'raw/physical.json').read_text())
    runs = physical['runs']
    assert runs['baseline']['exit_code'] != 0
    assert 'resume' in runs['baseline']['stderr']
    assert runs['candidate']['exit_code'] == 0
    assert runs['planted']['exit_code'] != 0
    assert 'unknown publication was repeated' in runs['planted']['stderr']
    receipt = json.loads(runs['candidate']['stdout'])
    assert receipt['classification'] == 'VERIFIED'
    assert [p['exit_code'] for p in receipt['processes']] == [-9, -9, 0, 0]
    assert receipt['pending']['published'] is False
    assert receipt['retained']['published'] is False
    assert receipt['lifecycle']['zero_residue'] is True
    assert receipt['authorizes_landing'] is False
    pclass = json.loads((directory / 'raw/pclass.json').read_text())
    expected = {'absent': ('proposal_pending', True),
                'pending': ('proposal_pending', False),
                'retained': ('previously_admitted', False)}
    result = {}
    for arm in ('baseline', 'treatment'):
        runs = pclass['arms'][arm]['runs']
        assert set(runs) == set(expected)
        for name, (action, published) in expected.items():
            run = runs[name]
            assert run['exit_code'] == 0, (arm, name, run)
            output = json.loads(run['stdout'])
            assert (output['action'], output['published']) == (action, published)
            assert run['argv'] == run['supplied_argv']
            assert output['next']['kind'] == 'input'
        result[arm] = {'legal_cases': len(runs), 'literal_invocations': len(runs)}
    return {'classification': 'VERIFIED', 'physical_controls': 'RED/GREEN/RED',
            'pclass': result, 'interpretation': 'scoped nonregression; no measured error-rate improvement',
            'authorizes_landing': False}


if __name__ == '__main__':
    import sys
    print(json.dumps(verify(sys.argv[1]), indent=2))
