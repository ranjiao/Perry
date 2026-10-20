# Perry hook — SkyTonight

## High-stakes operations

- 生产部署与发布：`deploy`, `deploys`, `deploying`, `release`, `releases`, `promote`, `production`, `prod`
- 凭据与密钥：`.env`, `secret`, `secrets`, `credentials`, `token`, `tokens`, `apikey`, `api_key`, `id_rsa`
- 云基础设施：`terraform`, `helm`, `k8s`, `infra/`, `iam`
- 资金及付费服务：`cost ceiling`, `paid API`, `billing`, `invoice`, `payment`, `refund`, `pricing`
- 破坏性数据操作：`DROP TABLE`, `migrate --down`, `rm -rf`, `rm -fr`, `bulk delete`, `restore-over`
- 代表用户发送或发布：`publish`, `publishes`, `publishing`, `published`, `send`, `sends`, `sending`, `sent`, `email`, `slack`, `post`, `posts`, `posting`, `client`, `filing`, `submit`, `submits`, `submitting`
- 重写 Git 历史：`push --force`, `rebase`, `tag deletion`

## Project specifics

- 产品与设计文档放在 doc/；Perry 状态位于 doc/perry/；不建立 iterations/。
- 正式开发需等待设计与体验确认；低保真原型不是正式实现。
- 亲子共用单界面，核心教学与望远镜品牌解耦。
- 用户不承担天文或技术专业决策，Agent 应提出可评估方案。
- 不自动派发任务或启动 autopilot；本次仅初始化。
- 默认高风险清单已由用户于 2026-09-16 明确确认：保留默认规则。自动派发仍需单独的任务执行指令。
