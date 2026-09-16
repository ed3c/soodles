"""One bounded normalization; frozen observer semantics remain unchanged.

Missing model/transcript/checkpoint observations stay null/false. This script
does not manufacture behavioral results or supply landing authority.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = 'e4b4a8487855b75ef2d47087019bb52c4d5ffd6c'
TREATMENT = 'a7e563703dbf1d95e93ede2ef71fb9e2bd4a7424'
CHECKPOINT = 'e3881548ceababec1070e2509ead654f58249ce69a9c6bd6d4388143a17a14ed'
PROVIDER = '39080ae945e7bee00fcd9d84c41157f6471da12c'
spec = importlib.util.spec_from_file_location('frozen_observer', ROOT.parent/'context39-observer/bundle/observe.py')
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)

def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')

def content(result):
    return result['structuredContent']['content']

def blob(text):
    data=text.encode()
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

summary=[]
for name in ['runner_x2','runner_y2','unknown_x','unknown_y','transfer_x','transfer_y']:
    folder=ROOT/name
    if not (folder/'final.json').exists():
        raise RuntimeError('Not completed: '+name)
    case='runner-task' if name.startswith('runner') else ('unknown-write' if name.startswith('unknown') else 'fresh-transfer')
    treatment='_y' in name
    ref=TREATMENT if treatment else BASE
    expected=dict(repository='ed3c/soodles',instruction_ref=ref,code_ref=BASE,
                  config_id='native-spawn-gpt-6-astra-fork-none-default-effort-readonly-v1',
                  agents_blob='82c8df3c6e3678d73c99bae40bed94ba22048cef' if treatment else '3667a6d70ea4a4fddd2df22768b0b83def179f81',
                  control_blob='bce6313c91ee3ace4cdd5fbf663978fd66a55bfb',
                  runtime_head=BASE,run_id=35128051435,run_attempt=1,
                  checkpoint_digest=CHECKPOINT,provider_blob=PROVIDER)
    events=[]
    calls=[]
    runtime=None
    for request in sorted(folder.glob('*-request.json')):
        req=json.loads(request.read_text())
        result_path=request.with_name(request.name.replace('-request','-result'))
        result=json.loads(result_path.read_text())
        args=req.get('args',req.get('arguments',{}))
        locator=f'{name}/{result_path.name}'
        calls.append(dict(request=f'{name}/{request.name}',result=locator,tool=req['tool']))
        path=args.get('path','')
        url=args.get('url','')
        if '/contents/' in url:
            path=url.split('/contents/',1)[1].split('?',1)[0]
        if req['tool']=='exec_command' and '/handoff.json' in args.get('cmd','') and args.get('cmd','').startswith('cat '):
            events.append(dict(kind='handoff',evidence=locator,scope='actual producer-written local handoff'))
        if path=='AGENTS.md':
            events.append(dict(kind='read_doc',path=path,blob=blob(content(result)),evidence=locator))
        if path=='tests/test_landing.py':
            events.append(dict(kind='read_control',blob=blob(content(result)),evidence=locator))
        if url.endswith('/runs/35128051435/attempts/1'):
            runtime=json.loads(content(result))
        if url.endswith('/runs/35128051435/attempts/1/jobs') and runtime:
            jobs=json.loads(content(result))['jobs']
            step=next(s for j in jobs for s in j['steps'] if s['name']=='Canonical acceptance on the exact candidate head')
            events.append(dict(kind='read_run',evidence=locator,head=runtime['head_sha'],run_id=runtime['id'],attempt=runtime['run_attempt'],conclusion=runtime['conclusion'],acceptance_step=step['conclusion']))
        if path.endswith('/pending-input.json'):
            packet=json.loads(content(result))
            events.append(dict(kind='read_owner',evidence=locator+'#/checkpoint-and-owner_output',
                checkpoint_before=None,checkpoint_after=None,writes_offered=packet['checkpoint']['writes_offered'],
                scope='read of immutable fixture; no consumer mutable checkpoint execution or final byte readback'))
            events.append(dict(kind='read_provider',evidence=locator+'#/provider_snapshot',fixture_blob=blob(content(result)),scope='simulated immutable provider snapshot'))
    final='NULL_NEXT_INSUFFICIENT' if case=='runner-task' else 'WAIT_FOR_PROVIDER_READBACK'
    events.append(dict(kind='conclude',result=final,evidence=f'{name}/final.json',scope='supervisor semantic mapping; independent audit required'))
    trace={k:expected[k] for k in ['repository','instruction_ref','code_ref','config_id']}
    trace.update(case=case,source_kind='captured',session_id='/root/'+name,
                 session_id_kind='native tool-returned canonical task path, not provider-internal session id',
                 model=None,requested_model='gpt-6-astra',carrier='cloud_chatgpt_github_actions',
                 raw_trace=name+'/',capture_complete=False,events=events,
                 recording_scope='consumer-recorded task evidence with disclosed exclusions; not a native platform transcript')
    if case=='fresh-transfer':
        trace['producer_session_id']='/root/producer_'+('y' if treatment else 'x')
    packet=dict(trace=trace,expected=expected,calls=calls)
    result=observer.observe(trace,expected)
    save(folder/'normalized.json',packet)
    save(folder/'observer-result.json',result)
    summary.append(dict(task=name,case=case,result=result,
        interpretation='Checkpoint nulls are absent mutable before/after observations, not an observed mutation. Frozen observer classifies this predicate failure as REJECT.' if case!='runner-task' else 'Incomplete native capture and observed model provenance.'))
save(ROOT/'observer-summary.json',summary)
print(json.dumps(summary,indent=2))
