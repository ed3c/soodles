#!/usr/bin/env python3
"""Process-kill boundary observer for this experiment; never part of the product."""
import io,json,os,signal,sys
from pathlib import Path


def main():
    control,selection,selected_sha,output,point,event_path=sys.argv[1:]
    sys.path.insert(0,control)
    import supervisor_admission as owner
    target=Path(output)
    original_open=io.open
    owner_file=str(Path(owner.__file__).resolve())
    def kill(path):
        # Persist which actual boundary was reached; failure to reach it is INVALID.
        event={'point':point,'observed_path':str(path),'final_authorization_exists':(target/'authorization.json').is_file(),
               'final_prepared_exists':(target/'prepared.json').is_file(),'signal':'SIGKILL'}
        with original_open(event_path,'w') as stream:
            stream.write(json.dumps(event,sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())
        os.kill(os.getpid(),signal.SIGKILL)
    class ReceiptStream:
        def __init__(self,stream,path):self.stream,self.path=stream,path
        def __getattr__(self,name):return getattr(self.stream,name)
        def __enter__(self):self.stream.__enter__();return self
        def __exit__(self,*args):
            result=self.stream.__exit__(*args)
            if args[0] is None:kill(self.path)
            return result
    def observed_open(file,mode='r',*args,**kwargs):
        is_receipt=isinstance(file,(str,bytes,os.PathLike)) and Path(file).name in ('.prepared.json','prepared.json') and any(c in mode for c in ('w','x','a'))
        if is_receipt and point=='before_receipt_write':kill(file)
        stream=original_open(file,mode,*args,**kwargs)
        return ReceiptStream(stream,file) if is_receipt and point=='after_receipt_write' else stream
    def trace(frame,event,arg):
        if frame.f_code.co_filename==owner_file and event in ('line','return') and (target/'prepared.json').is_file() and (target/'authorization.json').is_file():
            kill(target/'prepared.json')
        return trace
    if point not in ('before_receipt_write','after_receipt_write','after_publication'):raise ValueError('unsupported fault')
    io.open=observed_open
    if point=='after_publication':sys.settrace(trace)
    sys.argv=[str(Path(control)/'supervisor-admission'),'authorize',selection,selected_sha,output]
    status=owner.main()
    sys.settrace(None)
    raise SystemExit(status)

if __name__=='__main__':main()
