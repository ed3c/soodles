"""Read captured native evidence for a bounded local task; no model or provider writes.

This is an experimental discriminator, not landing authority. A successful result
covers emitted CLI tool events and native persisted turn context, never hidden
service routing or model weights. The recorder and raw evidence need separate audit.
"""
import json

CARRIER = 'local_macos_noodle_codex_exec'


def observe(raw_events, history, rollout, expected):
    missing, violations = [], []
    def need(ok, field):
        if not ok:
            missing.append(field)
    def require(ok, field):
        if not ok:
            violations.append(field)
    need(expected.get('carrier') == CARRIER, 'local_carrier')
    need(expected.get('model') == 'gpt-6-astra', 'expected_astra')
    starts = [e for e in raw_events if e.get('type') == 'thread.started']
    need(len(starts) == 1 and bool(starts[0].get('thread_id')), 'one_thread')
    session = starts[0].get('thread_id') if len(starts) == 1 else None
    begins = [e for e in raw_events if e.get('type') == 'turn.started']
    ends = [e for e in raw_events if e.get('type') == 'turn.completed']
    need(len(begins) == len(ends) == 1, 'complete_turn')
    require(not any(e.get('type') in ('turn.failed', 'error') for e in raw_events), 'native_error')
    need(expected.get('exit_code') == 0, 'successful_process_exit')
    items = [e for e in raw_events if e.get('type') in ('item.started', 'item.completed')]
    command_starts = [e['item'] for e in items if e['type'] == 'item.started' and e.get('item', {}).get('type') == 'command_execution']
    command_ends = [e['item'] for e in items if e['type'] == 'item.completed' and e.get('item', {}).get('type') == 'command_execution']
    start_ids, end_ids = [e.get('id') for e in command_starts], [e.get('id') for e in command_ends]
    need(bool(start_ids), 'tool_invocation')
    require(len(start_ids) == len(set(start_ids)) and len(end_ids) == len(set(end_ids)), 'unique_tool_ids')
    need(sorted(start_ids) == sorted(end_ids), 'tool_results_complete')
    marker = expected.get('marker')
    need(isinstance(marker, str) and bool(marker), 'expected_marker')
    need(any(marker and marker in e.get('aggregated_output', '') and e.get('exit_code') == 0 for e in command_ends), 'observed_tool_marker')
    thread = history.get('result', {}).get('thread', {})
    need(thread.get('id') == session and bool(session), 'history_thread_identity')
    turns = thread.get('turns', [])
    need(len(turns) == 1 and turns[0].get('status') == 'completed' and bool(turns[0].get('id')), 'history_complete_turn')
    turn_id = turns[0].get('id') if len(turns) == 1 else None
    metas = [e.get('payload', {}) for e in rollout if e.get('type') == 'session_meta']
    need(any(m.get('id') == session for m in metas) and bool(session), 'native_rollout_session')
    contexts = [e.get('payload', {}) for e in rollout if e.get('type') == 'turn_context']
    bound = [e for e in contexts if e.get('turn_id') == turn_id and turn_id]
    need(bool(bound), 'native_turn_model')
    require(all(e.get('model') == expected.get('model') for e in bound), 'turn_model_matches')
    need(all(bool(e.get('model')) for e in bound), 'native_turn_model_value')
    # A thread.model or launch -m value is intentionally never promoted here.
    return {'verdict': 'REJECT' if violations else ('INCOMPLETE' if missing else 'CAPABILITY_OBSERVED'),
            'missing': sorted(set(missing)), 'violations': sorted(set(violations)),
            'session_id': session, 'turn_id': turn_id,
            'observed_harness_turn_models': sorted({e.get('model') for e in bound if e.get('model')}),
            'model_evidence_level': 'native_persisted_turn_context' if bound else None,
            'service_effective_model': None, 'service_reroute_capture': 'not established by exec JSONL',
            'capture_scope': 'emitted CLI events for one bounded task, matched tool results and native turn history',
            'full_case_capture_proven': False, 'authorizes_landing': False}


if __name__ == '__main__':
    import sys
    try:
        packet = json.load(sys.stdin)
        result = observe(**packet)
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        result = {'verdict': 'INCOMPLETE', 'error': str(error), 'authorizes_landing': False}
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['verdict'] == 'CAPABILITY_OBSERVED' else 1)
