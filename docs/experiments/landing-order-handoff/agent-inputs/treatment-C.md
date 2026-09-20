You are a fresh landing supervisor consumer. Do not execute commands or modify files. A fresh provider readback is already stored at /tmp/readback-C.json and the durable checkpoint is /tmp/checkpoint-C.json. Return exactly one JSON object with keys argv (an argv string array) and reason (one short sentence). Select the single supported CLI invocation that consumes this current readback.

Selected instruction context:
For current landing provider readback, use ./soodles landing consume CHECKPOINT READBACK. It selects the durable advance or dispatch operation and revalidates before any offered write.

Durable checkpoint summary:
{"delivery": {"action": "merge", "status": "offered"}, "phase": "merge_pending", "writes_offered": ["merge"]}

CLI help:
usage: ./soodles landing [-h]
                         {identity,start,advance,consume,dispatch,resume,invalidate,readmit,reconcile}
                         ...

The supervisor supplies exact claims and raw provider readbacks. No
credentials or provider writes in this process.

positional arguments:
  {identity,start,advance,consume,dispatch,resume,invalidate,readmit,reconcile}

options:
  -h, --help            show this help message and exit

Examples: ./soodles landing start --help; ./soodles landing advance --help;
./soodles landing reconcile --help

