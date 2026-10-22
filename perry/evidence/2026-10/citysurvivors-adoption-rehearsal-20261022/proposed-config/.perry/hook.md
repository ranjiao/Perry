# CitySurvivors Perry 接入草案（未启用）

- Document root: perry
- Repo layout: single
- Document language: 中文
- Chat language: 中文
- Packs: [software-ops]
- Workflow conventions: M1/有界交付采用project；反馈分流采用queue；方案调查采用inquiry；资产评审采用pipeline叙述。没有mode/stage原生字段或调度器。

此文件是提议配置。原项目AGENTS及领域权限继续生效；软件包仅用于实际软件工作。没有美术/游戏专属pack。启用pack不增加收费、跨角色、发布或自动执行权限。
只沿已有权威专业源阅读，不搬移design/tech/art、资产manifest或runtime-manifest。原始文档生命周期不等于原生审批状态。
迁移选定范围外的CS/ART/DEV条目仍由原todo维护；选定条目切换后通过native查询维护唯一状态。确认前没有live写入。
任务负责角色从spec的明确声明读取；原生owner只是通用主体分类，不是三角色权限/过滤字段。卡片Loads供Agent读取，没有自动注入。
阶段/目标/KR和设计ADR本轮仅引用原源；未创建目标、指标、确认或自动授权。
发布策略未建立；Perry自身的版本/测试命令不适用于本游戏。实际游戏、资产、同机、LAN、设备、性能、真人验收由原规范要求，不由迁移自检替代。
自动派发和autopilot未启用；采用人工显式角色会话，不自动跨会话通信。
