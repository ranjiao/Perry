# CitySurvivors 迁移方案与隔离演练

**方案与演练已完成；未正式切换。** 所有配置、任务ID及todo预览都仅用于本轮提议／隔离试验，不能原样安装到CitySurvivors。

| 阅读目的 | 入口 |
|---|---|
| 了解三角色如何接入roles／modes／packs／templates | [迁移方案](迁移方案.md) |
| 查看三角色任务链、状态判读与待决字段 | [任务映射与待决](任务映射与待决.md) |
| 查看全部257条来源任务的处置 | [任务清单](task-inventory.md)、[完整原文与出处](source-inventory.json) |
| 明确旧todo如何逐条退出状态写入 | [旧todo与切换边界](旧todo与切换边界.md) |
| 查看实际演练、拒绝案例和恢复证据 | [演练报告](演练报告.md)、[最终摘要](rehearsal-final/summary.json) |
| 审阅未启用的角色／项目配置 | [hook](proposed-config/.perry/hook.md)、[策划卡](proposed-config/.perry/roles/planner.md)、[美术卡](proposed-config/.perry/roles/art.md)、[程序卡](proposed-config/.perry/roles/program.md)、[政策提议](proposed-config/.perry/safety.json) |
| 查看拟导入内容及来源冻结范围 | [32条试验计划](mapping-plan.json)、[39文件捕获清单](source-manifest.json)、[任务spec草案](proposed-task-specs/CS-080-source-spec.md) |
| 查看正式切换前的新鲜度问题 | [并行来源变化](source-delta/recheck.json)、[ART-087实际差异](source-delta/art-todo.diff) |

全量来源：CS 80条、ART 88条、DEV 89条。选择32条演练，另外225条link-only继续由原角色／原todo维护。没有将257条全部灌入新看板，没有创建目标／KR或批准设计。

实际验证：32条映射、15条parent、完整5页查询；重复执行新增0；模拟中断后匹配5条、补建27条，并补齐关系；原生export／import重放32条一致；重复导入、旧expect、未核验V4关单、重复来源身份和改变捕获字节均按各自边界拒绝。

本轮没有独立业务V4／真人V5，没有运行游戏／素材生产或把旧检查当作本轮验收。原生owner、子项优先级和验证层级中的试验占位值，不能带入正式接管而省略原维护者确认。

演练期间有其他会话提交及继续修改项目。最终发现美术todo与资产manifest较快照变化，已保留差异；不覆盖旧输入，不把新旧时点混合。冻结快照上的演练成功不表示当前可以直接切换。

全部材料作为Perry的历史接管案例保存在此处。CitySurvivors仍使用原流程；正式接管需要新的来源核对、实际字段／权限确认、旧写者逐条退休方案、恢复范围验证和明确切换授权。

来源字节归档说明：classification.md原始末尾空行必须保留，按[source-storage.json](source-storage.json)保存为gzip，脚本只在新的临时根恢复并逐字节验SHA；不规范化原文。原始带上下文diff也保留gzip，展示diff为等价的零上下文版本。
