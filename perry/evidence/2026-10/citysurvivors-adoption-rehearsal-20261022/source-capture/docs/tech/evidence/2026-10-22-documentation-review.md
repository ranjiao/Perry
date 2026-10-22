# CS-078 程序文档用途整理检查报告

| 字段 | 内容 |
| --- | --- |
| 文档ID | tech.evidence.cs078-review |
| 类型／负责人 | 整理检查报告／程序 |
| 用途／读者 | 验证与历史证据／程序、策划；CS-080复核者 |
| 维护方式 | 历史留证 |
| 生命周期／修订／更新 | 当前／1.0／2026-10-22 |
| 适用范围 | CS-078 U01～U06；程序分类、指南／实现分离、依赖与前后指纹 |
| 依据／关联 | [正式交接](../../production/documentation-handoff.md#3-cs-078-程序)、[用途规范](../../production/documentation-standard.md)、[目录规则](../../production/project-structure.md) |

## 对象、环境与写入边界

2026-10-22，程序执行CS-078；美术CS-079与全局CS状态由原角色维护。先读项目／角色入口、根todo、三份正式规范和模板，再检查共享脏树；没有重开CS-056历史验收、安装依赖、提交或改玩法。

环境为macOS arm64、Git／rg／Python标准库、已有Godot4.6.3和已有Node／Playwright／Chromium。文件基线记录HEAD与8983个入场仓库文件：[before.json](../../qa/documentation-cs078/before.json)。82份原程序Markdown实际字节保存到[original-docs.zip](../../qa/documentation-cs078/original-docs.zip)，逐项SHA核对后移除本轮新建的散装重复备份；没有依赖未跟踪文件可从Git恢复的假设。

本轮只改程序当前Markdown与新增整理证据。游戏源码、工具实现、协议、配置／运行manifest采用值、源资产、许可及既有原始测试数据均不搬删或重写。游戏／工具采用身份保持原入口，本轮没有发布新构建。机器结果见[checks.json](../../qa/documentation-cs078/checks.json)，实际写入／并行观察在其中分开。

## 分类与结论回填

- [程序入口](../README.md)按我的工作、长期专业资料、对象总表、协作接口、使用指南、验证／历史、项目治理组织；唯一构建仍在current-build，唯一组件总表仍是components。
- [测试场组件](../combat-lab.md)保留权威／生命周期／资源扩充，操作表与保存恢复统一进入[测试场指南](../guides/combat-lab.md)。
- [UI工具组件](../hud-layout-editor.md)保留实现／依赖／竞态；人工与Agent步骤进入[UI指南](../guides/ui-editor.md)，数据字段、版本／限制、HTTP及退回进入[UI接口](../ui-layout-contract.md)。原文件不是跳转页，稳定ID与有效实现说明保留。
- 当前专业源／接口／索引补用途、主要读者和维护方式；历史报告／旧清单／归档原文由[证据入口](README.md)与[分类清单](classification.md)登记，不为头信息重写历史。
- 无独立未定工作稿；本轮结论已进入上述正式源。重复操作／接口正文从原混合页提炼清除，独特实现／失败证据继续留存。没有以提案年龄删除有效预研。

完整逐文件用途、维护方式、原位原因、迁移前后路径及SHA见[处置清单](classification.md)及[migrations.json](../../qa/documentation-cs078/migrations.json)。本轮没有物理搬移文档，重组靠入口与内容分离；原路径消费者继续可用。

## 实际检查汇总

本轮清单共90份：36份当前维护源元信息齐全、53份历史类记录（52份入场原件字节保留＋本轮报告），另1份tools根说明权限例外原位保留。当前源从项目入口可达，文档ID无重复；本领域文件／锚点／图片检查无新增断链，也未发现既有断链。图表只核对文本／围栏，未把Mermaid渲染算作已测。

基线对比显示本轮程序改动为Markdown及新增证据，没有原始QA数据或非Markdown源文件改变。观察到美术侧并行文档修改，清单单列，不归本轮所有权、不回退；[after.json](../../qa/documentation-cs078/after.json)记录检查时保存状态，不能声称其他会话已停止编辑。

## U01～U06检查

| 案例 | 操作与判定边界 |
| --- | --- |
| U01 找文档 | 从总导航→程序首页→六类入口／共享治理；新指南、接口、分类表和检查报告须直接可达；结果见checks中的reachability |
| U02 唯一源 | components维护CMP分类；代码／配置决定实际行为；manifest维护素材台账。指南不再兼做API字段表，组件不再维护第二份操作表；抽样对应见checks |
| U03 生命周期 | 当前／历史逐份登记，旧证据字节校验；没有空任务工作稿，结论有正式去向，重复提炼段有后继；不改旧通过／失败／未测 |
| U04 使用者操作 | 下节区分真实headless操作、代码核对及未运行；未把软件图当GPU或真人验收 |
| U05 迁移安全 | 前后路径／SHA、当前与历史链接／图片／锚点、实时工具消费者、快照提及分别检查；旧断链与固定例外单列，不掩盖新增错误 |
| U06 辖区与收尾 | 对比本轮基线、明确写入集合与并行变化；程序todo登记DEV-092，根todo和美术正文未代改；待策划CS-080复核 |

以上结果以[机器检查](../../qa/documentation-cs078/checks.json)实际字段为准；本报告交付不等于用户确认。原报告中的历史“当前”通过证据索引解释，不强改原字节。

## U04 指南核对

| 范围 | 本轮实际操作与证据 |
| --- | --- |
| 入口／前置 | 三个启动器实际--help输出在[usage](../../qa/documentation-cs078/usage/start-game-help.txt)；对照已有可执行文件、路径与参数，没有安装依赖或启动图形窗口 |
| 统一测试场 | 原夹具headless[162项](../../qa/documentation-cs078/usage/lab/scene.json)通过：五分类、物品／E交互、展示播放／时间／缩放、同房确认与停止。图形capture按headless分支跳过 |
| 重置／保存报告 | 临时验证副本增加真实F6／F4输入，[165项](../../qa/documentation-cs078/usage/lab-guide/scene.json)通过，实际写出的[完整报告](../../qa/documentation-cs078/usage/lab-guide/interactive-report.json)含配置身份与测试状态；[验证副本](../../qa/documentation-cs078/usage/lab-guide.gd.txt)留证，不改原游戏测试脚本 |
| 通用UI指南 | [48项headless浏览器](../../qa/documentation-cs078/usage/ui-editor/checks.json)通过：页面／文字／图片／形状、拖拽／层级、JSON／PNG、真实磁盘保存、冲突／异步恢复和Agent写入人工读回；全部测试写入临时草稿 |
| HUD指南 | [headless浏览器结果](../../qa/documentation-cs078/usage/hud-editor/checks.json)记录原HUD拖拽／字体／状态、Godot布局读回、保存／导入冲突和PNG；不写用户运行配置 |

高级A／B预设保存位置与载入行为只按代码核对，本轮未新写用户已有预设。图形人工操作、物理手柄、真实LAN／Windows、目标机性能、概念生成、真人便利性和最终游戏GPU未重测；不由指南编写补验收。

## 固定消费者与未完成项

| 项目 | 处置、责任与影响 |
| --- | --- |
| 五份构建／release清单 | build_playtest.py与check_release.py仍读取原路径，coop-v04另与旧ZIP逐字节比较。五份原字节保留，DEV-070／CS-059待独立解除管线；不阻塞本轮新指南 |
| 历史报告／快照 | 旧JSON、原始日志／截图与归档正文不重写。快照内旧路径／SHA是原时点证据，不能把历史提及当作仍需执行的源，也不反向改成新路径 |
| 历史入链 | 本领域文件／旧锚点检查本轮无新增或既有断链；结果在[检查](../../qa/documentation-cs078/checks.json)列出。只读策划源已迁的后继在当前索引引用，不为修历史链接重写原证据或造共享跳转页；CS-080统一复核 |
| tools根说明 | tools/README.md原字节保留；正式角色写入列表只列工具子目录，本轮当前操作由程序指南／tests入口提供，旧工具固定输出说明按原位引用，不借整理扩大共享根说明写入 |
| 跨角色入口与全局状态 | 请策划沿现有程序入口复核分类、指南和例外，汇总CS-078／079；美术正文、共享规范及根todo由原维护者处理，本会话不跨会话派遣 |
| 未完成的实现／体验 | 既有玩法矩阵、动作接触、性能尖峰、缺件、平台／真人验收继续在程序todo维护，本报告不重复计状态或代关任务 |

需要后续修复的消费者及原位保留原因同时登记分类／依赖清单；纯历史路径引用不阻塞当前指南使用。检查通过只限报告列出的文档与headless操作范围，策划验收与用户确认保持待复核。
