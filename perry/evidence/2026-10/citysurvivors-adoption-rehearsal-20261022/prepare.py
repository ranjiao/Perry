import collections, hashlib, json, os, re, shutil
from pathlib import Path

RUN=Path(__file__).parent
SRC=Path('/Users/bytedance/proj/wargame/CitySurvivors')
PERRY=Path('/Users/bytedance/proj/Perry')
CAP=RUN/'source-capture'
OUT=Path(json.loads((RUN/'paths.json').read_text())['delivery'])
OUT.mkdir(exist_ok=False)
SELECT={'CS-030','CS-031','CS-061','CS-065','CS-066','CS-068','CS-076','CS-078','CS-079','CS-080',
 'ART-043','ART-044','ART-076','ART-085','ART-086','ART-087','ART-088','ART-089',
 'DEV-038','DEV-039','DEV-066','DEV-077','DEV-078','DEV-079','DEV-080','DEV-081','DEV-083','DEV-084',
 'DEV-089','DEV-092','DEV-094','DEV-096'}
PARENTS={'ART-043':'CS-030','ART-044':'CS-030','ART-076':'CS-030','DEV-038':'CS-031','DEV-039':'CS-031',
 'DEV-066':'CS-031','DEV-077':'CS-065','DEV-078':'CS-065','DEV-079':'CS-065','DEV-080':'CS-065',
 'DEV-081':'CS-061','DEV-083':'CS-061','DEV-084':'CS-061','DEV-092':'CS-078','ART-089':'CS-079'}
ROWS=json.loads((RUN/'source-rows.json').read_text())
SCOPE={'todo.md':'project.todo','docs/art/todo.md':'art.todo','docs/tech/todo.md':'tech.todo'}
def title(row):
 return next((v for k,v in row['cells'].items() if '任务' in k or k in ('工作','所属包／工作','本批任务')),row['id'])
def status(row):return next((v for k,v in row['cells'].items() if k.startswith('状态')),'未单列状态')
def role(row):
 if row['id'].startswith('ART'):return '美术'
 if row['id'].startswith('DEV'):return '程序'
 return row['cells'].get('负责人','策划')

records=[];inventory=[]
for row in ROWS:
 r=dict(row);r.update(source_identity='CitySurvivors:'+SCOPE[row['scope']]+':'+row['id'],
  responsible_role=role(row),lifecycle_writer='策划' if row['id'].startswith('CS') else role(row),
  title=title(row),source_state=status(row),disposition='create' if row['id'] in SELECT else 'link-only',
  approval='仅隔离演练；真实映射/状态/权限与切换未获确认')
 r['reason']='代表性演练候选；保留来源，未授予业务完成或验收' if r['disposition']=='create' else '本轮不接管：原角色/原todo继续权威；不复活、不关闭、不删除，后续逐项决定'
 inventory.append(r)
 if r['disposition']!='create':continue
 r['proposed_state']='not_started' if r['id'] in {'CS-066','CS-068','CS-076','CS-080','DEV-083'} else 'review'
 # Uniform trial defaults explicitly carry no claim about real priority or accepted verification.
 r['native_fields']={'title':'[隔离演练] '+r['id']+' '+r['title'],
   'summary':r['source_identity']+'; 责任角色='+r['responsible_role']+'; 生命周期维护='+r['lifecycle_writer']+
       '; 仅隔离映射；源状态和未测保留于附件；无实际验收、无KR归属。',
   'priority':row['cells'].get('优先级','P2'),'owner':'PMO Agent' if r['id'].startswith('CS') else 'User + Agent',
   'track':'intake','verification':'V4',
   'next_action':'演练候选状态，不开展游戏生产。正式迁移前由原维护者确认当前状态、优先级、验收层级和具体接续。'}
 r['parent_source_id']=PARENTS.get(r['id']);records.append(r)
assert len(records)==32 and len(inventory)==257
plan={'format':'citysurvivors-adoption-rehearsal/1','scope':'simulation-only','live_activation_authorized':False,
 'source_root':str(SRC),'source_manifest_sha256':hashlib.sha256((RUN/'source-manifest.json').read_bytes()).hexdigest(),
 'template_sha256':hashlib.sha256((PERRY/'templates/process/perry.json').read_bytes()).hexdigest(),
 'records':records,'inventory_counts':dict(collections.Counter(r['disposition'] for r in inventory)),
 'relation_policy':'Only15 explicit package membership edges; no source dependency is automatically translated to a terminal-completion blocks edge. ART-088 is not a child of ART-085; later modeling/rigging are distinct deliveries. CS-080 can inspect delivered candidates before package closure.',
 'defaults':'Non-CS priority P2, User+Agent and V4 are trial placeholders pending actual owner agreement; not source facts or approval. All imported source statuses are proposals; no task is marked done. Unknown goals/KRs have no native relation or progress.'}
(OUT/'mapping-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
(OUT/'source-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
shutil.copytree(CAP,OUT/'source-capture')
shutil.copyfile(RUN/'source-manifest.json',OUT/'source-manifest.json')
shutil.copyfile(RUN/'source-status-before.bin',OUT/'source-status-before.bin')
for name in ['capture.py','prepare.py']:
 shutil.copyfile(RUN/name,OUT/name)

draft=OUT/'proposed-config'
(draft/'.perry/roles').mkdir(parents=True)
auth='用户2026-10-22明确要求整理CitySurvivors迁移方案、先做隔离演练、暂不正式切换；本授权仅用于外部临时根和存储，不是live政策批准'
policy=json.loads((PERRY/'templates/internal/safety_POLICY_TEMPLATE.json').read_text())
policy['approval_ref']=''  # This is the unarmed live proposal. Trial copy is separately scoped below.
policy['rules'] += [
 {'id':'cross-role','label':'跨角色与共享规范写入需原负责人或用户具体授权','patterns':['docs/design/','docs/tech/','docs/art/','AGENTS.md','todo.md']},
 {'id':'spend','label':'付费生成与下载/购买需既有具体授权','patterns':['paid API','Tripo','billing','purchase']},
 {'id':'messaging','label':'不自动跨会话通信/后台协调','patterns':['send_message_to_thread','create_thread','background coordination']},
 {'id':'live-activation','label':'本轮禁止正式接管或复制演练库到live','patterns':['live activation','copy rehearsal database','正式切换']}]
(draft/'.perry/safety.json').write_text(json.dumps(policy,ensure_ascii=False,indent=2)+'\n')
hook='''# CitySurvivors Perry 接入草案（未启用）

- Document root: perry
- Repo layout: single
- Document language: 中文
- Chat language: 中文
- Packs: [software-ops]
- Workflow conventions: M1/有界交付采用project；反馈分流采用queue；方案调查采用inquiry；资产评审采用pipeline叙述。没有mode/stage原生字段或调度器。

此文件是提议配置。原项目AGENTS及领域权限继续生效；软件包仅用于实际软件工作。没有美术/游戏专属pack。启用pack不增加收费、跨角色、发布或自动执行权限。
只沿已有权威专业源阅读，不搬移design/tech/art、资产manifest或runtime-manifest。原始文档生命周期不等于原生审批状态。
迁移选定范围外的CS/ART/DEV条目仍由原todo维护；选定条目切换后通过native查询维护唯一状态。确认前没有live写入。
任务负责角色从spec的明确声明读取；原生owner只是通用主体分类，不是三角色权限/过滤字段。卡片Loads供Agent读取，没有自动注入。
阶段/目标/KR和设计ADR本轮仅引用原源；未创建目标、指标、确认或自动授权。
发布策略未建立；Perry自身的版本/测试命令不适用于本游戏。实际游戏、资产、同机、LAN、设备、性能、真人验收由原规范要求，不由迁移自检替代。
自动派发和autopilot未启用；采用人工显式角色会话，不自动跨会话通信。
'''
(draft/'.perry/hook.md').write_text(hook)
roles={
 'planner':('策划','根README/AGENTS/todo、docs/README.md、docs/design/、docs/decisions/、docs/discussions/、docs/research/、docs/production/；自身归档与根归档索引。',
 '原生CS交付包/本人策划任务的work状态；goals/decide须加载所属lane并有实际授权。不能代领或代关ART/DEV。',
 'game/、assets/、docs/art/、docs/tech/、docs/qa/只读；接口修改交原维护者。'),
 'art':('美术','assets/、docs/art/、tools/blender/及art归档/自有索引。',
 '仅自身ART任务的work生命周期、spec与交付证据；不维护根CS包状态。',
 'game/、docs/design/、docs/tech/、docs/qa/、根todo及共享规范只读。'),
 'program':('程序','game/、docs/tech/、docs/qa/、tools/validation/、tools/playtest/、tools/analysis/、tests/及tech/qa归档与自有索引。',
 '仅自身DEV任务的work生命周期、spec与技术证据；不代关根CS包或美术任务。',
 'assets源、docs/art/、docs/design/、根todo及共享规范只读；运行副本在game/assets/由程序维护。')}
for slug,(name,owned,native,readonly) in roles.items():
 card=f'''# Role · {name}

- Accepted by: 按原项目实际验收职责；跨角色交付由接收方/策划核对，只有实际用户可确认
- Default rung: V4
- Executors: manual

## Context

本卡是未启用方案。专业职责来自source-capture/AGENTS.md；Default rung是演练提议，正式任务沿原验收要求确认，不能替代真人V5。{native}
只读范围：{readonly} 用户授权不因卡片而扩大；所有来源“已确认”保留为历史引述，不新造human actor。

## Loads

- knowledge: 项目AGENTS、角色入口、任务引用的唯一专业源
- pack: {'software-ops（仅适用软件工作）' if slug=='program' else '显式按工作适用性读取；无专属领域pack'}

## May touch

- write: {owned} 以及按上述任务权限拥有的perry/evidence/叙述。
- run: 仅已检查且已获授权的本角色命令；本轮仅外部隔离数据/存储演练，不执行游戏、资产生成或安装。

## Must escalate

- 跨角色修改涉及 `game/`、`assets/`、`docs/design/`、`docs/tech/`、`docs/art/` 时按原AGENTS权限核对；非自身辖区交原负责人或用户明确授权。
- `git push`、`publish`、`paid API`、`Tripo`、`setup`、`send_message_to_thread`、`create_thread`、`正式切换` 需要实际专项授权；本轮未提供这些live权限。
'''
 (draft/'.perry/roles'/(slug+'.md')).write_text(card)

lines=['# 全量来源处置清单（本轮快照）','','257条均有来源和处置；create表示32条演练候选，225条link-only继续由原todo权威维护，均不是live映射批准。实际返回的演练ID另见rehearsal/mapping-result.json。','','| 来源ID | 原维护者/执行角色 | 原状态摘录 | 本轮处置 |','|---|---|---|---|']
for r in inventory:
 state=r['source_state'].replace('|','／').replace('\n',' ')[:95]
 lines.append(f"| [{r['id']}](source-capture/{r['scope']}#L{r['line']}) | {r['lifecycle_writer']}／{r['responsible_role']} | {state} | {r['disposition']} |")
(OUT/'task-inventory.md').write_text('\n'.join(lines)+'\n')
(RUN/'prepared.json').write_text(json.dumps({'out':str(OUT),'plan_sha256':hashlib.sha256((OUT/'mapping-plan.json').read_bytes()).hexdigest(),'record_count':len(records)},indent=2)+'\n')
print(json.dumps({'delivery':str(OUT),'selected':len(records),'link_only':225,'parents':len(PARENTS)},ensure_ascii=False))
