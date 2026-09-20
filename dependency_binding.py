"""Source-owned cross-repository dependency eligibility.

The claim selects an already registered consumer.  This module only validates
fresh provider readback for its registered producer result; it owns no effects,
scheduler, retry loop or lifecycle state.
"""
import re


EDGES = {
    ("ed3c/ops-reconciliation-copilot", 21): {
        "producer": "ed3c/soodles",
        "issue": 111,
        "pr": 112,
        "base_ref": "main",
        "base_head": "db5dd0c7e46ba5c8fe5270907b229688326fc8f4",
        "candidate_head": "498f384337609fc2a76c1cb293aa100e5d639b0d",
        "tree": "85fb13afdf603baccf1ee7644b209e40dfd25d88",
        "revision": "b7dd55ab1074d28afe83dae3a469fc5e6f5ad36d",
        "run_id": 35541786068,
        "run_attempt": 1,
        "workflow_path": ".github/workflows/runtime.yml",
        "jobs": {
            "runtime-evidence": ["Canonical acceptance on the exact candidate head"],
        },
    },
}


def edge(claim):
    if not isinstance(claim, dict):
        return None
    return EDGES.get((claim.get("repository"), claim.get("issue")))


def requests(claim):
    """Return exact read-only provider requests for a registered edge."""
    selected = edge(claim)
    if selected is None:
        return {}
    base = f"https://api.github.com/repos/{selected['producer']}/"
    paths = {
        "dependency_issue": f"issues/{selected['issue']}",
        "dependency_pr": f"pulls/{selected['pr']}",
        "dependency_commit": f"git/commits/{selected['revision']}",
        "dependency_branch": f"branches/{selected['base_ref']}",
        "dependency_ancestry": f"compare/{selected['revision']}...{selected['base_ref']}",
        "dependency_run": f"actions/runs/{selected['run_id']}",
        "dependency_jobs": f"actions/runs/{selected['run_id']}/jobs",
    }
    return {name: {"method": "GET", "url": base + path}
            for name, path in paths.items()}


def validate(claim, snapshot, require, next_action):
    """Validate one producer result before the consumer landing owner runs."""
    selected = edge(claim)
    if selected is None:
        return None

    def need(condition, field, value):
        require(condition, field, value, next_action)

    producer = selected["producer"]
    issue = snapshot.get("dependency_issue")
    need(isinstance(issue, dict), "dependency.issue", issue)
    need(issue.get("url") == f"https://api.github.com/repos/{producer}/issues/{selected['issue']}",
         "dependency.issue.url", issue.get("url"))
    need(issue.get("html_url") == f"https://github.com/{producer}/issues/{selected['issue']}",
         "dependency.issue.html_url", issue.get("html_url"))
    need(issue.get("number") == selected["issue"], "dependency.issue.number", issue.get("number"))
    need(issue.get("state") == "closed" and issue.get("state_reason") == "completed"
         and bool(issue.get("closed_at")), "dependency.issue.closure",
         {"state": issue.get("state"), "state_reason": issue.get("state_reason"),
          "closed_at": issue.get("closed_at")})

    pr = snapshot.get("dependency_pr")
    need(isinstance(pr, dict), "dependency.pr", pr)
    need(pr.get("number") == selected["pr"], "dependency.pr.number", pr.get("number"))
    need(pr.get("html_url") == f"https://github.com/{producer}/pull/{selected['pr']}",
         "dependency.pr.html_url", pr.get("html_url"))
    head_repo = (pr.get("head") or {}).get("repo") or {}
    base_repo = (pr.get("base") or {}).get("repo") or {}
    need(head_repo.get("full_name") == producer and base_repo.get("full_name") == producer,
         "dependency.pr.repository",
         {"head": head_repo.get("full_name"), "base": base_repo.get("full_name")})
    need((pr.get("head") or {}).get("sha") == selected["candidate_head"],
         "dependency.pr.head", (pr.get("head") or {}).get("sha"))
    need((pr.get("base") or {}).get("sha") == selected["base_head"]
         and (pr.get("base") or {}).get("ref") == selected["base_ref"],
         "dependency.pr.base", pr.get("base"))
    need(pr.get("state") == "closed" and pr.get("merged") is True and bool(pr.get("merged_at")),
         "dependency.pr.merge", {"state": pr.get("state"), "merged": pr.get("merged"),
                                  "merged_at": pr.get("merged_at")})
    need(pr.get("merge_commit_sha") == selected["revision"],
         "dependency.pr.revision", pr.get("merge_commit_sha"))

    commit = snapshot.get("dependency_commit")
    need(isinstance(commit, dict), "dependency.commit", commit)
    need(commit.get("sha") == selected["revision"],
         "dependency.commit.sha", commit.get("sha"))
    need((commit.get("tree") or {}).get("sha") == selected["tree"],
         "dependency.commit.tree", (commit.get("tree") or {}).get("sha"))
    parents = commit.get("parents")
    need(isinstance(parents, list) and len(parents) == 2
         and all(isinstance(parent, dict) for parent in parents)
         and [parent.get("sha") for parent in parents]
         == [selected["base_head"], selected["candidate_head"]],
         "dependency.commit.parents", parents)

    branch = snapshot.get("dependency_branch")
    need(isinstance(branch, dict), "dependency.branch", branch)
    need(branch.get("name") == selected["base_ref"],
         "dependency.branch.name", branch.get("name"))
    current = (branch.get("commit") or {}).get("sha")
    need(isinstance(current, str) and re.fullmatch("[0-9a-f]{40}", current),
         "dependency.branch.head", current)

    ancestry = snapshot.get("dependency_ancestry")
    need(isinstance(ancestry, dict), "dependency.ancestry", ancestry)
    need((ancestry.get("base_commit") or {}).get("sha") == selected["revision"],
         "dependency.ancestry.base", (ancestry.get("base_commit") or {}).get("sha"))
    need((ancestry.get("merge_base_commit") or {}).get("sha") == selected["revision"],
         "dependency.ancestry.merge_base",
         (ancestry.get("merge_base_commit") or {}).get("sha"))
    status = ancestry.get("status")
    need(status in {"identical", "ahead"}, "dependency.ancestry.status", status)
    need((ancestry.get("head_commit") or {}).get("sha") == current,
         "dependency.ancestry.head", (ancestry.get("head_commit") or {}).get("sha"))
    commits, total = ancestry.get("commits"), ancestry.get("total_commits")
    if status == "identical":
        need(current == selected["revision"] and commits == [] and total == 0,
             "dependency.ancestry.identical",
             {"head": current, "commits": commits, "total_commits": total})
    else:
        need(isinstance(commits, list) and bool(commits)
             and all(isinstance(item, dict) for item in commits)
             and type(total) is int and total == len(commits)
             and commits[-1].get("sha") == current,
             "dependency.ancestry.commits", commits)

    run = snapshot.get("dependency_run")
    need(isinstance(run, dict), "dependency.run", run)
    need(run.get("id") == selected["run_id"]
         and run.get("run_attempt") == selected["run_attempt"],
         "dependency.run.identity", {"id": run.get("id"), "attempt": run.get("run_attempt")})
    need((run.get("repository") or {}).get("full_name") == producer
         and (run.get("head_repository") or {}).get("full_name") == producer,
         "dependency.run.repository",
         {"repository": (run.get("repository") or {}).get("full_name"),
          "head_repository": (run.get("head_repository") or {}).get("full_name")})
    need(run.get("head_sha") == selected["candidate_head"],
         "dependency.run.head", run.get("head_sha"))
    need(run.get("event") == "pull_request"
         and run.get("path") == selected["workflow_path"],
         "dependency.run.workflow", {"event": run.get("event"), "path": run.get("path")})
    need(run.get("status") == "completed" and run.get("conclusion") == "success",
         "dependency.run.conclusion", run.get("conclusion"))

    jobs = snapshot.get("dependency_jobs")
    need(isinstance(jobs, dict), "dependency.jobs", jobs)
    raw_jobs = jobs.get("jobs", [])
    observed = {job.get("name"): job for job in raw_jobs
                if isinstance(job, dict)}
    need(isinstance(raw_jobs, list)
         and jobs.get("total_count") == len(raw_jobs) == len(observed) == len(selected["jobs"])
         and set(observed) == set(selected["jobs"]),
         "dependency.jobs.names", sorted(observed))
    for name, required_steps in selected["jobs"].items():
        job = observed[name]
        need(job.get("run_id") == selected["run_id"]
             and job.get("head_sha") == selected["candidate_head"],
             "dependency.job.identity", job.get("id"))
        need(job.get("status") == "completed" and job.get("conclusion") == "success",
             "dependency.job.conclusion", job.get("conclusion"))
        steps = job.get("steps") or []
        need(isinstance(steps, list) and all(isinstance(step, dict) for step in steps),
             "dependency.job.steps", steps)
        names = {step.get("name") for step in steps}
        need(all(required in names for required in required_steps),
             "dependency.job.acceptance", {"job": name, "steps": sorted(names)})
        need(all(step.get("status") == "completed" and step.get("conclusion") == "success"
                 for step in steps),
             "dependency.job.steps", steps)
    return {"producer": producer, "issue": selected["issue"],
            "revision": selected["revision"], "consumer": claim["repository"],
            "consumer_issue": claim["issue"]}
