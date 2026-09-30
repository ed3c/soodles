"""Seal this corrective comparison into its existing Issue's evidence subtree."""
import gzip,hashlib,json,shutil,tarfile
from pathlib import Path
B=Path(__file__).resolve().parents[1];C=B.parent
W=Path('/Users/neon/.codex/worktrees/authorization-shortest-path/soodles')
D=W/'docs/experiments/authorization-reentry/correction'
D.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,name):
 p=D/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
def save(name,v):(D/name).write_text(json.dumps(v,indent=2)+'\n')
files=['protocol.md','freeze.json','r03-integration-protocol.md','r03-freeze.json','downstream-freeze.json','winner.json','r01-decision.json','r02-decision.json','r03-decision.json','confirmation-decision.json']
for n in files:copy(B/n,n)
for folder in ['evaluator','tools','host','private']:
 for p in (B/folder).iterdir():
  if p.is_file() and p.suffix in ('.py','.json','.md','.sb'):copy(p,str(p.relative_to(B)))
rows=json.loads((B/'archives/index-initial.json').read_text())
rows += [json.loads(p.read_text()) for p in sorted((B/'archives').glob('*-index.json')) if p.name!='downstream-index.json']
assert len(rows)==30,len(rows)
for row in rows:
 copy(B/'archives'/row['archive'],'archives/'+row['archive']);row['archive']='archives/'+row['archive']
down=json.loads((B/'archives/downstream-index.json').read_text());copy(B/'archives'/down['archive'],'archives/'+down['archive']);down['archive']='archives/'+down['archive']
ns=['a1','a2','a3','b1','c1'];comparisons={}
for arm in ['r01','r02','r03','confirmation']:
 membership={'baseline':[('confirm-baseline' if arm=='confirmation' else 'baseline')+'-'+n for n in ns],'candidate':[('confirm-winner' if arm=='confirmation' else arm)+'-'+n for n in ns]}
 if arm=='r02':membership['comparator']=['r01-'+n for n in ns[:3]]
 comparisons[arm]={'membership':membership,'decision':arm+'-decision.json'}
pins={n:sha(B/n) for n in ['tools/archive_case.py','tools/replay_archive.py','evaluator/check.py','evaluator/capture_decoder.py','evaluator/analysis.py']}
save('evidence-index.json',{'schema':1,'tools':pins,'runs':rows,'comparisons':comparisons,'downstream':down,'authorizes_landing':False})
# Exact original sources remain immutable observations, not current executable judges.
with (D/'sources.tar.gz').open('xb') as out,gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0) as gz,tarfile.open(fileobj=gz,mode='w') as tar:
 for p in sorted((B/'snapshots').rglob('*')):
  if not p.is_file():continue
  info=tar.gettarinfo(str(p),arcname=str(p.relative_to(B/'snapshots')));info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
  with p.open('rb') as stream:tar.addfile(info,stream)
for name in ['activation-audit.md','activation-current-source.json','lifecycle-runtime-v1.json','lifecycle-current-custody.json','review-transition-manifest.json','review-transition-focused.log','review-transition-tests.log','lifecycle-activation-suite.log','independent-noodle-telemetry.json','branch-amendment-oracle.json','branch_amendment_oracle.py','base-recovery-oracle.json','delivery-oracle.json','owner-liveness.json','audit_owner_liveness.py','current-entry-refusal.json','publication-gap-reproduction.json']:
 copy(C/name,'verification/'+name)
copy(C/'noodle-restart-fixture/loop/soodles_completed_review_test.go','verification/soodles_completed_review_test.go')
for p in (C/'lifecycle-oracle-v2').glob('*.py'):copy(p,'verification/lifecycle-oracle/'+p.name)
# The result document intentionally does not manufacture future delivery receipts.
(D/'results.md').write_text('''# 同一 Issue #193 的 correction 實證

結論：外部 lifecycle owner 選定／準備／handoff 的局部正確性改善，獨立 confirmation 成立；提示詞短入口未達效率門檻，已撤回。完整交付仍由同 PR #194 的新 head 與既有 owner terminal receipt 證明，本文件不授權 merge。

| 比較 | A/B/C 結果 | 正常 A 操作數 | 判定 |
|---|---|---|---|
| Baseline | 0/5 通過 | 9、9、7，未完成不作效率分母 | 重現缺陷 |
| R01：CLI 修正、原 P | 5/5 | 10、9、9 | 保留正確性 |
| R02：CLI 相同、短 P 入口 | 5/5 | 9、9、9 | 中位數減少 0%，撤回 |
| R03：撤回短入口、必要契約文件整合 | 5/5 | 9、9、9 | 固定最終版本；不宣稱效率 |
| Confirmation baseline | 0/5 | 未完成，不作效率分母 | 缺陷仍在 |
| Confirmation winner | 5/5 | 9、8、10 | 正確性確認 |

R03 的事前 integration addendum 明確記錄文件整合與原 R02 優化門檻的差別，未改舊分數。跨 Session 補充由 fresh consumer 使用 R03-a1 實際保存的 handoff，產品對後續 head 變動回 git.head 拒絕，保留同一 authorization／next，無 lifecycle checkpoint。原始 archive 同時包含 producer consumer 與 downstream consumer，不能把重新生成的 fixture 當成 handoff。

產品證據分開讀：509 項 suite 通過；外部 Noodle process controls 驗證 review→failed→同 order promotion、mode hold 和 ack 無轉移反例；publisher fixtures 驗證同 PR 分支與新 head；新 lifecycle controls 驗證固定 bytes 與錯誤 source 拒絕。命令／輸出／退出碼／canonical state 由外部 observer 擷取。單元測試自述 PASS 不當作 independent telemetry。

資料流：真實失敗及 owner readback → eval-audit findings → protocol／固定 code oracle＋controls → baseline → 兩個單因果假設與一輪必要整合 → 固定 winner → 一次 confirmation → 跨 fresh Session handoff → 既有 Issue admission／Noodle／publication／exact-head acceptance／landing。主 protocol 是原始 pin；封存的絕對路徑是實際執行身分，離線重播只重定位觀察，不改寫身分。

重構判定：外部 observation 要求修正 canonical state 觀察和 process hold。只保留 correction_proposal 的共用生成，防止 producer／consumer 比較漂移；未發現需要再做大範圍輸入輸出等價重構的證據。每層都有保留或修正的理由；不強迫提示詞也必須改。

限制：小型固定案例不代表所有缺陷／所有 carrier／所有未來 Session 都不退化。不宣稱 >=20% 節省、零猜測、零打擾或完整 maintenance。各 run 保留 token、cache、reasoning 與 elapsed 原始量測；模型 alias 的實際後端版本未知，並行執行的 elapsed 不用作因果速度指標。Confirmation baseline-a2 另有 stdout provenance gate 失敗，保留原分數，未更换 run。

原來 authorization-reentry 三輪與 confirmation 完整保留；本 correction 是發現交付缺陷後、同一未 merge Issue 內另行固定的比較，不能合併成同一次獨立 confirmation。交付 provider readback／terminal receipt 由原 owner 保管，完成前不得宣稱整體閉環。
''')
print(json.dumps({'evidence_root':str(D),'runs':len(rows),'files':sum(p.is_file() for p in D.rglob('*')),'sources_sha256':sha(D/'sources.tar.gz')}))
