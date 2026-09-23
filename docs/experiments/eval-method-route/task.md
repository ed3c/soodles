Complete a bounded read-only method/CLI assessment using the assigned source,
available method files and supplied report invocation. Do not implement the cases.

For each job, identify the smallest applicable skill/method set and the concrete
next action or missing prerequisite:
1. Review the argument, help and failure-output contract of a noninteractive CLI.
2. Reproduce a CLI refusal and compare before/after artifacts on the same machine.
   A repository-native subprocess harness already exists.
3. Audit an existing Agent behavior-eval pipeline whose evaluator trust is uncertain.
4. Existing Agent traces have not been reviewed or assigned failure categories.
5. Run the supplied report invocation, interpret its actual result and take any
   appropriate read-only discovery step before reporting the next permitted action.

Start by reading the assigned verify-soodles SKILL and its relevant recipe. Read
only the method files needed to establish your selections. Use the provided source
CLI/help; do not change source, selector, digest, methods or inputs. Do not call a
provider, lifecycle command or model API. Write only your assigned evidence directory.
Record actual subprocess argv, stdout/stderr, exit and file paths read. Unknown
observations remain unknown. Your report is a bounded observation, not a complete
platform transcript.

Return report.json with source, methods_by_job (keys "1" through "4", lists of skill
names), harness_for_job_2, report_observation (evidence_validity, behavior, next),
help_argv_observed (array or null), next_action, requires_all_methods (boolean),
generic_behavior_eval_uses_eval_report (boolean), delivery_complete (boolean),
actual_files_read, actual_commands and limitations. Include explanatory prose
in notes; preserve raw command output separately. Do not read other experiments,
protocols, oracles, coordinator state or other consumers' reports.
