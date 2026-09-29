"""Validate supervisor-bound cross-repository dependency results.

The external landing claim selects exact producer results. This module owns
their shape, provider readback projection and satisfaction semantics; it owns
no edge registry, effects, scheduler, retry loop or lifecycle state.
"""
import re

from repository_binding import valid_name


EDGE_FIELDS = {
    "repository", "issue", "pr", "base_ref", "base_head",
    "candidate_head", "tree", "revision", "run_id", "run_attempt",
    "workflow_path", "jobs",
}


def _key(index, kind):
    return f"dependency_{index}_{kind}"


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def dependencies(claim, require):
    """Validate and return exact dependencies selected by the supervisor."""
    values = claim.get("dependencies", []) if isinstance(claim, dict) else []
    require(isinstance(values, list), "claim.dependencies", values)
    identities = []
    for index, selected in enumerate(values):
        field = f"claim.dependencies[{index}]"
        require(isinstance(selected, dict) and set(selected) == EDGE_FIELDS,
                field + ".fields", sorted(selected) if isinstance(selected, dict) else selected)
        require(valid_name(selected["repository"]),
                field + ".repository", selected["repository"])
        for name in ("issue", "pr", "run_id", "run_attempt"):
            require(type(selected[name]) is int and selected[name] > 0,
                    field + "." + name, selected[name])
        for name in ("base_head", "candidate_head", "tree", "revision"):
            require(isinstance(selected[name], str)
                    and re.fullmatch("[0-9a-f]{40}", selected[name]),
                    field + "." + name, selected[name])
        require(isinstance(selected["base_ref"], str)
                and re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9._/-]{0,98}[A-Za-z0-9])?",
                                 selected["base_ref"])
                and ".." not in selected["base_ref"]
                and not selected["base_ref"].endswith(".lock"),
                field + ".base_ref", selected["base_ref"])
        require(isinstance(selected["workflow_path"], str)
                and re.fullmatch(r"\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml",
                                 selected["workflow_path"]),
                field + ".workflow_path", selected["workflow_path"])
        jobs = selected["jobs"]
        require(isinstance(jobs, dict) and bool(jobs), field + ".jobs", jobs)
        for name, steps in jobs.items():
            require(_nonempty(name) and isinstance(steps, list) and bool(steps)
                    and all(_nonempty(step) for step in steps)
                    and len(steps) == len(set(steps)),
                    field + ".jobs." + str(name), steps)
        identity = (selected["repository"], selected["issue"], selected["revision"])
        require(identity not in identities, "claim.dependencies.identity", list(identity))
        identities.append(identity)
    return values


def requests(claim, require):
    """Project exact read-only provider requests without choosing an edge."""
    result = {}
    for index, selected in enumerate(dependencies(claim, require)):
        base = f"https://api.github.com/repos/{selected['repository']}/"
        paths = {
            "issue": f"issues/{selected['issue']}",
            "pr": f"pulls/{selected['pr']}",
            "commit": f"git/commits/{selected['revision']}",
            "branch": f"branches/{selected['base_ref']}",
            "ancestry": f"compare/{selected['revision']}...{selected['base_ref']}",
            "run": f"actions/runs/{selected['run_id']}",
            "jobs": f"actions/runs/{selected['run_id']}/jobs",
        }
        result.update({_key(index, kind): {"method": "GET", "url": base + path}
                       for kind, path in paths.items()})
    return result


def _validate_one(index, selected, snapshot, require, next_action):
    def need(condition, field, value):
        require(condition, f"dependency[{index}].{field}", value, next_action)

    producer = selected["repository"]
    issue = snapshot.get(_key(index, "issue"))
    need(isinstance(issue, dict), "issue", issue)
    need(issue.get("url") == f"https://api.github.com/repos/{producer}/issues/{selected['issue']}",
         "issue.url", issue.get("url"))
    need(issue.get("html_url") == f"https://github.com/{producer}/issues/{selected['issue']}",
         "issue.html_url", issue.get("html_url"))
    need(issue.get("number") == selected["issue"], "issue.number", issue.get("number"))
    need(issue.get("state") == "closed" and issue.get("state_reason") == "completed"
         and bool(issue.get("closed_at")), "issue.closure",
         {"state": issue.get("state"), "state_reason": issue.get("state_reason"),
          "closed_at": issue.get("closed_at")})

    pr = snapshot.get(_key(index, "pr"))
    need(isinstance(pr, dict), "pr", pr)
    need(pr.get("number") == selected["pr"], "pr.number", pr.get("number"))
    need(pr.get("html_url") == f"https://github.com/{producer}/pull/{selected['pr']}",
         "pr.html_url", pr.get("html_url"))
    head_repo = (pr.get("head") or {}).get("repo") or {}
    base_repo = (pr.get("base") or {}).get("repo") or {}
    need(head_repo.get("full_name") == producer and base_repo.get("full_name") == producer,
         "pr.repository",
         {"head": head_repo.get("full_name"), "base": base_repo.get("full_name")})
    need((pr.get("head") or {}).get("sha") == selected["candidate_head"],
         "pr.head", (pr.get("head") or {}).get("sha"))
    need((pr.get("base") or {}).get("sha") == selected["base_head"]
         and (pr.get("base") or {}).get("ref") == selected["base_ref"],
         "pr.base", pr.get("base"))
    need(pr.get("state") == "closed" and pr.get("merged") is True and bool(pr.get("merged_at")),
         "pr.merge", {"state": pr.get("state"), "merged": pr.get("merged"),
                      "merged_at": pr.get("merged_at")})
    need(pr.get("merge_commit_sha") == selected["revision"],
         "pr.revision", pr.get("merge_commit_sha"))

    commit = snapshot.get(_key(index, "commit"))
    need(isinstance(commit, dict), "commit", commit)
    need(commit.get("sha") == selected["revision"], "commit.sha", commit.get("sha"))
    need((commit.get("tree") or {}).get("sha") == selected["tree"],
         "commit.tree", (commit.get("tree") or {}).get("sha"))
    parents = commit.get("parents")
    need(isinstance(parents, list) and len(parents) == 2
         and all(isinstance(parent, dict) for parent in parents)
         and [parent.get("sha") for parent in parents]
         == [selected["base_head"], selected["candidate_head"]],
         "commit.parents", parents)

    branch = snapshot.get(_key(index, "branch"))
    need(isinstance(branch, dict), "branch", branch)
    need(branch.get("name") == selected["base_ref"],
         "branch.name", branch.get("name"))
    current = (branch.get("commit") or {}).get("sha")
    need(isinstance(current, str) and re.fullmatch("[0-9a-f]{40}", current),
         "branch.head", current)

    ancestry = snapshot.get(_key(index, "ancestry"))
    need(isinstance(ancestry, dict), "ancestry", ancestry)
    need((ancestry.get("base_commit") or {}).get("sha") == selected["revision"],
         "ancestry.base", (ancestry.get("base_commit") or {}).get("sha"))
    need((ancestry.get("merge_base_commit") or {}).get("sha") == selected["revision"],
         "ancestry.merge_base", (ancestry.get("merge_base_commit") or {}).get("sha"))
    status = ancestry.get("status")
    need(status in {"identical", "ahead"}, "ancestry.status", status)
    need((ancestry.get("head_commit") or {}).get("sha") == current,
         "ancestry.head", (ancestry.get("head_commit") or {}).get("sha"))
    commits, total = ancestry.get("commits"), ancestry.get("total_commits")
    if status == "identical":
        need(current == selected["revision"] and commits == [] and total == 0,
             "ancestry.identical", {"head": current, "commits": commits,
                                    "total_commits": total})
    else:
        need(isinstance(commits, list) and bool(commits)
             and all(isinstance(item, dict) for item in commits)
             and type(total) is int and total == len(commits)
             and commits[-1].get("sha") == current,
             "ancestry.commits", commits)

    run = snapshot.get(_key(index, "run"))
    need(isinstance(run, dict), "run", run)
    need(run.get("id") == selected["run_id"]
         and run.get("run_attempt") == selected["run_attempt"],
         "run.identity", {"id": run.get("id"), "attempt": run.get("run_attempt")})
    need((run.get("repository") or {}).get("full_name") == producer
         and (run.get("head_repository") or {}).get("full_name") == producer,
         "run.repository",
         {"repository": (run.get("repository") or {}).get("full_name"),
          "head_repository": (run.get("head_repository") or {}).get("full_name")})
    need(run.get("head_sha") == selected["candidate_head"],
         "run.head", run.get("head_sha"))
    need(run.get("event") == "pull_request"
         and run.get("path") == selected["workflow_path"],
         "run.workflow", {"event": run.get("event"), "path": run.get("path")})
    need(run.get("status") == "completed" and run.get("conclusion") == "success",
         "run.conclusion", run.get("conclusion"))

    jobs = snapshot.get(_key(index, "jobs"))
    need(isinstance(jobs, dict), "jobs", jobs)
    raw_jobs = jobs.get("jobs", [])
    observed = {job.get("name"): job for job in raw_jobs if isinstance(job, dict)}
    need(isinstance(raw_jobs, list)
         and jobs.get("total_count") == len(raw_jobs) == len(observed) == len(selected["jobs"])
         and set(observed) == set(selected["jobs"]),
         "jobs.names", sorted(observed))
    for name, required_steps in selected["jobs"].items():
        job = observed[name]
        need(job.get("run_id") == selected["run_id"]
             and job.get("head_sha") == selected["candidate_head"],
             "job.identity", job.get("id"))
        need(job.get("status") == "completed" and job.get("conclusion") == "success",
             "job.conclusion", job.get("conclusion"))
        steps = job.get("steps") or []
        need(isinstance(steps, list) and all(isinstance(step, dict) for step in steps),
             "job.steps", steps)
        names = {step.get("name") for step in steps}
        need(all(required in names for required in required_steps),
             "job.acceptance", {"job": name, "steps": sorted(names)})
        need(all(step.get("status") == "completed" and step.get("conclusion") == "success"
                 for step in steps), "job.steps", steps)
    return {"producer": producer, "issue": selected["issue"],
            "revision": selected["revision"]}


def validate(claim, snapshot, require, next_action):
    """Validate every supervisor-selected result before consumer acceptance."""
    return [_validate_one(index, selected, snapshot, require, next_action)
            for index, selected in enumerate(dependencies(claim, require))]
