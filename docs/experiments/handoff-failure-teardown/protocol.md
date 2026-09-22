# Handoff observer failure-teardown control

Source: c14774b72a0c667fc6333d52b31fddb4da737d35. Origin is the active full-map
qualification goal; no new Issue or model sample is implied by this diagnostic.

The current handoff oracle starts a process, waits for a projection and then
stops it. Its outer finally restores an environment variable, not the process.
Test one first-projection failure under a bounded unit seam before any repair.

Invoke the actual handoff_probe source. Stub only unrelated Git/Noodle fixture
initialization and replace its _start seam with a real harmless Python child
that signals readiness and waits. The supplied Noodle path is the measured
existing executable, but it is NEVER executed by this control. No alternative
Noodle, real model, production scheduler, provider operation or worktree is
started. This tests oracle-owned process cleanup, NOT real Noodle handoff.

After readiness, inject a single wait failure. Fixed expected behavior: retain
that primary failure while stopping/reaping the owned child before leaving the
fixture. Observe poll/kernel liveness and fixture path before external cleanup.
If it leaked, the independent harness uses the existing stop helper to stop and
wait for its one known child and confirms absence. That bounded emergency
cleanup cannot turn the subject's failed cleanup into success. Preserve argv,
source hash, actual exception, observations and cleanup result outside fixture.

One baseline control; no repeated fault searching. A later candidate uses these
same external bytes/criteria. Positive nearest control is successful explicit
stop of the same harmless child during harness cleanup. Missing capability is
INCONCLUSIVE. No product changes, new permission/CLI flags or generalized runner.
This is deterministic fault sensitivity, not natural P-class behavior or a
fresh baseline/treatment efficacy comparison. Linux full physical handoff still
requires its selected runtime and canonical owner; no macOS substitute claim.
