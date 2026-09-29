"""Standalone process/crash oracle. Provider is an explicit supervisor-owned fixture."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile


def delivery_probe(cli_root, isolated=False):
    cli_root = Path(cli_root).resolve()
    cases = []
    def require(ok, reason):
        if not ok:
            raise RuntimeError('delivery: ' + reason)
    with tempfile.TemporaryDirectory(prefix='soodles-delivery-') as directory:
        root = Path(directory)
        root.chmod(0o755)
        lane = root / 'lane'; lane.mkdir(); lane.chmod(0o777 if isolated else 0o700)
        sink = root / 'provider-effects.json'
        sink.write_text('[]\n'); sink.chmod(0o644)
        def execute(args, kill=None):
            env = {k: os.environ[k] for k in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR') if k in os.environ}
            argv = [sys.executable, '-B', str(cli_root / 'soodles.py'), 'landing', *map(str, args)]
            if kill:
                # Instrument only the child after its actual durable save. No oracle import of candidate code.
                code = """import json,os,signal,sys
sys.path.insert(0,sys.argv[1])
import landing
save=landing.save
def crash(path,state):
 save(path,state)
 if state.get('phase') in ('merge_pending','close_pending'):
  os.kill(os.getpid(),signal.SIGKILL)
landing.save=crash
getattr(landing,sys.argv[2])(sys.argv[3],json.load(open(sys.argv[4])))
"""
                argv = [sys.executable, '-B', '-c', code, str(cli_root), kill, str(args[1]), str(args[2])]
            result = subprocess.run(argv, cwd=lane, env=env, text=True, capture_output=True, timeout=20,
                                    user=65534 if isolated else None, group=65534 if isolated else None)
            return result
        def invoke(args):
            r = execute(args)
            require(r.returncode == 0, f'{args[0]} failed: {r.stderr.strip()}')
            return json.loads(r.stdout)
        def write(path, value):
            # Child owns lane/checkpoints; every provider observation is replaced from parent memory.
            if path.exists(): path.unlink()
            path.write_text(json.dumps(value)); path.chmod(0o644)
        identity = invoke(['identity'])['verifier_sha256']
        repo = {'full_name': 'ed3c/soodles'}
        claim = {'repository':'ed3c/soodles','issue':1,'pr':2,'head':'a'*40,'tree':'b'*40,
                 'base_head':'c'*40,'run_id':10,'run_attempt':1,'worktree':'fixture',
                 'control_root':str(root),'verifier_sha256':identity}
        snapshot = {'pr':{'number':2,'html_url':'https://github.com/ed3c/soodles/pull/2',
                         'body':'Refs ed3c/soodles#1','head':{'repo':repo,'sha':'a'*40,'ref':'fixture'},
                         'base':{'repo':repo,'sha':'c'*40,'ref':'main'},'merged':False,'state':'open',
                         'draft':False,'mergeable':True},
                    'issue':{'number':1,'html_url':'https://github.com/ed3c/soodles/issues/1','state':'open'},
                    'run':{'id':10,'run_attempt':1,'repository':repo,'head_repository':repo,'head_sha':'a'*40,
                           'event':'pull_request','path':'.github/workflows/runtime.yml','status':'completed','conclusion':'success'},
                    'commit':{'sha':'a'*40,'tree':{'sha':'b'*40}},
                    'jobs':{'total_count':1,'jobs':[{'id':11,'name':'runtime-evidence','run_id':10,'head_sha':'a'*40,
                              'status':'completed','conclusion':'success','steps':[{'name':'Canonical acceptance on the exact candidate head',
                              'status':'completed','conclusion':'success'}]}]},
                    'branch':{'name':'main','commit':{'sha':'c'*40}}}
        original = json.loads(json.dumps(snapshot))
        cf, sf = lane/'claim.json', lane/'readback.json'
        write(cf, claim); write(sf, snapshot)
        def fresh(name):
            cp = lane / (name + '.json')
            result = invoke(['start', cf, sf, cp])
            require(result.get('next', {}).get('kind') == 'provider_readback', 'start missing owner next readback')
            require(result['next']['operation'] == 'advance', 'start routes to wrong consumer')
            require(result['next']['requests']['pr'] == {'method':'GET','url':'https://api.github.com/repos/ed3c/soodles/pulls/2'}, 'provider subject guessed')
            require(result['next'].get('argv') == [sys.executable, '-B', str(cli_root / 'soodles.py'), 'landing', 'advance', str(cp.resolve()), str(sf.resolve())], 'known continuation lost exact argv')
            require(result['next']['required'] == ['readback'] and result['next']['known'].get('readback') == str(sf.resolve()), 'argv bypassed required fresh readback')
            return cp
        cp = fresh('prepared')
        r = execute(['advance',cp,sf], kill='advance')
        require(r.returncode == -signal.SIGKILL, 'pre-dispatch injection did not kill the real child')
        result = invoke(['advance',cp,sf])
        require(result.get('next', {}).get('operation') == 'dispatch', 'prepared intent lacks fresh dispatch readback')
        require(result.get('action') == 'dispatch', 'saved intent without transport cannot resume first dispatch')
        require(json.loads(cp.read_text())['writes_offered'] == [], 'prepared intent already counted as offered')
        require(json.loads(sink.read_text()) == [], 'provider changed before dispatch')
        request = invoke(['dispatch',cp,sf])['request']
        expected = {'action':'merge','repository_full_name':'ed3c/soodles','pr_number':2,
                    'expected_head_sha':'a'*40,'merge_method':'merge'}
        require(request == expected, 'dispatch changed exact merge identity')
        require(json.loads(cp.read_text())['writes_offered'] == ['merge'], 'dispatch was not durably consumed')
        require(execute(['dispatch',cp,sf]).returncode != 0, 'duplicate merge dispatch admitted')
        require(invoke(['advance',cp,sf])['action'] == 'readback', 'unknown merge outcome authorized retry')
        cases.append({'case':'prepared_sigkill_resume','signal':'SIGKILL','first_dispatches':1})
        # The supervisor transport fixture commits the request; response/ack is deliberately lost.
        sink.write_text(json.dumps([request]))
        snapshot['pr'].update(merged=True,state='closed',merged_at='2026-09-15T00:00:00Z',merge_commit_sha='d'*40)
        snapshot['merge_commit']={'sha':'d'*40,'tree':{'sha':'b'*40},'parents':[{'sha':'c'*40},{'sha':'a'*40}]}
        write(sf,snapshot)
        # Dependent merged-commit readback is owned here, not reconstructed by a skill.
        correct = json.loads(json.dumps(snapshot))
        before = cp.read_bytes()
        expected_get = {'method':'GET','url':'https://api.github.com/repos/ed3c/soodles/git/commits/'+'d'*40}
        bad_cases = [
            ('missing', None, 'merge_commit', None),
            ('shape', [], 'merge_commit', []),
            ('sha', {'sha':'e'*40,'tree':{'sha':'b'*40},'parents':[{'sha':'c'*40},{'sha':'a'*40}]}, 'merge.sha', 'e'*40),
            ('parents', {'sha':'d'*40,'tree':{'sha':'b'*40},'parents':[{'sha':'a'*40},{'sha':'c'*40}]}, 'merge.parents', [{'sha':'a'*40},{'sha':'c'*40}]),
            ('parent-shape', {'sha':'d'*40,'tree':{'sha':'b'*40},'parents':[None]}, 'merge.parents', [None]),
            ('tree', {'sha':'d'*40,'tree':{'sha':'e'*40},'parents':[{'sha':'c'*40},{'sha':'a'*40}]}, 'merge.tree', 'e'*40),
            ('tree-shape', {'sha':'d'*40,'tree':None,'parents':[{'sha':'c'*40},{'sha':'a'*40}]}, 'merge.tree', None),
        ]
        for operation in ('advance','dispatch'):
            for label, value, field, invalid in bad_cases:
                bad = json.loads(json.dumps(correct))
                if label == 'missing': bad.pop('merge_commit')
                else: bad['merge_commit'] = value
                write(sf,bad)
                r=execute([operation,cp,sf])
                require(r.returncode != 0, 'invalid merge evidence admitted')
                out=json.loads(r.stdout)
                require(out.get('owner')=='landing.'+operation and out.get('invalid')=={'field':field,'value':invalid},
                        'merge refusal lost exact field/value or owner')
                nxt=out.get('next',{})
                require(nxt.get('kind')=='provider_readback' and nxt.get('owner')=='GitHub','merge lacks owning provider readback')
                require(nxt.get('operation')==operation,'merge routes to wrong operation')
                require(nxt.get('known',{}).get('checkpoint')==str(cp.resolve()),'merge lost checkpoint')
                require(nxt.get('requests',{}).get('merge_commit')==expected_get,'merge request has wrong subject')
                require(nxt.get('argv') == [sys.executable, '-B', str(cli_root / 'soodles.py'), 'landing', operation, str(cp.resolve()), str(sf.resolve())] and 'request' not in out, 'merge refusal emitted a write or guessed argv')
                require(nxt['required'] == ['readback'] and nxt['known'].get('readback') == str(sf.resolve()), 'merge argv bypassed required readback')
                require(expected_get['url'] in r.stderr and nxt.get('reason','!') in r.stderr,'merge human and machine guidance disagree')
                require(cp.read_bytes()==before,'merge refusal changed checkpoint')
        # The URL cannot be derived from an invalid PR SHA or a foreign/stale subject.
        for sha in (None, 'HEAD', '../other', 'd'*39, 'D'*40):
            bad=json.loads(json.dumps(correct)); bad['pr']['merge_commit_sha']=sha
            write(sf,bad); r=execute(['advance',cp,sf]); out=json.loads(r.stdout)
            require(r.returncode!=0 and out.get('invalid')=={'field':'pr.merge_commit_sha','value':sha},'invalid PR merge SHA not rejected')
            nxt=out.get('next',{})
            require(nxt.get('kind')=='provider_readback' and nxt.get('operation')=='advance','missing merge SHA lacks fresh PR readback')
            require(nxt.get('requests',{}).get('pr')=={'method':'GET','url':'https://api.github.com/repos/ed3c/soodles/pulls/2'},'missing merge SHA lost PR subject')
            require('merge_commit' not in nxt.get('requests',{}),'invalid PR SHA became a commit request')
            require('request' not in out and cp.read_bytes()==before,'invalid PR SHA changed delivery')
        for label in ('foreign','head'):
            bad=json.loads(json.dumps(correct)); bad.pop('merge_commit')
            if label=='foreign': bad['pr']['head']['repo']={'full_name':'other/repository'}
            else: bad['pr']['head']['sha']='f'*40
            write(sf,bad); r=execute(['advance',cp,sf]); out=json.loads(r.stdout)
            require(r.returncode!=0 and 'requests' not in out.get('next',{}),'unconfirmed identity produced provider guidance')
            require(cp.read_bytes()==before,'foreign/stale subject changed checkpoint')
        # Legacy offered history is neither erased nor re-offered by a readback repair.
        legacy=lane/'merge-readback-legacy.json'; old=json.loads(cp.read_text())
        old['schema']=1; old.pop('delivery'); write(legacy,old)
        if isolated: os.chown(legacy,65534,65534)
        bad=json.loads(json.dumps(correct)); bad.pop('merge_commit'); write(sf,bad)
        legacy_before=legacy.read_bytes(); r=execute(['advance',legacy,sf])
        require(r.returncode!=0 and legacy.read_bytes()==legacy_before,'missing legacy readback changed history')
        write(sf,correct)
        repaired=invoke(['advance',legacy,sf])
        require(repaired.get('action')=='dispatch' and repaired.get('classification') is None,'fresh merge readback cannot prepare close')
        require(json.loads(legacy.read_text())['writes_offered']==['merge'],'legacy readback repeated merge')
        cases.append({'case':'merge_commit_readback_recovery','malformed_controls':14,'invalid_sha_controls':5,
                      'foreign_stale_controls':2,'legacy_history_preserved':True,'provider_fixture':True})
        write(sf,correct)
        r = execute(['advance',cp,sf],kill='advance')
        require(r.returncode == -signal.SIGKILL, 'close prepare injection did not kill child')
        require(invoke(['advance',cp,sf])['action']=='dispatch','prepared close cannot resume')
        close = invoke(['dispatch',cp,sf])['request']
        require(close=={'action':'close','repository_full_name':'ed3c/soodles','issue_number':1,'state':'closed','state_reason':'completed'},'wrong closure')
        require(execute(['dispatch',cp,sf]).returncode!=0,'duplicate closure admitted')
        require(invoke(['advance',cp,sf])['action']=='readback','unknown close authorized retry')
        sink.write_text(json.dumps([request,close]))
        snapshot['issue'].update(state='closed',state_reason='completed',closed_at='2026-09-15T00:01:00Z')
        write(sf,snapshot)
        require(invoke(['advance',cp,sf])['action']=='reconcile','committed effects did not recover through readback')
        require(json.loads(cp.read_text())['classification'] is None,'provider fixture claimed local reconciliation')
        require(json.loads(cp.read_text())['writes_offered']==['merge','close'],'lost response repeated write')
        cases.append({'case':'lost_response_and_close_prepare_crash','provider_fixture_effects':2,'phase':'awaiting_reconcile'})
        write(sf,original)
        cp = fresh('dispatch-gap'); invoke(['advance',cp,sf])
        r = execute(['dispatch',cp,sf],kill='dispatch')
        require(r.returncode==-signal.SIGKILL,'dispatch checkpoint injection did not kill child')
        require(invoke(['advance',cp,sf])['action']=='readback','dispatch gap guessed not sent')
        require(execute(['dispatch',cp,sf]).returncode!=0,'dispatch gap reoffered unknown write')
        cases.append({'case':'dispatch_gap_unknown','signal':'SIGKILL','reoffers':0})
        cp = fresh('concurrent'); invoke(['advance',cp,sf])
        # Start two independent consumers against the same durable checkpoint.
        argv=[sys.executable,'-B',str(cli_root/'soodles.py'),'landing','dispatch',str(cp),str(sf)]
        env={k:os.environ[k] for k in ('PATH','LANG','LC_ALL','TMPDIR') if k in os.environ}
        ps=[subprocess.Popen(argv,cwd=lane,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                             user=65534 if isolated else None,group=65534 if isolated else None) for _ in range(2)]
        outputs=[p.communicate(timeout=20) for p in ps]
        require(sum(p.returncode==0 for p in ps)==1,'concurrent consumers did not produce exactly one request')
        require([json.loads(o[0])['request'] for p,o in zip(ps,outputs) if p.returncode==0]==[expected],'concurrent request identity changed')
        cases.append({'case':'concurrent_dispatch','processes':2,'requests':1})
        for action in ('merge','close'):
            state=json.loads(cp.read_text()); state['schema']=1; state.pop('delivery',None)
            state['phase']=action+'_pending'; state['writes_offered']=['merge'] if action=='merge' else ['merge','close']
            if action=='close':
                state['merge_sha']='d'*40
                observation=json.loads(json.dumps(snapshot)); observation['issue']=original['issue']
            else: observation=original
            legacy=lane/('legacy-'+action+'.json'); write(legacy,state)
            if isolated: os.chown(legacy,65534,65534)
            write(sf,observation)
            require(invoke(['advance',legacy,sf])['action']=='readback','legacy missing evidence assumed prepared')
            require(execute(['dispatch',legacy,sf]).returncode!=0,'legacy write was reoffered')
        cases.append({'case':'legacy_unknown','merge_and_close_reoffers':0})
        write(sf,original); cp=fresh('identity'); invoke(['advance',cp,sf])
        changed=json.loads(json.dumps(original)); changed['pr']['head']['sha']='f'*40
        write(sf,changed); before=cp.read_bytes()
        r=execute(['dispatch',cp,sf])
        require(r.returncode!=0 and 'pr.head.sha' in r.stderr,'changed head not refused by field')
        require(cp.read_bytes()==before,'invalid identity consumed prepared intent')
        cases.append({'case':'head_drift','requests':0,'checkpoint_unchanged':True})
        refusal = json.loads(r.stdout)
        require(refusal.get('owner') == 'landing.dispatch', 'field prefix guessed wrong owner')
        require(refusal.get('invalid') == {'field':'pr.head.sha','value':'f'*40}, 'refusal lost actual field/value')
        require(refusal['next']['operation'] == 'dispatch', 'identity correction lost owning action')
        write(sf,original)
        invoke(['invalidate',cp])
        r=execute(['dispatch',cp,sf]); refusal=json.loads(r.stdout)
        require(r.returncode!=0 and refusal['next']['operation']=='readmit', 'invalidated dispatch has conflicting route')
        require('landing readmit --help' in r.stderr and 'landing dispatch --help' not in r.stderr,
                'human refusal disagrees with structured next')
        require(refusal['next']['required']==['claim','readback'], 'fresh admission inputs are guessed')
        require('argv' not in refusal['next'], 'missing fresh claim was executable')
        require('next' not in json.loads(cp.read_text()), 'next command persisted as authority')
        cases.append({'case':'structured_owner_refusal','conflicting_routes':0,'provider_requests':0})
        # A resolved checkpoint is fixture input, not a claim of live reconciliation.
        terminal=json.loads(cp.read_text())
        terminal.update(phase='resolved',classification='RESOLVED',writes_offered=['merge','close'],merge_sha='d'*40,
                        issue_closed_at=snapshot['issue']['closed_at'],local={'fixture':True})
        terminal.pop('recovery',None)
        write(cp,terminal)
        if isolated: os.chown(cp,65534,65534)
        write(sf,snapshot); before=cp.read_bytes()
        stopped=invoke(['advance',cp,sf])
        require(stopped.get('action')=='stop' and stopped.get('next','missing') is None,
                'resolved checkpoint still requests readback')
        require(cp.read_bytes()==before, 'terminal observation rewrote checkpoint')
        cases.append({'case':'terminal_projection','next':None,'checkpoint_unchanged':True})
        require(json.loads(sink.read_text())==[request,close],'child modified supervisor provider fixture')
    return {'scope':'local durable checkpoint/process faults; supervisor provider fixture, no GitHub writes',
            'cases':cases,'isolated_child_uid':65534 if isolated else None,'authorizes_landing':False}


if __name__=='__main__':
    try:
        result=delivery_probe(sys.argv[1], '--isolated' in sys.argv[2:])
        print(json.dumps(result,indent=2))
    except (RuntimeError,ValueError,OSError,subprocess.TimeoutExpired) as exc:
        print(json.dumps({'verdict':'NOT VERIFIED','reason':str(exc),'authorizes_landing':False}))
        sys.exit(1)
