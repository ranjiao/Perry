# 当前采用构建

| 字段 | 内容 |
| --- | --- |
| 文档ID | tech.current-build |
| 类型／负责人 | 采用入口／程序 |
| 用途／读者 | 项目治理与协调／程序、策划；采用与任务核对者 |
| 维护方式 | 持续维护 |
| 生命周期／修订／更新 | 当前／1.12／2026-10-22 |
| 适用范围 | 当前保存源码身份、战斗HUD／布局工具、启动及验证边界；历史ZIP不随本页升级 |
| 依据／关联 | 用户要求UI接入、内部留白、headless及可视化布局；CS-061／065；[程序todo](todo.md) |

## 当前身份

当前采用 **source-20261022-ui-editor**，协议13，未提交源码工作树。统一测试场包含战斗、物品、角色、武器、效果／材质五分类；CBD继续保留Q0～Q4，战斗素材组合没有被展示样件替换。

[源码快照](../qa/ui-editor/source-snapshot.json)登记HEAD、逐文件SHA、组合指纹与有效配置，父版本为[source-20261021-unified-lab](../qa/unified-lab/source-snapshot.json)；[本轮变化](../qa/ui-editor/source-changes.json)分开保存入场差异与交付差异。HEAD、协议相同均不足以与旧源码混联。

当前新增ART-062 v0.5八张UI运行副本、只读状态适配和同源布局编辑器。地图／人物／武器实战组合保持；其他角色WIP继续保留，不认领其所有权。布局文件可由用户继续编辑，快照只表示记录时保存内容。
通用UI工具当前按 **ui-studio-frames-20261022** 记录[工具源码与验证](../qa/2026-10-22-ui-studio-frames-validation.md)，增加Frame／嵌套局部坐标、逐层选择及继承，并重设计通用工作台／原HUD模式视觉；[前批扁平组验证](../qa/2026-10-22-ui-studio-batch-validation.md)与[原多页面验证](../qa/2026-10-22-ui-studio-validation.md)保留。游戏源码／玩法／菜单与上方HUD交付快照未由本轮升级，通用文档v3不改变游戏协议13。

## 启动与回退

- 统一测试场：`tools/playtest/start_game.sh combat-lab`，或菜单选“统一测试场 · 战斗／物品／展示”。旧`test-ground`命令进入同一场景；旧配置仅留内部回归，不再列第二个菜单入口。[操作](guides/combat-lab.md)／[实现与扩充](combat-lab.md)。
- F2五分类；F6重置；F7停止；F4报告；Tab场内工具条鼠标。展示内可旋转／缩放、选片段、暂停／循环／调速／拖动时间。
- CBD仍选“M1 · 三塔 CBD（Q4威胁试验）”或`tools/playtest/start_game.sh host --config res://config/m1-cbd.json`；Q4→Q3→Q2→Q1逐档回退，Q0留原通路对照。默认菜单首项仍是v002自由跑图。
- 客户端采用相同源码／完整覆盖；房间参数不热换代码。无覆盖host仍是defaults旧任务，不等于CBD或统一测试场。

- HUD布局：`tools/playtest/start_hud_editor.sh`，手动打开本地8864；保存后F8。Agent／人工独立草稿与PNG导出见[操作指南](guides/ui-editor.md)。

## 地图、素材与展示身份

CBD仍使用[runtime-manifest](../../game/assets/runtime-manifest.json)中的v005城市与CBD v001叠加，旧自由跑图／绿地用v002；锋刃v002、配套步枪v002、钳牙v001的实战采用保持。没有切换城市v006或把角色候选v003当作生产衔接验收。

统一场的展示输入逐文件见[lab manifest](../../game/assets/lab/manifest.json)，资源只作展示：锋刃运行／候选、游隼、钳牙、16把独立武器和10个效果／材质样件。H3～H16共14名缺模型／动作，界面明确禁用；终端／宝箱为无正式奖励的程序测试样件。工程feature仍为Godot4.7／GL Compatibility，无新依赖或新ZIP。

## 实现与验证

当前UI与工具见[本批QA](../qa/2026-10-22-hud-editor-validation.md)：双引擎各87项HUD检查、模型／主场景／同机ENet及25项浏览器操作。最终修订仅headless运行；浏览器排版图不代替GodotGPU帧。


[统一测试场原批QA](../qa/2026-10-21-unified-lab-validation.md)与[汇总](../qa/unified-lab/validation.json)覆盖分类切换、原生物品推动、终端／开箱、模型／动画采样、预览无伤害、输入隔离、重置及同机ENet确认／报告／重连。双引擎模型／旧夹具、双引擎真实图形、原战斗和物品回归各有独立证据。

原Q4[QA](../qa/2026-10-21-cbd-pressure-validation.md)和[威胁组件](cbd-pressure.md)继续约束通路／密度试验；本批没有重做42组路径、12局战斗或22只负载。此前人物／俯仰修复的报告仍限原被测范围。

## 未关闭边界

- 14名角色缺件、正式终端／宝箱美术及用途／奖励、更多效果素材、长射道与其他旧机制完整迁移仍待后续。
- 双引擎展示退出均有两条纹理释放告警；功能通过与资源清理未通过分别记录，不称无告警版本。
- 真人易用性／美观、真实双机LAN、Windows、物理手柄和目标机长局未验；不代标CS-061整包或CS-063确认。
- DEV-080四人22只尾部耗时、DEV-066生产动作接触过渡、CS-034空间评审、CS-048边界与CS-051／052完整规则矩阵没有由统一测试场交付关闭。
