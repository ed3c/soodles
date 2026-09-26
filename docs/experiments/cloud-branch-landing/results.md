# Cloud branch landing claim mapping

The actual #157 activation at head `1b32e98cd802d93a3c492c9366c99008a240c32d` refused before checkpoint or provider request: `landing-supervisor` copied the provider branch `cloud/157-pclass-case-exposure` to `claim.worktree`, and the selected publisher rejected that value. The original refusal and selected publisher digest are recorded in `raw/baseline.json`; no unknown provider write needs a retry.

The #177 candidate fixture now gives Cloud a safe `worktree` label (`cloud-122` in the fixture) and binds the exact PR branch in `publication_branch`. The existing landing owner reaches its `provider_readback` next. A changed PR branch and an unsafe worktree refuse; the Local canonical publication branch and ordinary slash-free Cloud branch remain covered by existing controls. `raw/candidate.json` is a local fixture receipt, not an independent publisher or actual #157 landing result.

The focused landing-supervisor module passed 9 tests. A wider macOS local drive of the landing test modules passed 73 of 74 tests and failed only the pre-existing `test_landing_continuation` path-binding observer. The unchanged main checkout fails that same test; the observed path-binding errors are consistent with macOS `/var` versus resolved `/private/var` paths. The failure is preserved in `raw/tests.txt`; this atom does not edit that unrelated observer or disable the test. Linux exact-head Actions must pass before delivery.

#157 remains blocked until this corrective atom is landed, a compatible external publisher is separately selected, and fresh #157 provider readback is consumed. Its six behavior runs are unchanged.
