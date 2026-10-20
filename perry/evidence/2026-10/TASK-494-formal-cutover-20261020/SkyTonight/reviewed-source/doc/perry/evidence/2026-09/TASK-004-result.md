# TASK-004 — 制作并走查低保真探索原型

日期：2026-09-16；执行者：Codex。下文为原型交付时技术走查记录；后续用户验收范围以 Perry 关闭事件及当日日志的 V5 记录为准。

## 产物

- `doc/assets/prototype/index.html`、`style.css`、`app.js`：零构建步骤的本地交互样段。
- `doc/assets/prototype/README.md`：运行和验证方式。
- `doc/product.md`：四路径交互、导航候选和当前限制。
- `doc/assets/prototype/verify.cjs`：Playwright 自动走查。

原型使用原创 SVG 示意与平面阴影关系互动，所有画面明确标注模拟；未使用真实参考照片，没有设备连接、天气计算、图像识别、正式 3D 引擎或对外部署。未设置付费服务或安装产品依赖。现有目录中的其他任务修改未撤回或提交。

## 固定四路径的技术检查

| 路径 | 检查结果 | 证据 |
| --- | --- | --- |
| 首次探索 | 通过 | 准备→现成示意→原猜想→拖动光源→实际原理说明→相反条件预测；不依赖家长选图或讲解 |
| 再次继续 | 通过 | 刷新后首页显示原预测，新示意并排比较；最终保留最初猜想与比较选择 |
| 阴天替代 | 通过 | 初次阴天转内置示意，再次阴天转模型；不会标记真实观测已完成 |
| 中断恢复 | 通过 | 光源角度、当前步骤与选择保存；包括已留下预测后暂停模型操作的情况 |

额外检查：390px 窄屏无横向溢出；1200px 与390px截图人工查看，文字与控件可读；无浏览器脚本异常。发现并修复浏览器全局名称冲突与“暂停后错误跳到验证页”问题，最终重跑全部路径通过。

## 命令与回执

项目根目录启动服务：

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory doc/assets/prototype
```

本机工作环境的复现命令：

```sh
NODE_PATH=/Users/bytedance/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules node doc/assets/prototype/verify.cjs
node --check doc/assets/prototype/app.js
git diff --check
/Users/bytedance/proj/Perry/bin/perry-lint --root .
```

最终浏览器输出：`PASS: four journeys, persistence, mobile layout, no page errors`。
[自动检查回执](TASK-004-verification.json) · [桌面截图](TASK-004-desktop.png) · [窄屏截图](TASK-004-mobile.png)。语法、diff 与 Perry lint 通过。未改正式应用代码，不运行其他仓库的测试套件。

## 交付时待验收事项（历史）

- 用户不预读教学文档走查首次与再次继续：待用户实际体验与反馈，不用技术检查代替。
- 根据反馈调整三个导航入口：待反馈，尚未定稿。
- V5 用户签收：未取得；本记录只证明原型和技术走查存在。

可评估问题：亲子能否只凭屏幕明白下一步；解释是否够用；再次回来是否能接上上次问题。用户已阅读过设计文档，因此本轮实际反馈应注明这一背景，不能声称完成严格的首次无背景测试；未来未读文档家庭的补充体验为可选，不因此制造新必修外部验证。

## 体验限制

这是约 5–8 分钟的缩短样段（估计，非实测），非 55～80 分钟完整课程；科学生成内容沿用已核对的光照与阴影概念。示意画面不应被用作真实地貌证据，正式课程参考图选材仍需制作。

朗读使用浏览器能力，可能因本机语音支持而失败；文字解释完整保留，未声称语音效果已人工验收。记录限当前浏览器，存储受限会提示失败；未实现云同步。原型页面已请求在 Codex 浏览器面板打开，工具返回 queued。

## 后续反馈处理

2026-09-16 用户明确本任务通过，认可发现、操作、验证链路；视觉品质不获认可。反馈已写入 doc/product.md，前端美学和减少文本、加强可视化的要求已同步 doc/visual.md 与 TASK-005-spec.md。导航、其他尺度场景的泛化性和真实学习效果不在本次认可范围内。具体签收由 perry-task done 记录，不在此重复维护签名。
