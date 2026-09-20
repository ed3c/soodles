You are a fresh landing supervisor consumer. Do not execute commands or modify files. A fresh provider readback is already stored at /tmp/readback-B.json and the durable checkpoint is /tmp/checkpoint-B.json. Return exactly one JSON object with keys argv (an argv string array) and reason (one short sentence). Select the single supported CLI invocation that consumes this current readback.

Selected instruction context:
For landing, consume the invoked owner's current owner, action, next, invalid and, when emitted, request. Follow the returned operation/help using confirmed inputs. A historical next action is trace evidence only. The owning action rechecks current state before an effect.

Durable checkpoint summary:
{"delivery": {"action": "merge", "status": "prepared"}, "phase": "merge_pending", "writes_offered": []}

CLI help:
usage: ./soodles landing [-h]
                         {identity,start,advance,dispatch,resume,invalidate,readmit,reconcile}
                         ...

The supervisor supplies exact claims and raw provider readbacks. No
credentials or provider writes in this process.

positional arguments:
  {identity,start,advance,dispatch,resume,invalidate,readmit,reconcile}

options:
  -h, --help            show this help message and exit

Examples: ./soodles landing start --help; ./soodles landing advance --help;
./soodles landing reconcile --help

