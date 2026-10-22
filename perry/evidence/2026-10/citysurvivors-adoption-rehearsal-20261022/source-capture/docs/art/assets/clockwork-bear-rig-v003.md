# 发条大熊骨架与基础动作 v003

| 字段 | 内容 |
| --- | --- |
| 文档ID | art.assets.clockwork-bear-rig-v003 |
| 类型／负责人 | 人物绑定／动画交付／美术 |
| 生命周期／修订／更新 | 当前／1.0／2026-10-22 |
| 适用范围 | ART-088；已认可本体v002的本地骨架、蒙皮、空手基础动作；动作外观待评审 |
| 依据／关联 | [人物唯一源](../../design/characters.md#h10)、[本体建模v002](clockwork-bear-body-v002.md)、[人物接口](../../tech/character-animation-handoff-v1.md)、[制作复盘](../character-production-lessons-v001.md) |

## 预览与用途

![实际GLB行走预览](../../../assets/previews/characters/clockwork_bear/v003/walk.gif)

[待机](../../../assets/previews/characters/clockwork_bear/v003/idle.gif) · [原地跑](../../../assets/previews/characters/clockwork_bear/v003/run.gif) · [三周期相位对照](../../../assets/previews/characters/clockwork_bear/v003/motion_preview.gif) · [七个关节探针](../../../assets/previews/characters/clockwork_bear/v003/deformation_sheet.png) · [Godot实际GPU蒙皮](../../../assets/previews/characters/clockwork_bear/v003/godot_motion_sheet.png)。均为最终导出GLB读回后的实际形变，未接主游戏。

单段GIF按原动作时长播放，约12FPS、10ms时长量化，源动作30FPS；相位并列图统一周期速度，只比较姿态，不能比较真实跑速。Blender重导入前显式设30FPS，并按交付片段时长检查，避免默认24FPS导致预览速度改变。

## ID、源与授权

资产ID `chr_clockwork_bear_rig_v003`，来源／唯一编辑源见[manifest](../../../assets/manifest.md)。用户2026-10-22回复“好，继续开始骨骼和动作绑定”，记录为本体v002外形认可及本次制作授权，**不扩展为新动作／蒙皮已经认可**；[原话、源SHA与路线](../../../assets/source/characters/clockwork_bear/v003/production-record.json)。

当前本体v002和标准化首稿v001分别做了Tripo免费预检，均返回`riggable=false`、类型biped，未给具体原因。不能据此断言方块风或某个网格岛就是原因，也没有绕过结果购买绑定。本轮改为Blender本地绑定，复用仓库已登记Mixamo源及本地编制跑步，不新增下载／付费动作；原有来源许可限制继续沿用。

## 接口

| 项目 | 当前交付 |
| --- | --- |
| 骨架 | **52骨**：24个身体／组织骨＋28个指骨；`Root`地面原点、`Hip`髋部位移、`Pelvis`下身分支、`Waist`上身分支；Root／Pelvis不承载网格权重 |
| 网格／材质 | 原14,564三角、1材质／2K基础色；同位置UV／法线拆点的权重统一，最多4个归一化影响骨 |
| 坐标 | 米制，GLB +Y上／-Z前，根scale=1，脚底中心原点；动作原地，游戏负责水平位移 |
| 人体拟合 | 沿v002内部参考置骨，肩部骨点间66cm；鞋内足底／发下颅顶仍为美术拟合，不能把含鞋发2.16m外包围盒说成208cm裸模实测 |
| 骨表与动作表 | [52骨实际父子／rest映射](../../../assets/source/characters/clockwork_bear/v003/bone-map.json)／[片段来源与SHA](../../../assets/source/characters/clockwork_bear/v003/clip-table.json)；不是锋刃41骨或游隼88骨的直接替换 |
| 导出 | `assets/exports/characters/clockwork_bear/v003/clockwork_bear.glb`；[接口JSON](../../../assets/exports/characters/clockwork_bear/v003/interface.json) |

| 片段 | 时长／循环 | 实际来源与处理 |
| --- | --- | --- |
| `idle` | 1.966667秒／循环 | 既有`Idle (1).fbx`；A-rest手臂补偿、减小躯干／锁骨摆动、闭环 |
| `walk` | 1.166667秒／循环 | 既有`Dwarf Walk.fbx`；沿本体腿长重定向，保持沉稳短步，闭环 |
| `run` | 0.900000秒／循环 | 本地空手原地跑草稿；按大体型调整摆臂／抬腿，没有购买Tripo跑步 |

每帧按实际网格最低点补髋高，未做游戏接触锁脚、跑速或脚底IK配套。GLB不保证携带Godot循环属性；程序应对三段显式设置`Animation.LOOP_LINEAR`。七个`probe_*`是中立、抬臂、屈肘、转头、抬腿、转躯干与屈指检查，不作为额外玩法片段导出。

## 导出版本

唯一执行源：[build_clockwork_bear_rig_v003.py](../../../tools/blender/build_clockwork_bear_rig_v003.py)＋冻结本体v002＋仓库FBX源；source中的`clockwork_bear.blend`为派生快照。代理求权重数据保存在同目录`binding-cage.npz`，不混入可见GLB。

本地流程：临时14mm体素代理→约7000顶点／14000三角的封闭主要身体→Blender自动骨热权重→最近三角重心插值回原表面→头眼／靴子和12个手部岛专项赋权→躯干串腿、领口与髋中线修正→14次表面过渡平滑→4影响骨限制。**可见模型没有体素重建或重新生成**。

初次高度分区把高领口误分给Head，自动权重还把部分大腿影响带入躯干。已按实际伸长边定位，修正头发／皮肤／领口区域和躯干、髋部过渡；前后证据在[初次记录](../../../assets/previews/characters/clockwork_bear/v003/before_weight_cleanup/build_report.json)、[当前构建](../../../assets/previews/characters/clockwork_bear/v003/build_report.json)与[当前热点](../../../assets/previews/characters/clockwork_bear/v003/deformation_hotspots.json)。

## 检查与接入

| 层级 | 实际证据与结论 |
| --- | --- |
| 本体保持／循环 | [实际导出审计](../../../assets/previews/characters/clockwork_bear/v003/skin_loop_audit.json)：14,564个三角全部对应，最大角点差约0.000925mm、UV差0；中立蒙皮误差约0.000267mm；三段首尾网格差0 |
| 权重／动作采样 | 无未赋权顶点、1～4影响骨；124个30FPS烘焙帧检查为有限坐标。5mm以上边的各动作最坏95分位伸长比约1.10～1.17，最大局部比约3.13～4.86；这是定位指标，**不是全部关节或连续动作审美合格证明** |
| 真实视觉 | [读回渲染](../../../assets/previews/characters/clockwork_bear/v003/render_report.json)：三周期50张抽帧＋7探针已查看；未再见初版领口大块拉开，局部肩腋／髋布面挤压和脚步节奏仍待评审 |
| Godot数值 | [4.6.3实际Skeleton3D／AnimationPlayer](../../../assets/previews/characters/clockwork_bear/v003/godot_report.json)：52骨、3片段、归一化rest误差约0.000001m内、Root位移0；原始权重和误差按引擎量化精度另记 |
| Godot画面 | [Compatibility／M4 Pro实际GPU蒙皮](../../../assets/previews/characters/clockwork_bear/v003/godot_render_report.json)：三段各4个相位、960×800；不是主游戏、完整控制器或持续性能验收 |
| 用户确认 | 本体v002外形已认可；本次骨架／动作外观待评审 |

原可见身体仍保留v002的43条边界／39条多面边，代理封闭不等于原网格已全量重拓扑。已做实际形变检查，但不声称适合任意极端动作、布料或面部动画。手指可受骨驱动，不等于武器包握、扳机操作或双手IK已经完成。

## 缺口与交接

美术继续收本体动作反馈，后续再按精确GAT／单侧吊架版本制作持枪、预旋、开火交接与换弹；本批未装配武器或增加玩法。程序如接入，须登记源／副本SHA，配置三段循环、H10独立状态与骨过滤，再做同版游戏／命中／网络验证；不能照搬锋刃整套过滤或偏移。当前未写game。

## 本轮费用

| 步骤 | 任务ID | 实扣积分 |
| --- | --- | --- |
| 本体v002免费预检 | `7b99786e-92ec-4465-9fdc-4d02b95f0ad0` | 0 |
| 首稿v001免费预检 | `d8c2345f-5ca9-4a5b-9df0-7d78e67a13f7` | 0 |
| 本地骨架、权重、动作与检查 | 无Tripo绑定／动作任务 | 0 |
| **合计／查询后余额** | [费用台账](../../../assets/source/characters/clockwork_bear/v003/cost-ledger.json) | **0；余额395、冻结0** |

[最终SHA包清单](../../../assets/exports/characters/clockwork_bear/v003/package-manifest.json)。原本体生成50积分属于ART-084，本轮不重复计费；未采用的付费dry-run已标[禁止自动提交](../../../assets/source/characters/clockwork_bear/v003/rig-plan-status.json)。
