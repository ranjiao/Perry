# Perry hook — 示例项目

## 高风险操作

<!-- Heading localized via the glossary; the match TOKENS below stay verbatim,
     because they are matched against real commands and file names.
     reference/i18n.md § The invariant layer. -->

- 生产部署 — `deploy`、`release`、`promote`、`production`、`prod`
- 凭据与密钥 — `.env`、`secrets`、`credentials`、`token`、`apikey`
- 破坏性数据操作 — `DROP TABLE`、`migrate --down`、`rm -rf`
- 改写 Git 历史 — `push --force`、删除 tag

## 项目专属

若项目为 **示例项目**：
- 路线图事实源：—
- 决策类型标签：Process | Architecture | Tooling
