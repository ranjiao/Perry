# CitySurvivors 文档总导航

| 字段 | 内容 |
| --- | --- |
| 文档ID | docs.index |
| 类型／负责人 | 总索引／策划；各领域入口由原角色维护 |
| 用途／读者 | 项目治理与协调／策划、程序、美术 |
| 维护方式 | 持续维护 |
| 生命周期／修订／更新 | 当前／1.2／2026-10-22 |
| 适用范围 | 新Agent会话导航与人类查阅；不复制阶段、数值或资产清单 |
| 依据／关联 | [文档规范](production/documentation-standard.md)、CS-054～056 |

## 新会话怎么开始

读[AGENTS](../AGENTS.md)确认角色／权限，读[根todo](../todo.md)确认阶段／任务；再从下表进入当前源。不要把“当前文档”“用户确认”“已实现”“已验证”合为一个状态。默认检索不扫archive，追查决策或旧证据再进入。

| 要找什么 | 从这里进入 | 维护与限制 |
| --- | --- | --- |
| 当前任务与跨角色依赖 | [全局todo](../todo.md) | 策划；阶段唯一入口 |
| 游戏定位与M1范围 | [当前企划](design/game-design.md)、[M1范围](design/prototype-scope.md) | 两者都是设计输入，不是运行证明 |
| 玩法分类／所有策划规则 | [设计索引](design/README.md) | 武器／角色／敌人／能力／地图／Perk与附表 |
| 美术风格、模型与效果 | [美术入口](art/README.md)、[画廊](art/gallery.md) | 八类分类与画廊已交，CS-055文档静态验收通过；外观／游戏接入另验 |
| 素材总登记／武器效果 | [资产manifest](../assets/manifest.md)、[美术武器页](art/weapons.md) | 唯一源／许可与导出登记不在本页复制 |
| 实际接入素材版本 | [运行manifest](../game/assets/runtime-manifest.json) | 程序维护；最新导出不代表已接入 |
| 程序组件／接口／运行构建 | [组件总表](tech/components.md)、[程序入口](tech/README.md)、[采用源码](tech/current-build.md)、[素材接口](tech/asset-integration.md) | CMP-001～008已登记，采用源码与历史包分开；CS-056文档静态验收通过，不代验代码 |
| 验证步骤与证据 | [QA索引](qa/README.md) | 程序；静态、引擎、同机、真实LAN／设备与真人分层 |
| 决策、授权、确认与待决 | [决策索引](decisions/README.md) | 用户指令与ADR；部分已替代的授权链仍保留 |
| 制作规则／交接／模板 | [制作索引](production/README.md) | 含文档治理、M1交接与审查 |
| 外部资料与研究局限 | [研究索引](research/README.md) | 案头研究不等于本地游戏能力 |
| 原始讨论与用户修正 | [讨论索引](discussions/README.md) | 保留依据，不当作当前配置表 |
| 旧设计与迁移记录 | [归档索引](archive/README.md) | 仅回溯；不得作当前输入 |

## 按工作用途查阅

先按维护角色进入[策划](design/README.md)、[程序](tech/README.md)、[美术](art/README.md)。角色入口区分工作清单／按需工作稿、长期专业资料、对象总表、协作接口、使用指南和验证／历史；同一正文可以跨角色读取，维护权仍归原角色。

| 用途 | 当前入口 |
| --- | --- |
| 任务工作区 | 从角色todo的任务进入；结束需提炼／留证／清理，不在总导航堆中间过程 |
| 长期专业资料 | [策划资料](design/README.md#长期专业资料当前m1与战斗)、[研究](research/README.md)，程序／美术专业资料由各自入口组织 |
| 对象总表与索引 | [策划六类总表](design/README.md#对象总表与索引)、[程序组件](tech/components.md)、[资产manifest](../assets/manifest.md) |
| 协作接口与交付要求 | [制作／交接入口](production/README.md#协作接口与交付要求)及各角色对外接口 |
| 使用指南 | [试玩执行](production/m1-playtest-plan.md)；工具／素材指南由程序CS-078／美术CS-079提炼，现有操作源仍可引用 |
| 验证与历史证据 | [策划证据](production/evidence/README.md)、[原始讨论](discussions/README.md)、[QA](qa/README.md)、[归档](archive/README.md) |
| 项目治理与协调 | [AGENTS](../AGENTS.md)、[根todo](../todo.md)、[决策](decisions/README.md)、[文档规范](production/documentation-standard.md) |

本轮策划整理见[报告](production/evidence/2026-10-22-planner-documentation-review.md)，两角色接续要求见[正式交接](production/documentation-handoff.md)。CS-078／079与CS-080是本轮整理，第一批CS-055／056验收不重新打开。

## 第一批整理证据与既有遗留

[导演验收报告](production/evidence/2026-10-20-documentation-acceptance-review.md)逐项核对D01～D07、两边证据、归档与兼容清理。CS-055／056在文档治理静态范围内通过，用户评审及游戏／素材实测另记。

- 策划：入口、规范、分类、模板及历史整理见[原迁移快照](production/2026-10-20-documentation-migration-review.md)，本次已汇总三角色索引与清理23个短跳转。
- 美术：[八类入口](art/README.md)、[报告](art/2026-10-20-documentation-review.md)、[归档子索引](archive/art/README.md)。ART-070旧发布器适配保留，当前不执行旧发布器重生覆盖。
- 程序：[组件](tech/components.md)、[报告](tech/2026-10-20-documentation-review.md)、[tech归档](archive/tech/README.md)／[QA归档](archive/qa/README.md)。五份字节绑定旧清单及固定QA输出暂保留；DEV-070后续独立迁移。

角色todo分别见[美术](art/todo.md)、[程序](tech/todo.md)；后续工具问题列全局CS-058／059，不重新打开已完成的静态文档验收，也不把CS-051／052玩法修复视为完成。
