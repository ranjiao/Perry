# CBD通路收尾与Q2～Q4试验验证

| 字段 | 内容 |
| --- | --- |
| 文档ID | qa.cbd-pressure-validation |
| 类型／负责人 | 验证报告／程序 |
| 生命周期／修订／更新 | 当前／1.0／2026-10-21 |
| 适用范围 | CS-065程序试验候选；不代真人平衡／真实LAN／目标机验收 |
| 依据／关联 | 用户继续Q1→Q4的指令；[规则源](../design/m1-qianya-pressure.md)、[实现](../tech/cbd-pressure.md)、DEV-077～080 |

## 被测对象与环境

候选`source-20261021-cbd-q4`，协议13；[保存源码身份](cbd-pressure-followup/source-snapshot.json)、[有效配置与相邻档差异](cbd-pressure-followup/config-diff.json)。本轮开始时已有三处碰撞／移动修改，见[入场差异](cbd-pressure-followup/incoming-changes.json)，已保留，未接美术新素材。地图仍v005、CBD v001，原GLB／派生身份随快照登记。

macOS26.5.2／Apple M4 Pro，Godot4.6.3与4.7.2；图形用Compatibility。所有数据为实际引擎运行或明确标注的测试夹具；没有真人评价、真实两机LAN、Windows／物理手柄证据。旧[Q1首批QA](2026-10-21-cbd-path-recovery-validation.md)不回写，其两段超2秒停滞保留为修复输入。

## 通路步骤与实际结果

三门及花箱断口、公交两端、站棚，在实际同版地面／静态碰撞／1.3米移动半径下追逐经PlayerMotor移动的目标。夹具仅把敌人伤害设0，隔离移动；严格记录0.5米位置进展、合法队列、重寻路、最小间距及配置异常，不传送／删怪／缩尺寸。

- [Q1：1／5／8只共18组](cbd-pressure-followup/final-groups/q1.json)；[Q4：8／12／16／22只共24组](cbd-pressure-followup/final-groups/q4.json)。均按实际放入数量、非队列停滞、间距及阶段判定；原始停滞／队列与轨迹保留在JSON。
- 原两段停滞来自路点变化重置计时与动态预留无解时沿用旧终点。修为独立身体锚计时、重新规划到当前目标；22只复测又发现静态起点可达、动态连接被同伴挡住，增加连接段实际同伴间距检查。
- 有效队列须关联真实推进／可攻击领头者；推进时间戳只在身体离开0.5米锚时更新，隔墙近身不获队列豁免。队列等待仍走原碰撞／恢复检查；减算实验引入追移动目标停滞，已回退。
- 受控静态／同伴阻挡、网格恢复与无解有界报错：[4.6.3](cbd-pressure-followup/final-fast/recovery46.json)、[4.7.2](cbd-pressure-followup/final-fast/recovery47.json)，各38项。[本轮Q0五例负对照](cbd-pressure-followup/final-fast/recovery-q0-negative.json)仍停滞25秒，预期非零退出；原Q0证据另存不覆盖。

“超过2秒非队列停滞”从实际位置锚计算；真实攻击／推进队列期间不累计无故停滞，解除后重新观察。原始纯位置停留时长也保存，不把队列排除改写成所有敌人每两秒都移动。有限点位通过不等于整图穷举。

## 接近、攻击与动作

相同CBD20米直线，Q1／Q2／Q3各五轮；正常伤害、无保护，直接记录首次起手／HP变化，不用理论值冒充实测。

| 档位 | 首次起手 | 首次生效 | 每档重复 |
| --- | --- | --- | --- |
| Q1 | 5.23s | 6.07s | 5轮一致 |
| Q2 | 3.83s | 4.67s | 5轮一致 |
| Q3 | 3.77s | 4.60s | 5轮一致 |

[最终边界专项4.6.3](cbd-pressure-followup/final-fast/pressure46.json)／[4.7.2](cbd-pressure-followup/final-fast/pressure47.json)各49项：3／6只实际移动与伤害、最多2只同时前摇、实际效果≥0.6秒、锁向后绕背落空、49°命中／51°落空（100°扇区）、超2.2米落空、前摇后新增遮挡挡伤、冷却失距追逐、长步长不叠效果、重开清许可及私有数据不进快照。群体长观察仅测试HP提高到10000，明确不作正常生存难度结论。旧中间pressure文件包含夹具phase错误和修正过程，以此最终专项为准。

[实际主场景键鼠输入](cbd-pressure-followup/release/input-scene/scene.json)测试3／6只真实钳牙：鼠标消费弹药、R换弹、D横移、前摇朝向；只暂停入场调度，没有关闭身体碰撞。六只包围可能拦住横移并命中，不能把“输入已执行”写成保证无伤躲开。前期一次单渲染帧按键未覆盖物理步、首击被捕获保护吞掉，夹具已改为明确松开／重按并保持按键，原失败日志保留。

## 有限调度、恢复与正常资源

[Q1逻辑324项](cbd-pressure-followup/final-fast/logic-q1.json)、[Q4逻辑540项](cbd-pressure-followup/final-fast/logic-q4.json)分别枚举1～4人三波总量／上限、N+1批量、部分余量、隐藏／净距、实际间隔、阻塞暂停、无人行动停刷、恢复及自救额度。调度夹具直接清敌隔离请求守恒，不当正常战斗。另有[恢复专项15项](cbd-pressure-followup/final-fast/schedule-recovery.json)：实际连续批次、待发预告中倒地、停刷不消费余量、恢复完整1.5秒重预告与继续原批；Q4实际间隔由3秒配置约束，0.1秒采样存在步长量化。

按[汇总器](../../tools/analysis/summarize_cbd_pressure.py)整理[两枪Q1／Q4各三局原始数据](cbd-pressure-followup/candidate-combat/combat-runs.json)及[汇总](cbd-pressure-followup/combat-summary.json)：正常HP、弹匣／换弹与真实hitscan，自动瞄准脚本，获取新目标后0／0.1／0.2秒反应，不注入击杀或无敌。每秒采样在场／未到E／可交战／近战数，逐敌人保存出生→首次显形→E→接敌→攻击，未发生的后续时间为空。

在该全方向快速瞄准脚本下，两档均在敌人到E／近身前清除，Q4增加可交战量但没有构成脚本生命威胁。这既不证明真人觉得足够热闹，也不证明真人无法无伤；需CS-066接续。未到E与可交战可重叠，不能把“在途”全部当隐藏不可打的空等。

[实际主场景Q4](cbd-pressure-followup/candidate-main/scene.json)10项：落地、模型／物理／无限备弹HUD、开始隐藏批次、配置暂停及重开；[北向截图](cbd-pressure-followup/candidate-main/north.png)中的单只钳牙是渲染探针。已打开核对实际画面；截图FPS不当性能验收。

[最终回环ENet](cbd-pressure-followup/candidate-network/network.json)：房主／中途加入／掉线重连、身份／HP／弹药／自救额度、客户端无重开权限、房主重开同步。是真实同机多进程，不是真实LAN。旧模式[核心63项](cbd-pressure-followup/release/core.log)、[三波47项](cbd-pressure-followup/release/waves.log)保留回归。

## 22只负载与风险

四玩家状态，第三波由真实有限调度发入22只，保持实际移动、碰撞和动作；仅`enemy.damage=0`用于持续负载，不绕过生成合法性。60秒模拟，[最终候选独立本机样本](cbd-pressure-followup/load22-candidate.json)统计35秒后的751步：中位18.46ms、p95 88.60ms、最大157.78ms。此为headless模拟CPU时间，不含四客户端网络或图形，不代表目标机性能通过。该采样p95超过30Hz的33.3ms步长，DEV-080继续保留尾部耗时风险。

[插桩定位](cbd-pressure-followup/load22-profile.json)显示主要开销在重复碰撞试走和求路。最终只保留先排除被同伴占据的候选、再做静态网格检查；所有被接受的移动仍须同时通过动态／静态检查。中间试验load22／adaptive／query-order／queued均保留；其中adaptive周期复用与queued队列减算均未采用，后者的失败轨迹见release/groups-q1与groups-q4原始文件，不把不同运行样本当严格同负载性能基准。

图形退出仍出现既有两条纹理泄漏（每条349524字节）；部分无图形运行偶发ObjectDB退出告警，未定位根因。日志保留，不把进程返回0称为所有诊断干净。

## 重做与后续

```sh
python3 tools/analysis/build_cbd_presets.py --check
python3 tools/validation/check_cbd_pressure.py --groups --network --graphical --output tmp/cbd-pressure-new
# 独立执行负载，避免与其他验证同时采样
/Applications/Godot.app/Contents/MacOS/Godot --headless --path game --script tests/cbd_pressure_load.gd -- --report=res://../tmp/cbd-load-new.json
```

[检查索引](cbd-pressure-followup/validation.json)列各结果／源码绑定，旧文件不覆盖。新试验默认写tmp；旧cbd_scene固定输出通过[已登记复制夹具](cbd-pressure-followup/fixture-sources.json)隔离。本批同步程序todo／组件／采用入口；根CS状态由导演维护。真人两枪各三局与原话、真实LAN／设备、目标机长局和空间偏差评审未完成，CS-065不标全项关闭。
