# TASK-001 — 文档拆分与产品全景整理验收

日期：2026-09-16。执行者：Codex。验证级别：V3（可重跑的迁移及链接检查）。

## 验收范围

依据 [任务规格](TASK-001-spec.md)：原 README 的12个一级章节、本次对话已确认约束和7份目标文档。
文档入口：[doc/README.md](../../../README.md)。

## 原章节迁移映射

| 原章节 | 主要目的地 | 结果 |
| --- | --- | --- |
| 1 产品定位及引言 | overview.md | 保留定位与学习循环，标明设计阶段 |
| 2 目标用户与使用场景 | product.md | 保留场景，将智能设备限定改为品牌独立 |
| 3 项目目标 | overview.md、knowledge.md、learning.md | 兴趣、知识与能力、科学思维分别归档 |
| 4 成功标准 | overview.md | 保留指标，补充单家庭验证边界 |
| 5 设计原则 | learning.md | 保留8项原则，更新设备与时长表述 |
| 6 学习内容地图 | knowledge.md | 八个单元完整保留，Seestar改为设备示例 |
| 7 App主要内容 | product.md、learning.md | 入口、记录归产品；探索链、实验、引导归教学 |
| 8 首期产品边界 | overview.md | 保留月球主线、扩展及不做事项，入口标为候选 |
| 9 内容质量要求 | knowledge.md | 保留来源、准确性、适龄及观测条件要求 |
| 10 规划阶段 | overview.md、knowledge.md、product.md、engineering.md | 各方向细化事项分别归档，全景维护阶段关系 |
| 11 下一步问题 | overview.md | 保留待核对信息，明确亲子同屏已决定、专业方案由Agent提出 |
| 12 初始参考资料 | knowledge.md | 3个原始资料链接保留，明确尚未逐条审核 |

原文 SHA-256、48个片段的来源与目的地、正文哈希及明确修订对照见 [迁移清单](TASK-001-migration.json)。清单不重复保存正文。
空的原章节容器标题已计入映射；其子节分别迁移。原文备份保存在本次临时工作区，不作为产品文档的第二份来源。

## 已确认约束核对

- 亲子共用设备与界面：overview.md明确，product/visual/engineering保持一致。
- 品牌独立：核心探索不需要Seestar账号、连接或专属协议；现有家庭仍使用Seestar作为验证实例。
- 学习深度：knowledge.md保留发现、解释、预测、迁移，以及三条反复深化的主线。
- 原型辅助决策：三个入口、教学步骤、视觉和技术方案都未锁定，产品文档列出四条走查路径。
- 时间预算：learning.md保存55～80分钟、四次活动的时间区间，并把初次设备设置和跨日期等待单列。
- 先设计后实现：overview/engineering明确，本次无原型、正式应用或设备集成代码。
- 文档与管理分工：全部产品正文位于doc，根README已迁移；未创建iterations或第二套任务进度表。
- 外部家庭反馈为可选项，真实学习效果与低保真走查区分。

## 实际执行的验证

命令（项目根目录执行）：

```sh
python3 doc/perry/evidence/2026-09/TASK-001-verify.py
PERRY_HOME=/Users/bytedance/.codex/skills/Perry /Users/bytedance/.codex/skills/Perry/bin/perry-lint --root .
```

迁移检查输出：PASS；12个原章节、48个映射片段、7份目标文档、8个知识单元；38个内部链接及锚点均可解析；导航24行；根README正文已移走。
迁移过程中比对已有Perry文件SHA-256，均未被覆盖；任务与KR后续由Perry工具回写。
3个外部链接仅迁移保留，本次未联网验证科学来源或页面可用性。

当前目录不是Git仓库，无法运行git diff --check；已执行本次7份文档的尾随空格、文件末换行及范围检查。
仓库无tests/run且本次没有应用代码，未运行应用测试。可重跑脚本是本任务迁移时点的验收工具，不是后续设计内容必须保持不变的约束。

## 待后续任务处理

知识来源核对、具体教学脚本、可点击原型、视觉稿及工程选型均未执行。TASK-001完成不代表这些设计或学习效果已获验证。

## Perry回写与最终检查

perry-task done已将TASK-001标为done（V3）；perry-goals measure已记录P001-O1-KR1的accepted=1。回写后perry-lint仍为clean，恢复检查blocking=false；未启动其他任务。
