"""Fresh context consumes a previous real consumer's exact handoff."""
import hashlib,json,os,subprocess,sys
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source,label,target,context=sys.argv[1:];root=Path(target);root.mkdir(parents=True)
 choice=json.loads(Path(context).read_text());prior=Path(choice['prior_facts'])
 if sha(prior)!=choice['prior_facts_sha256']:raise ValueError('parent facts changed')
 facts=json.loads(prior.read_text());receipt=Path(facts['task']['raw_cli_receipt'])
 if sha(receipt)!=choice['receipt_sha256']:raise ValueError('parent receipt changed')
 prepared=json.loads(receipt.read_text());handoff=json.loads(Path(facts['task']['handoff']).read_text())
 if handoff!={'receipt':{'path':str(receipt)},'next':prepared['next']}:raise ValueError('parent did not preserve exact handoff')
 control=Path(facts['control_root']);before=subprocess.check_output(['git','rev-parse','HEAD'],cwd=control,text=True).strip()
 if before!=choice['prior_head']:raise ValueError('parent HEAD changed before deliberate drift')
 (control/'work-item.txt').write_text('new disposable state after actual consumer preparation\n')
 env=dict(os.environ);env.update(GIT_AUTHOR_NAME='Fixture',GIT_COMMITTER_NAME='Fixture',GIT_AUTHOR_EMAIL='fixture@example.invalid',GIT_COMMITTER_EMAIL='fixture@example.invalid')
 subprocess.run(['git','add','work-item.txt'],cwd=control,env=env,check=True,capture_output=True)
 subprocess.run(['git','commit','-m','Advance disposable state after saved handoff'],cwd=control,env=env,check=True,capture_output=True)
 after=subprocess.check_output(['git','rev-parse','HEAD'],cwd=control,text=True).strip()
 (root/'handoff').mkdir();(root/'work-output').mkdir()
 (root/'handoff/prepared.json').write_bytes(receipt.read_bytes())
 facts.update(work_id=label,authorization=prepared['authorization'],prepared_handoff=str(root/'handoff/prepared.json'))
 facts['host']['environment'].update(prepared['next']['environment'])
 facts['task']={'raw_cli_receipt':str(root/'work-output/raw-cli-receipt.json'),'handoff':str(root/'work-output/handoff.json')}
 (root/'workspace.json').write_text(json.dumps(facts,indent=2)+'\n')
 (root/'work.md').write_text('''# Continue the saved local work

A previous Session saved the actual preparation receipt in handoff/prepared.json. Use its exact next.argv and environment to obtain one current owner result. Save actual stdout unchanged to work-output/raw-cli-receipt.json and {"receipt":{"path":"absolute raw receipt path"},"next": ...} to work-output/handoff.json with next unchanged. Stop after that result. Preserve selected identity; do not repair, replace or refresh authorization or use provider transport. Report the observed result.
''')
 print(json.dumps({'parent_facts_sha256':sha(prior),'actual_parent_receipt_sha256':sha(receipt),'head_before':before,'head_after':after,'provider_transport':False}))
if __name__=='__main__':main()
