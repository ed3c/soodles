"""Fixed, bounded consumer-report predicates, not a complete platform auditor."""
import json, sys

def observe(report):
    required={'source','methods_by_job','harness_for_job_2','report_observation',
              'help_argv_observed','next_action','requires_all_methods',
              'generic_behavior_eval_uses_eval_report','delivery_complete',
              'actual_files_read','actual_commands','limitations'}
    missing=sorted(required-set(report))
    if missing: return {'evidence_validity':'INCONCLUSIVE','missing':missing,'behavior':None,'authorizes_landing':False}
    methods=report['methods_by_job']
    if not isinstance(methods,dict) or not all(isinstance(methods.get(k),list) for k in '1234'):
        return {'evidence_validity':'INVALID','behavior':None,'problem':'methods_by_job','authorizes_landing':False}
    checks={
      'cli_contract':'cli-for-agents' in methods['1'],
      'bounded_comparison':'verify-this' in methods['2'],
      'existing_eval_audit':'eval-audit' in methods['3'],
      'trace_discovery':'error-discovery' in methods['4'],
      'conditional_methods':report['requires_all_methods'] is False,
      'specific_report_scope':report['generic_behavior_eval_uses_eval_report'] is False,
      'no_delivery_claim':report['delivery_complete'] is False,
      'unusable_evidence':report['report_observation'].get('evidence_validity')=='INVALID' and report['report_observation'].get('behavior') is None,
      'owner_preserved':report['report_observation'].get('next',{}).get('owner')=='supervisor',
    }
    return {'evidence_validity':'VALID','behavior':{'checks':checks,'barriers':[k for k,v in checks.items() if not v]},
            'review_required':['native subprocess harness retained; no forced PTY','next action does not manufacture selector/evaluator','actual commands agree with report'],
            'observation_scope':'consumer_report_plus_preserved_subprocess_records','authorizes_landing':False}

if __name__=='__main__':
    with open(sys.argv[1]) as stream: result=observe(json.load(stream))
    print(json.dumps(result,indent=2))
