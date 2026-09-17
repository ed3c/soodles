from pathlib import Path
import subprocess,selectors,json,time,signal,os,shutil,sys
r=Path(__file__).parent;runtime=r/'live/runtime';out=r/'native';out.mkdir()
s=json.loads((runtime/'state.snapshot.json').read_text());a=s['state']['orders']['soodles-39']['stages'][0]['attempts'][-1];sid=a['session_id'];raw=runtime/'sessions'/sid/'raw.ndjson'
events=[json.loads(line) for line in raw.read_text().splitlines() if line];starts=[e for e in events if e.get('type')=='thread.started'];assert len(starts)==1;thread=starts[0]['thread_id']
requests=[{'id':1,'method':'initialize','params':{'clientInfo':{'name':'soodles39-readonly-observer','version':'1'},'capabilities':{'experimentalApi':True}}},{'id':2,'method':'thread/read','params':{'threadId':thread,'includeTurns':True}}]
responses={};start=time.monotonic();status='timeout'
with (out/'stderr.log').open('wb') as err,(out/'stdout.jsonl').open('wb') as log,(out/'requests.jsonl').open('w') as sent:
 p=subprocess.Popen(['/Users/neon/.codex/packages/standalone/releases/0.153.4-aarch64-apple-darwin/bin/codex','app-server','--stdio'],cwd=r,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,start_new_session=True)
 sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ);buffer=b''
 def send(request):
  sent.write(json.dumps(request)+'\n');sent.flush();p.stdin.write((json.dumps(request)+'\n').encode());p.stdin.flush()
 send(requests[0])
 while time.monotonic()-start<30 and p.poll() is None:
  for key,_ in sel.select(.2):
   chunk=os.read(key.fd,65536)
   if not chunk:status='eof';break
   log.write(chunk);log.flush();buffer+=chunk
   while b'\n' in buffer:
    line,buffer=buffer.split(b'\n',1)
    if not line:continue
    msg=json.loads(line)
    if msg.get('id') in (1,2):responses[msg['id']]=msg
    if msg.get('id')==1:
     if 'error' in msg:status='initialize_error';break
     send({'method':'initialized','params':{}});send(requests[1])
    if msg.get('id')==2:status='read_error' if 'error' in msg else 'read_ok'
  if status!='timeout':break
 if p.poll() is None:
  p.stdin.close()
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.send_signal(signal.SIGTERM);p.wait(timeout=5)
 (out/'observation.json').write_text(json.dumps({'status':status,'exit':p.returncode,'pid':p.pid,'thread_id':thread,'noodle_session':sid,'elapsed_seconds':time.monotonic()-start,'new_model_turns':0},indent=2)+'\n')
 history=responses.get(2,{});(out/'history.json').write_text(json.dumps(history,indent=2)+'\n')
 data=history.get('result',{}).get('thread',{});path=data.get('path')
 if path and Path(path).is_file():
  content=Path(path).read_bytes();lines=[json.loads(x) for x in content.splitlines() if x]
  assert any(x.get('type')=='session_meta' and x.get('payload',{}).get('id')==thread for x in lines)
  (out/'rollout.jsonl').write_bytes(content)
 print(json.dumps({'status':status,'thread':thread,'history_mode':data.get('historyMode'),'history_model':data.get('model'),'turns':len(data.get('turns',[])),'path':path,'rollout_copied':(out/'rollout.jsonl').exists()}))
