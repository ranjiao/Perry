# Perry Agent 文档与当前架构对齐检查

日期：2026-10-20。结论：检查前并未完全对齐；本次扫描 142 份当前源码文档和模板，修正其中 54 份。确认的失效接口、矛盾指令和过时状态说明已修正。此次结果是实现会话的文档核查，不是独立 V4 或新的人类 V5 验收。

## 范围与依据

覆盖根入口 AGENTS/SKILL/README/INSTALL/ARCHITECTURE，以及 goals、work、decide、reference、modes、packs、templates、kernel、tools、tests、release 中的当前 Markdown 文档。逐文件目录见 [coverage.csv](coverage.csv)，完整前后内容哈希见 [inventory-before.json](inventory-before.json) 和 [inventory-after.json](inventory-after.json)。每份文档均经过清单和引用/旧接口扫描；语义核查重点是路由、命令、原生字段、写入归属、安全策略、验收、模板与工作流程。扫描不等于对所有自然语言语义的独立认证。

依据当前根架构、DESIGN-023 及已接受修订、ADR-028、真实切换最终记录、`bin/perry describe`、当前原生进程模板和辅助工具实现。当前 surface 为 1.1，10 个命令组、17 个命令；进程模板有 9 种 item 类型。机器事实由原生 items/events 与 SQLite 承载，Agent 负责解释、规划和受授权的叙事文档维护。安装位置 `/Users/bytedance/.codex/skills/Perry` 是本源码仓库的符号链接，读取同一份文档。

冻结的 `release/retirement/` 清单、旧阶段记录、真实项目历史和迁移收据不按当前操作指令重写。独立 scaffold 的 STATE/DECISIONS 等文件有自身用途，不因名称类似旧寄存器而删除。`work/reference/kernel.md` 保留兼容跳转，共享契约以 `reference/kernel.md` 为准。

## 发现与修正

| 问题 | 已完成的修正 |
| --- | --- |
| 根路由仍列 journal/cadence、旧写入归属 | 统一为原生 items/events、各工作线职责和按需读取 |
| 模板仍调用旧 CLI、引用不存在的路由 | 更新 evidence/handoff/weekly 等模板，移除失效路径和命令 |
| 文档虚构原生字段或聚合能力 | 风险使用 concern/reason；区分直接子项指标和未实现的递归/阶段汇总 |
| 已接受的切换或修订仍写“待批准” | 对齐实际 surface 1.1、正式切换和 R0096；保留冻结提案清单原始标签 |
| 角色模板还要求退役的封闭语法 | 保留 May touch/Must escalate；Context/Loads 可选，不声称自动注入或旧 lint |
| 新项目 bootstrap 和 hook 归属不清 | 根入口建立 native store 和模板；偏好放项目 hook，各工作线按需建立叙事文档 |
| 迁移说明暗示 helper 直接解析旧 Markdown/JSONL | 明确实际接受经过审查、由 SHA256 固定的迁移计划，准备过程与正式导入分开 |
| 派发文档仍使用已删除的测试 tier/检查器 | 对齐当前 full/slow 和现有审查工具，不声称不存在的自动检查 |
| scratch 路径只按仓库名，多个工作树可能冲突 | 在仓库名桶内每次运行分配独立 mktemp 目录，并传递实际绝对路径 |
| digest/index/runbook 暗示后台自动维护或年龄淘汰 | 明确由 Agent 在授权范围维护；缺失信息标未知，不因未引用或旧 mtime 自动归档 |
| 软件 pack 混淆架构建议与变更授权 | 对齐用户拥有的硬约束、实际 review 日期、模块文档和可执行检查边界 |
| host 能力、原生存储前置条件说明不准 | 根据当前会话能力选交互；明确 root anchor 与非 Git 默认存储位置 |

仅本次 54 份文档的前后差异见 [audit-only.patch](audit-only.patch)，与之前未提交的清理工作分开记录。未改内核实现、进程声明、发布版本或项目任务状态。

## 验证

- 完整 `bash tests/run` 通过：288 项内核测试（其中 1 项环境相关跳过），182 项辅助工具测试。[原始日志](full-tests.log)。完整测试后只又修正一处历史时态说明，随后重跑下述文档与隔离验证。
- 142 个本地 Markdown 文件引用检查无失效目标。此检查不验证远端链接或所有标题锚点。
- 隔离 store 实际执行文档中的 create/query 及完整分页示例；带 evidence 的 Agent V5 完成请求被拒绝，store seq 不变。[原生收据](native-example-receipts.json)
- 实例化实际角色模板：省略可选 Context/Loads 可通过；缺少必需安全标题会拒绝。[角色收据](role-example.json)
- 实际执行 scratch 配方两次，得到两个不同且位于仓库外的目录。
- 原有项目状态、历史、内核源代码、进程模板及发布记录等 2,327 个受保护文件的 SHA256 不变。完整测试也确认 live store 仍为 seq 1895。[汇总](verification.json)
- 退役来源审计通过：610 行清单、365 个来源文件，无错误。该工具保留历史 pending/proposal 状态，只证明来源/哈希/路径，不替代实际用户接受记录。[审计摘要](retirement-summary.json)
- `git diff --check` 通过。

## 边界

没有修改 live store、补写人类同意、分配版本、提交或发布；保留此前所有未提交工作。本次没有独立复核员，未自授 V4/V5。新项目创建、真实迁移和各宿主交互没有逐场景重演；它们不能从文档扫描或单元测试推定为已验收。检查脚本保留为 [validation-source.py](validation-source.py)，它记录本机本次隔离核查过程，运行时需要原 scratch 清单与指针，不是新增产品工具。
