# 锋刃移动持枪与换弹衔接（ART-076／CS-030）

| 字段 | 内容 |
| --- | --- |
| 文档ID | art.assets.fengren-motion-transition |
| 类型／负责人 | 资产交付／美术 |
| 用途／读者 | 协作接口与交付要求／程序取包；美术维护源与检查；策划审阅 |
| 维护方式 | 持续维护 |
| 生命周期／修订／更新 | 当前／1.0／2026-10-21 |
| 适用范围 | 锋刃v003＋配套步枪v004；DEV-066两项动作退回；不切换游戏版本 |
| 依据／关联 | [根todo CS-030](../../../todo.md)、[程序退回](../../qa/2026-10-20-layered-animation-validation.md#退回美术适配的具体问题)、[人物接口](../../tech/character-animation-handoff-v1.md)、[原v002](fengren-grip-v002.md) |

## 预览与用途

![同条件连续预览：左原v002，右人物v003＋步枪v004](../../../assets/previews/characters/fengren/v003/reload_run_comparison.webp)

实际最终GLB在隔离Godot工程中使用现行CharacterVisual／AnimationTree渲染，82帧、约30FPS、循环；左为原配套v002，右为新配套。两侧同相位跑步／换弹、混合0.08秒；不是当前M1实机画面。取景、光照相同，模型纹理未修。

![结束前后对照](../../../assets/previews/characters/fengren/v003/transition_comparison.png)

修复目标是换弹起止混合时左掌离开握点，以及换弹结束直接进入跑步时枪口跳变。新配套已交，外观／动作待用户评审；游戏版本尚未更新。

## ID、源与授权

登记ID为`character_fengren_v003`与`wpn_assault_rifle_01_v004`，完整来源／限制在[唯一manifest](../../../assets/manifest.md)。沿用原人物v002与配套步枪v002；无外部下载、付费生成或新许可结论。Tripo／Mixamo原来源限制继续有效。

唯一编辑源为[动作策略](../../../assets/source/characters/fengren/v003/animation_policy.json)＋[构建器](../../../tools/blender/build_fengren_transition_v003.py)＋[左臂烘焙器](../../../tools/blender/bake_fengren_contact_v003.py)，输入是冻结的原v002配套。两个blend仅为最终GLB读回的派生快照，不能当成第二编辑权威。

## 接口

- 原米制、−Z朝前、脚底原点、1.85米、41骨、10段人物动作保持。网格／UV／蒙皮／绑定矩阵／骨长／材质／图片／静态节点与挂点均与原v002一致，原GLB二进制数据完整保留，只追加动画数据。
- `weapon_r`仍挂`R_Hand`，位置`(0,.07,0)`、旋转`Ry(20°)*Rx(90°)`；武器`HandL`、`Muzzle`等原标记不改。原22根上身遮罩与19根下身／根骨划分保持。
- idle／walk／run／sprint／aim_idle共用原aim_idle首帧的上身准备姿势；Root／Hip／Pelvis／腿等原下身轨道逐字节保持。fire／hit／down／death完全不改。
- 人物`reload`与武器`reload_tactical`仍同播2秒片段；两端各0.2秒片段时间保持准备姿势，中间1.6秒同步重映射原换弹动作、弹匣／枪机和HandL目标。**不改变权威换弹时长**；1.8／1.17／2.5秒是测试控制器缩放的时长样例，不是新玩法值。
- 换弹按120FPS重采样，离线固定骨长求解并烘焙左上臂／前臂／手3根旋转轨道；没有运行时IK。武器其余idle／fire／draw／reload_empty四片段原样保持。
- 取舍：冲刺上身改为共享持枪准备，取消原举枪姿势；冲刺髋腿轨道与步态时钟保持。此取舍需动作审美评审。

## 导出版本

| 交付 | 唯一导出与追溯 |
| --- | --- |
| 人物v003 | [fengren.glb](../../../assets/exports/characters/fengren/v003/fengren.glb)／[provenance](../../../assets/exports/characters/fengren/v003/provenance.json)／[blend快照](../../../assets/source/characters/fengren/v003/fengren.blend) |
| 配套步枪v004 | [GLB](../../../assets/exports/weapons/wpn_assault_rifle_01/v004/wpn_assault_rifle_01.glb)／[interface](../../../assets/exports/weapons/wpn_assault_rifle_01/v004/interface.json)／[provenance](../../../assets/exports/weapons/wpn_assault_rifle_01/v004/provenance.json)／[blend快照](../../../assets/source/weapons/wpn_assault_rifle_01/v004/wpn_assault_rifle_01.blend) |
| 配套与最终SHA | [汇总检查](../../../assets/previews/characters/fengren/v003/validation_report.json)，含原输入／源策略／生成器与两件最终GLB的SHA256 |

步枪v004仅从**原人物配套步枪v002**派生；独立武器图鉴的v003枪口修正不在此包中。两条版本支线不可按数字自动合并。旧版均保留；人物v003与步枪v004须成对接入，不能混搭v002换弹时间线。

## 检查与接入

验证均绑定[复制输入与程序SHA](../../../assets/previews/characters/fengren/v003/review_inputs.json)；配置引用只在临时工程改为新配套，正式game未由本会话写入。

| 检查层 | 实际结果与证据 |
| --- | --- |
| 最终GLB结构／数据保护 | [汇总](../../../assets/previews/characters/fengren/v003/validation_report.json)：几何／rest／材质／图片／原二进制、570条下身通道、未改片段一致；[Blender实际重导入](../../../assets/previews/characters/fengren/v003/roundtrip_report.json)：人物10924三角／41骨／10动作，步枪996三角／4网格／5动作，无缺图 |
| 原版对照矩阵 | [48例／逐例指标](../../../assets/previews/characters/fengren/v003/transition_metrics.json)：两版本×idle／walk／run／sprint×3权威时长样例×混合0／0.08秒；原版最差掌心107.6毫米、动作边界枪口单帧639.4毫米（含冲刺） |
| 新配套24例 | 同矩阵60Hz：掌心代理最大1.247毫米；动作边界枪口单帧最大9.203毫米；下身层相对误差0。枪口值限定动作起止窗口，不表示换弹全程运动幅度 |
| 既有分层／Arena回归 | [逻辑406项](../../../assets/previews/characters/fengren/v003/runtime_logic.json)、[场景8项](../../../assets/previews/characters/fengren/v003/runtime_scene.json)通过；场景未报大于0.1米的动画枪口跳变 |
| 同机双进程ENet | [报告](../../../assets/previews/characters/fengren/v003/network_report.json)：延迟40毫秒／抖动15毫秒／丢包5%，普通／快速换弹、晚加入、倒地取消与只读动画通过；主／客最大接触偏差1.258／1.261毫米 |
| 视觉查看 | 实际查看最终对照板与近景，连续预览已导出；审美未获用户确认。掌心代理指标不等于手指包握或连续表面无穿插证明 |

沿用原2毫米接触门槛。早期采样方案的同机网络失败报告以`network_report_60fps_rejected.json`／`network_report_120fps_rejected.json`保留在同一证据目录，不覆盖成通过；当前最终配套增加离线左臂烘焙后通过。

## 缺口与交接

程序CS-031接入时成对复制两件最终GLB、更新人物／武器引用与运行manifest，并核对上表SHA；保留现有骨映射、挂点、分层遮罩与权威状态时长。0混合与0.08秒均有独立检查，配置取值由程序维护。完整重跑入口为[矩阵](../../../tools/blender/view_fengren_transition_v003.py)、[既有回归／图形](../../../tools/blender/verify_fengren_transition_v003.py)、[网络](../../../tools/blender/network_fengren_transition_v003.py)。

待接入后在真实M1检查移动／射击／换弹、ADS切换及俯仰、冲刺结束和倒地恢复；本矩阵为中性瞄准俯仰，不能关闭全部ADS问题。真实双设备LAN、Windows、目标设备持续性能、全身装备／手指穿插与真人动作验收未测。美术交付不表示游戏已修复，导演据本页更新跨角色状态。
