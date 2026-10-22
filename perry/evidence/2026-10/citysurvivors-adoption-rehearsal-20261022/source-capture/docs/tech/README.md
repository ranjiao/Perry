# 程序阅读入口

| 字段 | 内容 |
| --- | --- |
| 文档ID | docs.tech.README |
| 类型／负责人 | 导航／程序 |
| 用途／读者 | 对象总表与索引／程序、策划、美术；按用途阅读 |
| 维护方式 | 持续维护 |
| 生命周期／修订／更新 | 当前／2.2／2026-10-22 |
| 适用范围 | 程序工作、长期专业源、总表、接口、指南与证据 |
| 依据／关联 | CS-078；[用途规范](../production/documentation-standard.md)、[正式交接](../production/documentation-handoff.md#3-cs-078-程序) |

## 我的工作

程序领取与内部拆分只看[程序todo](todo.md)，阶段／全局优先级看[根todo](../../todo.md)。没有实际未定记录就不建空工作稿；有工作稿时经所属DEV链接进入，结论回填正式源，必要失败证据转留证，纯重复稿完成依赖检查后清理。

本轮分类／处置、固定消费者及U01～U06检查经[CS-078报告](evidence/2026-10-22-documentation-review.md)进入，完整文件用途见[分类清单](evidence/classification.md)。不从历史记录或聊天推断当前任务。

## 长期专业资料

| 阅读任务 | 维护源 |
| --- | --- |
| 架构、权威与生命周期 | [运行架构](architecture.md)、[组件详情](component-details.md) |
| 移动与分层动作、命中 | [动作状态与恢复](character-action-state.md)、[钳牙分区命中](qianya-hitboxes-v10.md) |
| CBD通路与分组威胁 | [通路恢复](cbd-path-recovery.md)、[Q0～Q4实现](cbd-pressure.md)、[CBD联调与差异](m1-cbd-integration.md) |
| 地图分块与原生物理 | [流加载](city-streaming-v1.md)、[物品破坏与物理](interactive-props-v1.md) |
| 测试场与UI工具实现 | [统一测试场组件](combat-lab.md)、[战斗HUD组件](combat-hud.md)、[UI编辑工具组件](hud-layout-editor.md) |
| 尚未收敛的专业提案 | [破坏预研](destruction.md)、[性能计划](performance-budget.md)；保留草拟与未验边界 |

这些页维护实现职责／约束；实际行为与参数来自代码／有效配置，验证结论回原报告，不因补目录再次通过。

## 对象总表

[components](components.md)是唯一CMP分类总表；详情和专题引用它，不另建组件台账。当前运行副本及精确版本只在[runtime-manifest](../../game/assets/runtime-manifest.json)维护；源资产／许可只在[美术manifest](../../assets/manifest.md)，本入口不重抄路径／参数。

## 协作接口

| 提供／使用任务 | 维护源 |
| --- | --- |
| 所有美术素材接入与职责 | [素材总则](asset-integration.md) → [人物动画](character-animation-handoff-v1.md)、[武器](weapon-handoff-v1.md)、[物品](interactive-prop-handoff-v1.md)、[特效音频](effects-audio-handoff-v1.md) |
| 地图交付与后处理 | [地图契约](map-streaming-contract-v1.md) |
| 会话、恢复与快照 | [网络接口](networking.md) |
| Agent／人工UI草稿交接 | [UI文档／HUD接口](ui-layout-contract.md)；操作另看指南 |
| 分类首件验收 | [首件清单](../qa/asset-handoff-v1-checklist.md)，不代表任意交付已可用 |

## 使用指南

| 使用者要完成的事 | 指南 |
| --- | --- |
| 策划／美术：启动测试场、分类、测量、停止与取报告 | [统一测试场使用指南](guides/combat-lab.md) |
| 美术／策划／Agent：搭菜单／结算、Frame层级／逐层选择、多选排布、跨页复制／替换图片、调整HUD及导出 | [UI与HUD使用指南](guides/ui-editor.md) |
| 从源码启动或加入游戏 | [game使用说明](../../game/README.md)；当前组合回采用入口 |
| 程序：选择检查与保护旧输出 | [tests](../../tests/README.md)、[旧工具固定输出说明](../../tools/README.md)；固定消费者见本轮报告 |

指南维护步骤与结果，接口维护字段／兼容，组件维护原理；同一事实不再另写内部／外部版本。

## 验证与历史

[QA索引](../qa/README.md)按被测对象进入原报告／日志；[程序证据索引](evidence/README.md)列原位历史交付、review和本轮检查。原始JSON、截图、固定清单、历史Markdown不因分类改字节，例外在处置清单登记。

更早归档从[tech](../archive/tech/README.md)／[QA](../archive/qa/README.md)按需回溯；默认专业检索排除archive、evidence、work。历史方案、旧ZIP／协议和旧500米场地不能驱动新实现。同机ENet、图形、设备、真人与用户确认继续分层。

## 项目治理与协调

唯一[当前采用入口](current-build.md)区分源码、历史ZIP、展示与正式运行；不在本页维护第二份构建状态。共享[规范／目录／决策](../README.md)由策划维护；阶段与CS状态回根todo。程序只更新自己辖区，跨角色清单交策划沿CS-080复核，不代报美术CS-079或玩法验收。
