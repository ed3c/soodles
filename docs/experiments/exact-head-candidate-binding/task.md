# Exact-head candidate binding task

Drive one read-only candidate-verification entry against real Git commits.

The fixed observer owns three cases:

1. candidate instruction bytes differ from the manifest treatment digest;
2. observer bytes and their candidate manifest digest change together but differ
   from the externally frozen Issue digest;
3. instruction, evidence manifest, required artifacts and external pins all
   match the exact candidate tree.

The baseline entry is absent, so both invalid candidates remain admitted.  The
treatment must refuse the first two cases at their exact fields and admit the
complete candidate.  The observer performs no provider write and no receipt
authorizes landing.
