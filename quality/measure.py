"""Report-only pinned source measurement. Does not execute Soodles or authorize landing."""
import ast
from collections import Counter
from dataclasses import asdict
import hashlib
from importlib import metadata
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import argparse
import re

PIN = '0.1.3'
SCOPES = ('production', 'tests', 'oracles', 'tooling', 'unclassified')


def initialize():
    global pipeline, astgrep, parse_source, sloc_line_numbers
    global CYC_COMPLEXITY_NODE_TYPES, iter_nodes, compute_report, rule_texts, yaml, SG
    import scb_check.pipeline as pipeline
    from scb_check.analysis import astgrep
    from scb_check.analysis.parse import parse_source
    from scb_check.analysis.loc import sloc_line_numbers
    from scb_check.analysis.symbols import CYC_COMPLEXITY_NODE_TYPES
    from scb_check.analysis.syntax import iter_nodes
    from scb_check.reporting.score import compute_report
    from scb_check.resources import rule_texts
    import yaml

    assert metadata.version('scb-check')==PIN
    assert not os.environ.get('SCB_CHECK_EXTRA_SLOP_RULES'), 'unexpected extra analyzer rules'
    # Some hosts have an unrelated Unix sg command. Use the installed analyzer binary by exact version.
    SG=None
    for name in ('ast-grep','sg'):
        candidate=Path(sys.executable).parent/name
        if candidate.is_file():
            r=subprocess.run([str(candidate),'--version'],capture_output=True,text=True)
            if r.returncode==0 and r.stdout.strip()=='ast-grep 0.42.1':
                SG=str(candidate); break
    assert SG, 'pinned ast-grep 0.42.1 unavailable'

def strict_sg(files,rules):
    if not files: return ()
    r=subprocess.run([SG,'scan','--json=stream','-r',str(rules),*[str(p) for p in files]],capture_output=True,text=True,timeout=120)
    if r.returncode:
        raise RuntimeError('AST-Grep failed; no score is valid: '+r.stderr)
    raw=[json.loads(line) for line in r.stdout.splitlines() if line.strip()]
    hits=astgrep._parse_hits(r.stdout)
    assert len(hits)==len(raw), 'analyzer output records dropped'
    return hits


def git(repo,*args):
    return subprocess.check_output(['git',*args],cwd=repo)

def flag_lines(entries):
    return {(str(e.file),line) for e in entries for line in e.lines}

def analyze(paths):
    result=pipeline.analyze_files(tuple(paths),include_all=True)
    assert {p for p,_ in result.flags.total_loc_by_file}==set(paths), 'parse/discovery coverage mismatch'
    return result.flags

def article_counts(flags):
    a=flag_lines(flags.ast_sloc_lines_by_file); c=flag_lines(flags.clone_sloc_lines_by_file)
    w=flag_lines(flags.trivial_wrapper_sloc_lines_by_file)
    return a,c,w,a|c

def controls(root):
    p=root/'control.py'
    p.write_text('def first(x):\n    if x == True:\n        return 1\n    return 0\n\ndef second(x):\n    if x == True:\n        return 1\n    return 0\n')
    flags=analyze([p]); a,c,w,union=article_counts(flags)
    assert any(h.rule_id=='bool-comparison' for h in flags.ast_grep_hits)
    assert c and a&c, 'clone/AST overlap discriminator absent'
    assert len(union)<len(a)+len(c)
    assert compute_report(flags).verbosity_flagged_loc==len(a|c|w)
    p.write_text('def boolean_condition(x):\n    if x:\n        return 1\n    return 0\n')
    assert not any(h.rule_id=='bool-comparison' for h in analyze([p]).ast_grep_hits)
    p.write_text('\n\n'.join('def '+name+'(x):\n'+''.join('    if x == '+str(i)+':\n        x += 1\n' for i in range(n))+'    return x\n' for name,n in [('at_ten',9),('over_ten',10)]))
    flags=analyze([p]); symbols={s.name:s for s in flags.all_functions}
    assert symbols['at_ten'].cyc_complexity==10 and symbols['over_ten'].cyc_complexity==11
    report=compute_report(flags)
    total=sum(s.cyc_complexity*math.sqrt(s.sloc) for s in symbols.values())
    high=11*math.sqrt(symbols['over_ten'].sloc)
    assert math.isclose(report.total_mass,total) and math.isclose(report.erosion,high/total)
    p.write_text('def outer():\n    with open(\"fixture\") as stream:\n        def nested():\n            return stream.read()\n        return nested()\n')
    complete=complete_symbols([p],root)
    assert {s['name'] for s in complete}=={'outer','outer.nested'}
    return {'complete_nested_callables':True,'ast_positive':True,'ast_legal_noncase':True,'clone_overlap_union':True,'cc_10_11_threshold':True,'independent_mass_recalculation':True}

def scope(path):
    if path in ('landing.py','soodles.py'): return 'production'
    if path.startswith('tests/'): return 'tests'
    if path in ('cleanup_oracle.py','cleanup_lock_oracle.py','delivery_oracle.py',
                'handoff_oracle.py','resume_oracle.py'): return 'oracles'
    if path.startswith('quality/'): return 'tooling'
    return 'unclassified'

def qualified_names(source):
    result={}
    class Visitor(ast.NodeVisitor):
        names=[]
        def visit_ClassDef(self,node):
            self.names.append(node.name); self.generic_visit(node); self.names.pop()
        def visit_FunctionDef(self,node):
            self.names.append(node.name); result[node.lineno]='.'.join(self.names)
            self.generic_visit(node); self.names.pop()
        visit_AsyncFunctionDef=visit_FunctionDef
    Visitor().visit(ast.parse(source))
    return result

def complete_symbols(paths,destination):
    symbols=[]
    for path in paths:
        source=path.read_text(); tree=parse_source(source); sloc_lines=sloc_line_numbers(source,tree)
        names=qualified_names(source)
        for node in iter_nodes(tree.root_node):
            if node.type!='function_definition': continue
            start,end=node.start_point.row+1,node.end_point.row+1
            cc=1+sum(n.type in CYC_COMPLEXITY_NODE_TYPES for n in iter_nodes(node))
            sloc=sum(start<=line<=end for line in sloc_lines)
            symbols.append({'file':str(path.relative_to(destination)),'name':names[start],'start':start,'end':end,
                            'cc':cc,'sloc':sloc,'mass':cc*math.sqrt(sloc),
                            'body_sha256':hashlib.sha256(source.encode()[node.start_byte:node.end_byte]).hexdigest()})
        assert {(s['start']) for s in symbols if s['file']==str(path.relative_to(destination))}==set(names), 'callable coverage differs from Python AST'
    return symbols

def measure(repo,sha,destination,out):
    tracked=git(repo,'ls-tree','-rz','--name-only',sha).decode().rstrip('\0').split('\0')
    py=[p for p in tracked if p.endswith('.py')]
    files={};manifest=[]
    for name in py:
        data=git(repo,'show',sha+':'+name)
        p=destination/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        files[name]=p;manifest.append({'path':name,'scope':scope(name),'sha256':hashlib.sha256(data).hexdigest(),'physical_lines':len(data.splitlines())})
    groups={g:[p for n,p in files.items() if scope(n)==g] for g in SCOPES}
    groups['all_python']=list(files.values())
    data={}
    for group,paths in groups.items():
        started=time.monotonic(); flags=analyze(paths); elapsed=time.monotonic()-started
        report=asdict(compute_report(flags)); a,c,w,union=article_counts(flags)
        assert report['verbosity_flagged_loc']==len(a|c|w)
        symbols=complete_symbols(paths,destination)
        native={(str(s.file.relative_to(destination)),s.start_line):s for s in flags.all_functions}
        for sym in symbols:
            original=native.get((sym['file'],sym['start']))
            if original: assert (original.cyc_complexity,original.sloc)==(sym['cc'],sym['sloc'])
        omitted=[sym for sym in symbols if (sym['file'],sym['start']) not in native]
        total_mass=sum(sym['mass'] for sym in symbols)
        high_mass=sum(sym['mass'] for sym in symbols if sym['cc']>10)
        hits=[{'file':str(h.file.relative_to(destination)),'start':h.line,'end':h.end_line,'rule':h.rule_id,
               'message':h.message,'text':h.matched_text} for h in flags.ast_grep_hits]
        clones=[{'file':str(b.file.relative_to(destination)),'start':b.start_line,'end':b.end_line,'group':b.group_hash,
                 'others':[{'file':str(p.relative_to(destination)),'start':line} for p,line in b.other_instances]} for b in flags.clones]
        perfile=[]
        for p,sloc in flags.total_loc_by_file:
            own=[s for s in symbols if s['file']==str(p.relative_to(destination))]
            perfile.append({'file':str(p.relative_to(destination)),'sloc':sloc,'physical_lines':len(p.read_text().splitlines()),
                            'ast_lines':sum(f==str(p) for f,l in a),'clone_lines':sum(f==str(p) for f,l in c),
                            'article_union_lines':sum(f==str(p) for f,l in union),
                            'mass':sum(s['mass'] for s in own),'high_cc_mass':sum(s['mass'] for s in own if s['cc']>10)})
        line_sets={label:{str(p.relative_to(destination)):sorted(line for f,line in values if f==str(p)) for p in paths}
                   for label,values in [('ast',a),('clone',c),('wrapper',w),('article_union',union)]}
        data[group]={'scb_report':report,'status':'measured' if report['total_loc'] else 'empty',
                     'article_verbosity':len(union)/report['total_loc'] if report['total_loc'] else 0,
                     'article_union_lines':len(union),'ast_clone_overlap':len(a&c),'scan_seconds':elapsed,
                     'all_callable_erosion':high_mass/total_mass if total_mass else 0,
                     'all_callable_total_mass':total_mass,'all_callable_high_mass':high_mass,'native_omitted_callables':omitted,
                     'files':perfile,'symbols':symbols,'ast_hits':hits,'clones':clones,'line_sets':line_sets}
    result={'sha':sha,'tree':git(repo,'rev-parse',sha+'^{tree}').decode().strip(),'manifest':manifest,
            'excluded_non_python':sorted(set(tracked)-set(py)),'groups':data}
    (out/(sha+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    return result

def preflight(repo, base, head, output):
    for field, value in (('base', base), ('head', head)):
        if not re.fullmatch('[0-9a-f]{40}', value):
            raise ValueError(f"invalid {field}={value!r}; use python quality/measure.py --help")
        try:
            kind = git(repo, 'cat-file', '-t', value).decode().strip()
        except subprocess.CalledProcessError as exc:
            raise ValueError(f"unavailable {field}={value!r}; fetch the exact commit, then use python quality/measure.py --help") from exc
        if kind != 'commit':
            raise ValueError(f"invalid {field}={value!r}: expected commit; use python quality/measure.py --help")
    output = Path(output).resolve()
    if output == repo or repo in output.parents:
        raise ValueError(f"invalid output={str(output)!r}: must be outside the subject; use python quality/measure.py --help")
    if output.exists():
        raise ValueError(f"invalid output={str(output)!r}: already exists; use a fresh output directory; python quality/measure.py --help")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, help='Exact 40-character PR base commit SHA')
    parser.add_argument('--head', required=True, help='Exact 40-character PR head commit SHA')
    parser.add_argument('--output', required=True, help='Fresh directory outside the repository')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    BASE, HEAD = args.base, args.head
    out = preflight(repo, BASE, HEAD, args.output)
    initialize()
    pipeline.run_sg = strict_sg
    out.mkdir(parents=True)
    recipe_files = ('quality/measure.py', 'quality/requirements.txt')
    recipe = {name:hashlib.sha256((repo/name).read_bytes()).hexdigest() for name in recipe_files}
    recipe_sha = hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest()
    rules=list(rule_texts()); rule_hashes={name:hashlib.sha256(text.encode()).hexdigest() for name,text in rules}
    rule_ids=[d['id'] for _,text in rules for d in yaml.safe_load_all(text) if d]
    with tempfile.TemporaryDirectory(prefix='soodles-quality-snapshots-') as tmp:
        temp=Path(tmp);test=temp/'controls';test.mkdir();proof=controls(test)
        base=measure(repo,BASE,temp/'base',out);head=measure(repo,HEAD,temp/'head',out)
    table=[];delta=[]
    for group in base['groups']:
        b=base['groups'][group];h=head['groups'][group]
        table.append({'scope':group,'base_status':b['status'],'head_status':h['status'],'base_sloc':b['scb_report']['total_loc'],'head_sloc':h['scb_report']['total_loc'],
                      'base_v':b['article_verbosity'],'head_v':h['article_verbosity'],
                      'base_native_v':b['scb_report']['verbosity'],'head_native_v':h['scb_report']['verbosity'],
                      'base_e':b['all_callable_erosion'],'head_e':h['all_callable_erosion'],
                      'base_native_e':b['scb_report']['erosion'],'head_native_e':h['scb_report']['erosion'],
                      'base_mass':b['all_callable_total_mass'],'head_mass':h['all_callable_total_mass'],
                      'base_high_mass':b['all_callable_high_mass'],'head_high_mass':h['all_callable_high_mass'],
                      'base_union':b['article_union_lines'],'head_union':h['article_union_lines']})
        if group=='all_python': continue
        bs={(s['file'],s['name']):s for s in b['symbols']};hs={(s['file'],s['name']):s for s in h['symbols']}
        assert len(bs)==len(b['symbols']) and len(hs)==len(h['symbols']), 'ambiguous function matching'
        for key in sorted(bs.keys()|hs.keys()):
            old,new=bs.get(key),hs.get(key)
            if old is None or new is None or old['body_sha256']!=new['body_sha256']:
                delta.append({'scope':group,'file':key[0],'name':key[1],'before':old,'after':new})
    summary={'repository':'ed3c/soodles','base':BASE,'head':HEAD,'recipe_sha256':recipe_sha,'recipe_files':recipe,
             'measurement_head':git(repo,'rev-parse','HEAD').decode().strip(),
             'recipe_changed':bool(git(repo,'diff','--name-only',BASE,HEAD,'--',*recipe_files).strip()),'scb_check':PIN,'ast_grep':'0.42.1',
             'benchmark_source':'06b5c0687d4c05ee502e9696a4d0c22fc1eec5e0','rules':len(rule_ids),'rule_sha256':rule_hashes,
             'controls':proof,'table':table,'function_deltas':delta,
             'git_numstat':git(repo,'diff','--numstat',BASE,HEAD).decode(),
             'packages':sorted((d.metadata['Name'],d.version) for d in metadata.distributions()),
             'scope_contract':'All tracked .py at exact snapshots; production/tests/oracles/tooling/unclassified disjoint; empty cohorts have status=empty (displayed zeros are not observations). all_python is separately scanned and includes cross-scope clones.',
             'metric_contract':'V_article=|AST SLOC union clone SLOC|/SLOC. V_native also includes trivial wrappers. E=sum(CC*sqrt(SLOC) where CC>10)/sum(CC*sqrt(SLOC)). CC/SLOC follow pinned scb-check, not Radon. E counts every function definition, including those nested under with/control blocks, cross-checked against Python AST; native tool E and omitted callables are retained separately.',
             'limitations':['197-rule tool release is not the paper historical 137-rule run; no human/agent ranking.',
                            'Nested function spans include inner bodies, matching the pinned CC/SLOC convention; masses are not disjoint source ownership.',
                            'scb-check 0.1.3 misses some nested definitions under with/control blocks. Each snapshot records exactly which native callables were omitted. The E column uses complete callable traversal with identical per-function CC/SLOC rules; native E is retained.',
                            'All metrics are structural signals, not correctness, authority, deletion permission or maintenance-time measurements.',
                            'Static analysis does not execute the exported subject snapshots. The PR report implementation is not a fixed external judge. No provider writes or acceptance rerun.'],
             'authorizes_landing':False}
    from provider import collect
    summary['provider_cost'] = collect(HEAD)
    (out/'provider-cost.json').write_text(json.dumps(summary['provider_cost'],indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Soodles code-quality observation','',f'Base `{BASE}` → head `{HEAD}`. Analyzer `scb-check=={PIN}`, AST-Grep `0.42.1`, {len(rule_ids)} bundled rules.','',
           'Report only; not an acceptance gate or formal correctness proof.','',
           '| Scope | SLOC base → head | Article V base → head | Native V base → head | E all callables base → head |',
           '|---|---:|---:|---:|---:|']
    for r in table: lines.append(f"| {r['scope']} ({r['base_status']} → {r['head_status']}) | {r['base_sloc']} → {r['head_sloc']} | {r['base_v']:.4f} → {r['head_v']:.4f} | {r['base_native_v']:.4f} → {r['head_native_v']:.4f} | {r['base_e']:.4f} → {r['head_e']:.4f} |")
    lines+=['', 'Native scb-check E (before completing omitted callables): '+ '; '.join(f"{r['scope']} {r['base_native_e']:.4f} → {r['head_native_e']:.4f}" for r in table)+'.', '', 'The complete-callable E is an explicitly documented reporting adaptation, not an unmodified benchmark score.']
    lines+=['','## Absolute complexity mass','', '| Scope | Total mass base → head | CC>10 mass base → head | Article flagged SLOC base → head |','|---|---:|---:|---:|']
    for r in table:lines.append(f"| {r['scope']} | {r['base_mass']:.2f} → {r['head_mass']:.2f} | {r['base_high_mass']:.2f} → {r['head_high_mass']:.2f} | {r['base_union']} → {r['head_union']} |")
    lines+=['','## Head function locations','', '| Scope | Function | CC | SLOC | Mass |','|---|---|---:|---:|---:|']
    for group in SCOPES:
        for s in sorted(head['groups'][group]['symbols'],key=lambda s:-s['mass'])[:8]:
            url=f"https://github.com/ed3c/soodles/blob/{HEAD}/{s['file']}#L{s['start']}"
            lines.append(f"| {group} | [{s['file']}:{s['name']}]({url}) | {s['cc']} | {s['sloc']} | {s['mass']:.2f} |")
    lines+=['', '## Observation provenance and cost', '', f'Recipe `{recipe_sha}`; recipe changed: {summary["recipe_changed"]}. Compare histories only under the same recipe.', '', f'Provider cost snapshot: **{summary["provider_cost"]["status"]}**. See provider-cost.json for exact-head run/attempt/job/step readbacks. Pending or unavailable is not zero cost.', '', 'Per-scope scan seconds are in the snapshot JSON. Git numstat and changed callable locations identify touched source; shared job time cannot be attributed to an individual function or Agent active work.']
    lines+=['','## Interpretation limits','',summary['metric_contract'],'',summary['scope_contract'],'',*['- '+x for x in summary['limitations']], '',
            'The JSON artifacts retain every rule hit, clone counterpart, function, exact line set, file digest, and base/head delta. Original acceptance and fixed external verifier remain unchanged.',
            '', 'Sources: https://earendil.com/posts/measuring-code-sloppiness/ ; https://arxiv.org/html/2603.24755v1 ; https://pypi.org/project/scb-check/0.1.3/']
    markdown='\n'.join(lines)+'\n';(out/'report.md').write_text(markdown)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(markdown)
    print('QUALITY_REPORT_SHA256='+hashlib.sha256(markdown.encode()).hexdigest())
    print('QUALITY_SUMMARY='+json.dumps({'table':table,'controls':proof,'rules':len(rule_ids)}))
    print('QUALITY_FUNCTIONS='+json.dumps(head['groups']['production']['symbols']))
    print('QUALITY_HITS='+json.dumps(Counter(h['rule'] for h in head['groups']['all_python']['ast_hits'])))

if __name__=='__main__':
    try:
        main()
    except (ValueError, RuntimeError, AssertionError, OSError, ImportError, subprocess.SubprocessError) as exc:
        print(f'QUALITY_MEASUREMENT_FAILED: {exc}; action: python quality/measure.py --help', file=sys.stderr)
        sys.exit(1)
