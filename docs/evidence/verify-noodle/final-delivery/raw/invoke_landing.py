from pathlib import Path
import importlib.util,json,sys
r=Path(__file__).parent
spec=importlib.util.spec_from_file_location('record',Path('/Users/neon/soodles/.agents/skills/verify-soodles/scripts/record_context.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
label=sys.argv[1];result,stdout,stderr=m.record(r/'landing-records',label,[sys.executable,'-B',str(r/'publisher/soodles.py'),'landing',*sys.argv[2:]])
if stdout:
 value=json.loads(stdout);(r/(label+'.json')).write_bytes(stdout);print(json.dumps(value))
else:print(json.dumps({'recorder':result,'stderr':stderr.decode()}))
raise SystemExit(result['exit_code'])
