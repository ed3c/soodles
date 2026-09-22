"""Fixed semantic evaluator for baseline and matched P-only treatment reports."""
import hashlib,json,subprocess,sys
from pathlib import Path

report_path=Path(sys.argv[1]).resolve()
root=Path(sys.argv[2]).resolve()
expected_head=sys.argv[3]
output=Path(sys.argv[4]).resolve()
assert not output.exists()
report=json.loads(report_path.read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
checks={}
checks['head']=report.get('source_head')==expected_head==subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
checks['source_clean']=subprocess.check_output(['git','status','--porcelain'],cwd=root)==b''
observed={item.get('path'):item for item in report.get('actual_files_read',[]) if isinstance(item,dict)}
accurate=True
for name,item in observed.items():
    path=Path(name)
    if not path.is_absolute(): path=root/path
    if not path.is_file() or sha(path)!=item.get('sha256') or path.stat().st_size!=item.get('bytes'):
        accurate=False
checks['read_bindings_accurate']=bool(observed) and accurate
checks['map_read']=any(Path(name).name=='README.md' and 'features' in Path(name).parts for name in observed)
checks['recipe_read']=any(Path(name).name=='cross-repository-delivery.md' for name in observed)
checks['task_input_read']=any(Path(name).name=='task-input.json' for name in observed)
checks['no_judge_read']=not any(Path(name).name in {'protocol.md','manifest.json','freeze.py','observe.py','evaluate_report.py','decision.json'} for name in observed)
classification=str(report.get('classification','')).lower()
checks['classification_mapped']=classification=='mapped'
feature=report.get('selected_feature')
if isinstance(feature,dict): feature=feature.get('mapped_feature')
checks['selected_existing_feature']=str(feature).lower() in {'cross-repository delivery','cross-repository-delivery','cross_repository_delivery'}
checks['recipe_path']=str(report.get('recipe_path','')).endswith('.agents/skills/verify-soodles/features/cross-repository-delivery.md')
owner=json.dumps(report.get('owner_boundary'),ensure_ascii=False).lower()
checks['existing_owner']='landing' in owner and 'next.requests' in owner and 'dependency_' in owner
checks['no_new_feature']=report.get('new_feature_required') is False
checks['no_new_cli']=report.get('new_cli_required') is False
checks['no_new_registry']=report.get('new_registry_required') is False
checks['not_delivery_complete']=report.get('delivery_complete') is False
checks['no_external_operations']=report.get('external_operations_performed') in ([],False,None)
auxiliary=[{'argv':item.get('argv'),'exit_status':item.get('exit_status'),'stderr':item.get('important_stderr') or item.get('stderr')}
 for item in report.get('actual_commands',[]) if item.get('exit_status') not in (0,None)]
barriers=[name for name,value in checks.items() if not value]
value={'schema':1,'report':str(report_path),'source_root':str(root),'expected_head':expected_head,
 'classification':'NO_OBSERVED_BARRIER' if not barriers else 'OBSERVED_BARRIER',
 'checks':checks,'barriers':barriers,'auxiliary_read_only_command_failures':auxiliary,
 'external_evaluator_sha256':sha(Path(__file__)),'authorizes_landing':False,
 'unknowns':['complete platform transcript','hidden reads','actual model/config/context/compaction']}
output.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'classification':value['classification'],'barriers':barriers,'checks':len(checks)}))
