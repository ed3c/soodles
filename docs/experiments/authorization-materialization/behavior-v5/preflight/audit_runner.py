import os,sys,json,runpy
log=open(sys.argv[1],'w'); entry=sys.argv[2]; sys.argv=sys.argv[2:]
def audit(event,args):
 if event in ('tempfile.mkdtemp','os.mkdir','os.rmdir','os.remove','os.rename','open'):
  log.write(json.dumps({'event':event,'args':list(args)},default=str)+'\n');log.flush()
sys.addaudithook(audit)
sys.path.insert(0,os.path.dirname(entry))
runpy.run_path(entry,run_name='__main__')
