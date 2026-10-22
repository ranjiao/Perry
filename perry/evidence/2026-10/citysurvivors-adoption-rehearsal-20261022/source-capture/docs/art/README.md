# 美术入口

| 字段 | 内容 |
| --- | --- |
| 文档ID | art.readme |
| 类型／负责人 | 领域索引／美术 |
| 用途／读者 | 对象总表与索引／美术开工；策划、程序查找素材与交付 |
| 维护方式 | 持续维护 |
| 生命周期／修订／更新 | 当前／2.0／2026-10-22 |
| 适用范围 | 美术阅读路由；分类页不代替资产登记或运行采用 |
| 依据／关联 | CS-079／ART-089；[规范](../production/documentation-standard.md)、[目录规则](../production/project-structure.md)、[正式交接](../production/documentation-handoff.md) |

先从[总导航](../README.md)了解项目；阶段、优先级与跨角色状态只查[根todo](../../todo.md)。策划／程序取素材可直接读[选择与预览指南](asset-selection-preview-guide.md)，接入前读[美术交付入口](asset-delivery.md)。

## 我的工作

- [美术todo](todo.md)：领取、依赖、产物、退回项；不在首页重抄任务状态。
- [建筑样楼工作稿](environment/building-visual-upgrade.md)：ART-064未定方案与试验顺序，尚非长期制作标准；结束去向写在稿内。
- 新任务确有试验笔记时才建一份工作记录，按[工作稿模板](../production/templates/work.md)列任务、未定问题、结论去向和结束条件；不得把每次交付都当新规范。

## 长期资料

| 主题 | 唯一专业源 | 阅读边界 |
| --- | --- | --- |
| 风格 | [Art Bible](style-guide.md) | 已确认方向与美术建议分列；人物名字、尺寸与机制读策划源 |
| 制作方法 | [角色制作检查单](character-production-lessons-v001.md) | 可复用步骤；旧任务费用、失败与当时建议另留证据 |
| 动画与工具 | [动画／制作流程](animation-workflow.md)、[文档工具](documentation-tooling.md) | 每只骨架单独适配；旧发布器不用于整理导航 |
| 实景转译 | [陆家嘴参考](environment/lujiazui-photo-reference-v001.md) | 原研究与转译依据，不替代当前地图／物件采用 |

## 对象总表

[assets/manifest](../../assets/manifest.md)是唯一资产源、许可、导出登记；运行副本与实际采用查[runtime-manifest](../../game/assets/runtime-manifest.json)和[程序当前构建](../tech/current-build.md)。图组较新不代表运行更新。

| 分类链接视图 | 查什么 |
| --- | --- |
| [人物](characters.md) | 全员二维设定、既有角色本体与动作的单项入口 |
| [敌人](enemies.md) | 概念、可用交付与失败／暂缓样本 |
| [武器图鉴](weapons.md) | 全部效果、固定外形与单项接口；不另登记源许可 |
| [环境／地图](environment/README.md) | 城市、CBD、树木、实验室及对应版本交接 |
| [道具](props.md) | 分件、互动表现与碰撞证据 |
| [UI](ui.md) | 操作流程制作输入、结构图与组件审阅包 |
| [特效／音频](effects-audio.md) | 独立表现、试听及程序适配边界 |
| [动作源](animation-workflow.md) | 现有源库与逐骨架交付；不是通用成品动画包 |

人物／尺寸只读[人物总表](../design/characters.md)，武器、敌人与地图分别读[武器](../design/weapons.md)、[敌人](../design/enemies.md)、[地图](../design/maps.md)。不维护“内部／外部”两套参数。

## 协作接口

- [美术交付入口](asset-delivery.md)：提供者／消费者、接口权威源、版本搭配、检查与退回。
- [环境当前组合交接](environment/lujiazui-integration-handoff.md)：美术地图、CBD冻结输入与运行身份；不能跨版拼接。
- [素材接入总则](../tech/asset-integration.md)及其分类规范由程序维护；[上级3D流程](../../../doc/agent-3d-art-workflow.md)定义共用制作过程。新授权优先，未定字段不补猜。

## 使用指南

- [素材选择、预览与退回](asset-selection-preview-guide.md)：从选图到版本核对、打开审阅、反馈与恢复。
- [画廊](gallery.md)：各类当前展示入口；制作源与检查明细回对应单项，不靠时间戳猜版本。
- [文档工具使用与限制](documentation-tooling.md)：只读检查命令、输出、旧发布器副作用与恢复边界。

## 验证／历史

[证据入口](evidence/README.md)区分本轮文档检查、版本化素材检查与历史提案；[分类／处置清单](documentation-dispositions.md)列每份文档的用途、读者、维护方式、入口、指纹与保留原因；[CS-079报告](evidence/2026-10-22-art-documentation-review.md)交策划统一复核。

原确认、失败、费用和未测项只在对应版本证据中解释；概念认可、独立资产、引擎、游戏、同机多人、真实LAN、设备／性能、用户确认分开。[CS-055旧报告](2026-10-20-documentation-review.md)及[美术归档](../archive/art/README.md)只供回溯，不重新作为当前规范输入。
