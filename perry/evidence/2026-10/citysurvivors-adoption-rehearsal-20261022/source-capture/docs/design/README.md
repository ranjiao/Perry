# 策划入口与文档分类

| 字段 | 内容 |
| --- | --- |
| 文档ID | design.index |
| 类型／负责人 | 索引／策划 |
| 用途／读者 | 对象总表与索引／策划、程序、美术 |
| 维护方式 | 持续维护 |
| 生命周期／修订／更新 | 当前／2.0／2026-10-22 |
| 适用范围 | 策划工作、长期规则、对象总表、跨角色交付与历史证据 |
| 依据／关联 | [总导航](../README.md)、[用途规范](../production/documentation-standard.md)、CS-077 |

## 我的工作与阅读顺序

当前阶段、优先级与策划任务只查[根todo](../../todo.md)；先读[企划](game-design.md)、[M1范围](prototype-scope.md)，按任务进入下列源。实际构建和已接入版本回[程序入口](../tech/README.md)，美术原件与外观状态回[美术入口](../art/README.md)。

## 任务工作区

当前没有需要单独持续维护的策划临时稿；已有设计提案仍是长期专业资料，不按“未采用”当临时垃圾。新任务有中间记录时按[工作稿规则](../production/project-structure.md#2-任务工作区)在work/<task-id>.md集中维护，并从所属CS任务链接；任务结束需有结论去向。

## 对象总表与索引

| 对象 | 唯一源 | 边界 |
| --- | --- | --- |
| 人物 | [characters](characters.md) | 16人正文、体型／性格／职责与招牌候选集中一份；不等于正式16人运行阵容 |
| 武器 | [weapons](weapons.md) | 参数、距离与资源层次；具体六人攻击规则由下方单项承接 |
| 敌人 | [enemies](enemies.md) | 类型、行为／攻击／HP；M1仍按范围只采用近战A |
| 能力 | [abilities](abilities.md) | 共同动作与角色专属机动候选，不用人物背景赠送运行技能 |
| 地图 | [maps](maps.md) | 母版、CBD、任务边界与测试场的关系 |
| Perk | [perks](perks.md) | 六卡规则及收益边界；非M1前置 |

总表允许兼有完整规则；不再派生内部版／对外版。稳定ID、资产ID和运行版本分开。

## 长期专业资料：当前M1与战斗

| 主题 | 规则源与用途 |
| --- | --- |
| 定位／范围 | [当前企划](game-design.md)、[原型范围](prototype-scope.md)、[战斗规则](combat.md) |
| 场地／来敌 | [CBD布局](m1-cbd-battlefield.md)、[钳牙威胁试验](m1-qianya-pressure.md)、[任务边界](mission-boundary.md)；试验参数与正式采用分开 |
| HUD／实验室 | [M1 HUD](m1-hud-flow.md)、[紧凑实验室](test-ground.md)、[测试场机制清单](test-ground-cases.md)；设计不代表当前工具能力已全部实现 |
| 六人攻击公共规则 | [输入、状态与资源](characters/attack-rules.md)；六人方向已有认可，具体初值与接入另验 |
| 六人攻击单项 | [锋刃](characters/fengren-attack.md)、[游隼](characters/yousun-attack.md)、[铁砧](characters/tiezhen-attack.md)、[霆弧](characters/tinghu-attack.md)、[壁垒](characters/bilei-attack.md)、[星轨](characters/xinggui-attack.md) |
| 扩展候选 | [单武器变化探索](characters/attack-variants.md)、[人物常态候选](characters.md#candidate-weapons)；早期备选不覆盖当前推荐 |

## 长期专业资料：后续方案与参考

| 主题 | 源与采用边界 |
| --- | --- |
| 城市流程与机动 | [城市跑图](city-traversal-and-encounters.md)、[完整一局](large-map-run.md)、[载具／积分](vehicles-and-tactical-points.md)、[旧短闭环机制参考](prototype-loop.md)；仍有效，不因非M1归档 |
| 遭遇／特殊威胁 | [敌潮](encounters.md)、[Boss](boss-encounter.md)、[惊嚎兽](enemy-h-jinghao.md)、[明珠激光](oriental-pearl-laser.md)；后续候选，不增加M1门槛 |
| 外部研究 | [研究索引](../research/README.md)；外部事实、策划推断与本地实测分开 |

## 长期专业资料：算术附表

以下是计算依据，不是当前参数源或实测平衡。

| 附表 | 用途 |
| --- | --- |
| [武器射程](weapon-range-estimates.md)、[强力体验算例](weapon-power-examples.md) | 射程、投影、理论TTK与有限预算 |
| [敌人阈值](enemy-combat-estimates.md)、[Perk收益](perk-benefit-estimates.md) | 理想阈值、走位窗口与卡片收益 |
| [M1两枪预期](m1-combat-test-estimates.md)、[波次时序](m1-wave-timing-estimates.md) | 离线预期与人数节奏，不代替真人／运行证据 |
| [完整局说明算例](large-map-run-examples.md) | 后续局长／共享积分的说明场景 |

## 协作接口与交付要求

| 使用方／任务 | 正式输入 |
| --- | --- |
| 程序／美术：CBD | [场地交接](../production/m1-cbd-handoff.md)、[规则修正](../production/m1-rule-fixes-handoff.md) |
| 程序／美术：实验室 | [重构交接](../production/test-ground-refactor-handoff.md)、[两枪＋钳牙验收矩阵](m1-combat-test-matrix.md) |
| 美术：人物视觉设定 | [CS-076正式任务](../../todo.md#cs-076-全员角色视觉设定)，人物／尺寸仍回characters |
| 程序／美术：文档整理 | [CS-078／079正式交接](../production/documentation-handoff.md)，内部任务自行拆分 |

## 使用指南

[试玩执行计划](../production/m1-playtest-plan.md)说明人员、阶段、记录、通过／回退与开测前置，是策划维护的执行指南。

程序工具当前综合说明见[统一测试场](../tech/combat-lab.md)、[HUD编辑器](../tech/hud-layout-editor.md)及[当前采用](../tech/current-build.md)；其使用者指南由CS-078从实现说明中提炼，策划不复制操作源。美术素材选择／预览指南由CS-079提供，现有[画廊](../art/gallery.md)仍可查。

## 验证与历史证据

[策划证据索引](../production/evidence/README.md)集中审查、文档检查与旧记录；[原始讨论](../discussions/README.md)保留用户依据；[程序QA](../qa/README.md)记录实际被测版本。默认不从这些目录取当前参数。

[归档索引](../archive/README.md)保留已替代正文，原始记录不因新分类改写结论；固定路径／快照约束见[本轮处置清单](../production/evidence/2026-10-22-planner-documentation-review.md)。

## 项目治理与协调

[AGENTS](../../AGENTS.md)、[全局todo](../../todo.md)、[决策](../decisions/README.md)、[文档规范](../production/documentation-standard.md)、[目录规则](../production/project-structure.md)与[模板](../production/templates/README.md)由策划维护。游戏、资产及其他角色文档继续只读。
