# CitySurvivors 源码运行说明

| 字段 | 内容 |
| --- | --- |
| 文档ID | game.usage |
| 类型／负责人 | 使用说明／程序 |
| 用途／读者 | 使用指南／程序、策划、美术；工具实际使用者 |
| 维护方式 | 持续维护 |
| 生命周期／修订／更新 | 当前／1.9／2026-10-22 |
| 适用范围 | 当前源码启动、配置选择与验证边界 |
| 依据／关联 | CS-056；[文档规范](../docs/production/documentation-standard.md) |

## 采用版本与前提

唯一采用：[source-20261022-ui-editor](../docs/tech/current-build.md)，当前源码／协议13；旧props-v1等ZIP仅作历史，不含后续全部源码能力。使用已安装Godot，工程feature为4.7／Compatibility，专项4.6.3／4.7.2验证范围见[QA](../docs/qa/README.md)；不因本文改写宣称再次运行通过。

## 启动

从项目根运行；`GODOT_BIN`或`--godot`指定本机可执行文件，`-h`看实际选项。编辑器打开[project.godot](project.godot)，F5进入统一菜单。

```sh
tools/playtest/start_game.sh                         # 主菜单
tools/playtest/start_game.sh free-roam               # 房主：v002分块全图自由跑图
tools/playtest/start_game.sh combat-lab              # 房主：统一测试场（五分类）
tools/playtest/start_game.sh test-ground             # 兼容旧命令，进入同一统一测试场
tools/playtest/start_game.sh join 192.168.1.20 --config res://config/lujiazui-free-roam.json --profile client_b
tools/playtest/start_game.sh host --config res://config/m1-cbd.json # Q4威胁试验
tools/playtest/start_game.sh host --config res://config/m1-cbd-q1.json # 保留通路修复，回退全部增强
tools/playtest/start_game.sh host --config res://config/m1-cbd-q0.json # 原通路对照
```

客户端必须用房主同一代码和配置；不同本机实例用不同profile。默认UDP24560，真实LAN需要实际网络／防火墙检查。无覆盖`host`使用defaults旧任务配置，不等于菜单首项自由跑图。[levels.json](config/levels.json)是菜单配置源；JSON关卡路径由菜单加载并校验。

## 场景与操作

| 场景 | 入口／当前边界 |
| --- | --- |
| 自由跑图 | v002分块；无波次边界，1～6跳地标，F3诊断；[流加载](../docs/tech/city-streaming-v1.md) |
| 统一测试场 | 战斗／物品／角色／武器／效果与材质五分类；同一房间切换，F6重置、F7停止、F2面板、F4报告；[使用与缺件](../docs/tech/guides/combat-lab.md)、[本批QA](../docs/qa/2026-10-21-unified-lab-validation.md) |
| CBD联调候选 | 菜单选“M1 · 三塔 CBD（Q4威胁试验）”；[实现／偏差](../docs/tech/m1-cbd-integration.md)、[实测](../docs/qa/2026-10-20-m1-cbd-validation.md)；v005同版，当前Q4试验；[Q0～Q4对照与回退](../docs/tech/cbd-pressure.md)；摆放评审／真人待验 |
| M1／绿地／旧任务 | 各关卡保留独立配置与历史测试，不代表[CBD](../docs/design/maps.md)及CS-051／052已验收 |

WASD移动、鼠标转镜头、左键／RT开火、右键／LT瞄准、R换弹、Q／Y测试火箭槽、Shift／L3冲刺、C或Ctrl／B蹲伏、空格跳跃、F火箭靴。E／LB交互／救援；旧任务模式Z补给、X空袭、方向指令后左键确认落点。Tab／Esc菜单，指令中Esc先取消；统一测试场中Tab改为释放工具条鼠标。具体映射与上下文以HUD、input配置和模式说明为准。

人物采用锋刃v002＋配套步枪v002，钳牙兵v001；运行身份见[runtime-manifest](assets/runtime-manifest.json)。[分层换弹](../docs/tech/character-animation-handoff-v1.md)已实现并有原版本证据，衔接仍待美术；[上身开火／受击与基础步态](../docs/tech/character-action-state.md)已解耦并修复后续实例冲刺停帧；侧移方向动画未完成，游隼未接入。

## 配置、验证与历史包

配置默认值只维护在[defaults.json](config/defaults.json)，单个覆盖合并由Config校验，房间内不能靠改文档修改规则。来源／算法／工具边界读[组件](../docs/tech/components.md)、[工具](../tools/README.md)、[测试](../tests/README.md)。

旧包及协议各见[历史交付](../docs/archive/tech/README.md)，不得当作当前源码完整副本。验证按原报告版本：源码／包内运行／同机ENet／真实LAN／Windows／物理手柄／目标机器性能／真人分别验收。CS-034新增游戏检查见QA；本批未导出新包。

## HUD可视化布局

`tools/playtest/start_hud_editor.sh` 后手动访问 <http://127.0.0.1:8864>；拖拽、缩放、字号、状态与分辨率预览。保存到game/config/hud-layout.json后游戏F8重读；无效文件保留上一有效布局。[Agent／人工草稿与PNG示意图流程](../docs/tech/guides/ui-editor.md)。调试默认headless，不自动开窗口；浏览器示意图不等于游戏GPU截图。
