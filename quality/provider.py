"""One bounded read of existing exact-head runtime costs; never waits or retries."""
from datetime import datetime, timezone
import json
import os
import urllib.request

API = 'https://api.github.com/repos/ed3c/soodles'


def seconds(start, end):
    if not start or not end:
        return None
    return max(0, (datetime.fromisoformat(end.replace('Z', '+00:00')) -
                   datetime.fromisoformat(start.replace('Z', '+00:00'))).total_seconds())


def summarize_job(job):
    return {'id': job['id'], 'name': job['name'], 'status': job['status'],
            'conclusion': job.get('conclusion'),
            'seconds': seconds(job.get('started_at'), job.get('completed_at')),
            'steps': [{'name': step['name'], 'conclusion': step.get('conclusion'),
                       'seconds': seconds(step.get('started_at'), step.get('completed_at'))}
                      for step in job.get('steps', [])]}


def collect(head):
    result = {'status': 'unavailable', 'head': head, 'runs': [],
              'observed_at': datetime.now(timezone.utc).isoformat(),
              'limits': 'One read, at most 20 runs and 100 jobs per run. Latest observed attempt only; not all retry history or Agent active time. Pending is not zero. Job seconds overlap and are not billed runner-minutes.'}
    token = os.environ.get('GH_TOKEN')
    if not token:
        result['reason'] = 'No provider read capability in this environment'
        return result

    def get(path):
        request = urllib.request.Request(API + path, headers={
            'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'soodles-quality-report'})
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)

    try:
        raw = get('/actions/runs?head_sha=' + head + '&event=pull_request&per_page=20')
        result['raw_runs'] = raw
        partial = raw['total_count'] > len(raw['workflow_runs'])
        for run in raw['workflow_runs']:
            if run['head_sha'] != head or run['path'] != '.github/workflows/runtime.yml':
                continue
            jobs = get(f"/actions/runs/{run['id']}/attempts/{run['run_attempt']}/jobs?per_page=100")
            partial |= jobs['total_count'] > len(jobs['jobs'])
            if any(job['head_sha'] != head for job in jobs['jobs']):
                raise ValueError('provider job head differs from measured head')
            result['runs'].append({'id': run['id'], 'attempt': run['run_attempt'],
                                   'url': run['html_url'], 'status': run['status'],
                                   'conclusion': run['conclusion'], 'raw_jobs': jobs,
                                   'jobs': [summarize_job(job) for job in jobs['jobs']]})
        result['status'] = 'partial' if partial else ('observed' if result['runs'] else 'pending')
        if any(run['status'] != 'completed' for run in result['runs']):
            result['status'] = 'pending'
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result['status'] = 'unavailable'
        result['reason'] = f'Provider read failed: {type(exc).__name__}; no unchanged retry'
    return result
