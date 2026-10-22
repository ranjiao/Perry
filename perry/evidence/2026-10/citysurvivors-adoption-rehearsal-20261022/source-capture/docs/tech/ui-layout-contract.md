# UI文档与HUD布局数据接口

| 字段 | 内容 |
| --- | --- |
| 文档ID | tech.ui-layout-contract |
| 类型／负责人 | 数据接口／程序 |
| 用途／读者 | 协作接口与交付要求／美术Agent、程序、使用接口的策划 |
| 维护方式 | 持续维护 |
| 生命周期／修订／更新 | 当前／1.2／2026-10-22 |
| 适用范围 | 本机编辑器HTTP、citysurvivors-ui/version1～3与HUD schema_version1 |
| 依据／关联 | DEV-094～096；DEV-093／CS-078／DEV-091；[实现](hud-layout-editor.md)、[操作指南](guides/ui-editor.md) |

## 提供者、使用者与权威

程序提供编辑器、验证器及原子保存；美术Agent／人工提供布局草稿与图片，在自己可写目录制作。策划审阅信息结构与概念设计；程序另行接入选定布局、素材和实际状态／按钮行为。源／许可登记仍在[美术manifest](../../assets/manifest.md)，运行采用仍在[runtime-manifest](../../game/assets/runtime-manifest.json)，接口不建立新资产台账。

通用设计文档是独立草稿，不直接替换游戏菜单。HUD布局在用户选择“保存到游戏”时才写运行布局；F8回读沿[HUD组件](combat-hud.md)。两类格式不能互换，通用文档与HUD必须配置为不同文件。数据／UI变化不修改战斗资源、协议或房间阶段。

## 通用文档 v1与v2

| 对象 | 字段与含义 |
| --- | --- |
| 根 | format=`citysurvivors-ui`、version=1或2、name、reference（设计宽高）、assets、pages |
| page | id、name、background、elements；元素数组从底到顶绘制；v2另有groups，及可选reference覆盖本页设计宽高 |
| v2 group | id、name、visible、locked、members（同页元素ID数组）；2～200个成员，每页最多100组；不含独立几何／样式或父变换 |
| 共有节点 | id、name、type、x／y／width／height、anchorX／anchorY、opacity、visible／locked、fill／stroke／strokeWidth／radius |
| text | 另有text、fontSize、weight、align、valign、lineHeight；换行由文字框宽度决定，溢出按框裁切 |
| image | 另有asset、fit（contain／cover／stretch）、aspectLock |
| 形状 | type为rect／ellipse／line；rect的radius表示圆角 |
| 图片资源 | 稳定ID映射到{name,mime,width,height,data}；data是嵌入base64 data URL，仅PNG／JPEG／WebP；不接受外部URL或SVG |

完整样例读[模板](../../tools/playtest/hud_editor/studio-default.json)，结构限制实现以[验证器](../../tools/playtest/hud_editor/studio_document.py)为实际来源。当前边界：最多32页、每页200元素、64张图片；单图≤5MiB／边长8192px，整个请求≤16MiB。设计宽高320～4096，坐标／尺寸等字段的有限数值边界由同一验证器检查，新增字段需一起修改验证与消费端，不能只补说明。

参考坐标以像素计。设计宽高优先取page.reference，缺省取根reference。预览单位 `s=min(预览宽/设计宽,预览高/设计高)`；位置为 `x*s+anchorX*(预览宽-设计宽*s)`，纵轴同理，尺寸乘s。锚点0／0.5／1分配多余区域。更改reference不自动重排已有节点；新增模板按当前尺寸生成。

## 通用文档 v3：Frame与父子关系

v3沿用v2的根、图片、页与扁平组结构，elements新增type=frame；共有字段同rect，默认透明填充、无描边。节点增加可选parent，省略或null为页面根层，否则必须是同页Frame ID。Frame也可有parent，最多16层祖先；拒绝循环、悬空或非Frame父级。页内元素ID唯一，组成员仍只引用元素，且必须在同一Frame父级下；不支持组直接嵌套组。

| 规则 | v3含义 |
| --- | --- |
| 坐标／锚点 | 根层沿原参考像素和预览锚点；子项x／y相对父Frame左上角，尺寸仍是参考像素。子项锚点保留但不参与定位，前端禁用其修改；跟随顶层祖先的预览位移 |
| Frame尺寸 | 独立于内容；改宽高不缩放／重排子项，无自动布局、旋转、裁切或约束系统，内容允许超出容器 |
| 绘制 | 同父级按elements中的相对顺序绘制；Frame自身先画，再递归完整子树，构成连续绘制范围。逻辑组不改变原成员顺序 |
| 显示／锁定 | 有效显示为节点与全部祖先及其所属组的visible均为true；有效锁定为任一祖先／节点／所属组locked。任一后代锁定仍阻止整体误移动／删除；从树中选择对应父级解锁 |
| 透明度 | 节点opacity与祖先Frame的opacity相乘；复制单个子项离开祖先时合入继承透明度、显示和锁定，保持原有效表现 |
| 包入／切换父级 | 以页面设计参考坐标保留外部位置并换算局部坐标；已选祖先与后代去重，不重复移动。重挂父级后继承新父级的显示／锁定／透明度，不改子项自身开关 |
| 解除Frame | 删除容器本身，把直接子项提升到原父级，保持设计坐标并合入移除容器的显示／透明度；锁定状态需先解除。与删除Frame（连子树删除）不同 |
| 组与复制 | 原成组／解组继续可用；组可含同父级的Frame和普通元素。复制Frame带完整子树和组关系，新ID重映射parent／members；单个子项复制为根层独立对象 |

包入Frame及切换父级按设计尺寸保留几何；原稿若有不同顶层预览锚点，变成同一父级后会共用祖先位移，需重查其他预览比例。新增Frame是显式结构变更，可改变穿插图层的绘制范围；仅v1／v2加载或升级版本不重排原数组。没有以树显示替代旧稿实际绘制的静默迁移。

## 组、绘制、复制与图片语义

组ID在本页唯一，且不与本页元素ID重名；members只能引用本页元素，元素最多属于一个组，不接受组ID、重复或悬空成员。v1／v2元素在page.elements中保存绝对参考坐标；v3局部坐标及Frame绘制按上一节。组仍无独立变换、整体缩放或旋转。

v1／v2绘制以elements数组为唯一顺序，成组／解组不重排；groups／members顺序不另设绘制权威。组边界取全部成员外框并集（含隐藏成员）。有效可见为成员visible且组visible；有效锁定为成员locked或组locked。任一成员锁定则整体移动／排布／删除被阻止；解组及组剩余不足两个成员时，把父级显示／锁定合并到成员后解除。

多选移动、复制、删除、成组、解组、对齐／分布及图片替换，各作为一次文档变更进入撤销。对齐按当前预览内选择集的整体边界；等距按边界空隙，组算一个对象。分布跨度不足时允许负间距，不自动改变尺寸。

同文档粘贴生成新元素／组ID，重映射members，保留参考坐标、样式和所复制集合的相对绘制顺序，追加到目标页最上方；不同页面尺寸不自动重排。复制到工具内存，切页保留，导入／载入清空。若只复制一个组成员，则不保留该组，但继承的显示／锁定合入副本；复制两个以上成员可保留所复制子集的扁平组。

图片资源按MIME及完整data字节复用。替换仅更新所选元素asset，不原地修改旧资源；外框／锚点／透明度／fit／aspectLock保留，宽高比变化按原fit渲染。旧资源不自动回收，仍计入64张上限；导出PNG不携带编辑辅助线。解码失败或读取期间编辑／页面／选择变化时取消替换，保留当前稿。

## 格式演进与兼容

- v1原稿可加载、保存、导入、导出；只加载不改写文件或自动增加字段。仅在明确成组或设置单页reference时升级为v2，并为全部页补groups数组；原元素／资源不丢失，升级可随该步骤撤销到精确v1。
- v2每页必须有groups数组，空组列表有效；page.reference可省略，范围同根reference。解组后仍保留v2，不做隐式降级。不要只把version改回1；v1含groups或page.reference会被拒绝，避免静默忽略新结构。
- v3仅在新增／包入Frame或调整父级时显式启用，旧稿只加载不改写；为全部页补groups，保留原节点／图片／ID。升级与结构操作同一步撤销，可回到精确v1／v2。
- 新前端读取服务capabilities，再开放分组和Frame；旧Python服务无能力声明时只提供v1操作，分组被拒并提示启动新服务。刷新浏览器无法更新已运行的旧Python后端。
- 新服务对v2／v3写入与校验要求client_schema不低于文档版本，当前最大3；v2接受2或3，v3只接受3。旧客户端返回409；v1请求继续兼容。v1／v2不能夹带Frame或parent，不通过删字段降级绕过。外部改坏文件时GET也校验并拒绝，浏览器保留当前草稿。
- HUD schema_version=1保持原接口；通用version=2／3不是游戏HUD格式升级，也不代表新游戏页面已实现。

## HTTP与保存恢复

服务仅监听本机。所有POST用application/json；存在Origin时必须匹配本地站点。启动选项和默认保存位置只在[操作指南](guides/ui-editor.md)维护。

| 接口 | 请求／返回及副作用 |
| --- | --- |
| `GET /api/document/schema` | 返回能力、节点共有字段、Frame默认值、限额、坐标／绘制语义与安全读写流程；不读写稿件 |
| `GET /api/document` | 返回document、revision（保存字节SHA256）、path、capabilities（document_versions:[1,2,3]、flat_groups:true、frames:true、nested_frames:true、max_depth:16、client_schema:3）；读取不保存 |
| `POST /api/document/validate` | `{document:文档,client_schema:3}`；返回ok／pages／elements，校验结构与嵌入资源；不保存，不等于引擎渲染验收 |
| `POST /api/document/save` | `{document:文档,revision:读取版本,client_schema:3}`；校验及版本一致后原子保存，返回新revision／path；备份旧稿 |
| `GET /api/layout` | 返回HUD layout、revision、path、target（game／draft）、assets映射 |
| `POST /api/preview` | `{layout,width,height,scale,state,pad}`；调用实际Godot HUD headless，返回labels／resolved／model／commands等排版数据；不保存 |
| `POST /api/save` | `{layout,revision}`；HUD格式校验及版本一致后原子保存，返回新revision／path；备份旧稿 |

通用文档备份在tmp/ui-editor/backups，HUD备份在tmp/hud-editor/backups。过期写入409，非法结构400，跨域403，超限413；HUD引擎预览失败422或超时504。层级结构错误返回error、code和path（如pages[1].elements[2].parent）；其他旧校验可能只有通用code和空path。失败时保留页面草稿，不能把新编辑标成已保存。Agent重新保存前重读revision；有并行编辑先导出自己的稿，再合并，不强制覆盖。

## HUD格式与兼容

HUD由 [hud_layout.gd](../../game/core/hud_layout.gd) 定义schema_version=1，reference为参考尺寸，groups含anchor／offset／scale，elements含稳定id、group、rect、type及显示字段。rect为组内参考像素，bind读取只读视图模型，safe相对safe_frame底图归一化。HUD状态normal／low／reload／down／team／solo与设备符号只用于预览。

[运行布局](../../game/config/hud-layout.json)给出完整有效样例；保留游戏已有ID、绑定和素材ID。服务端HUD验证与引擎验证都需兼容，不能把可任意添加节点的通用文档直接交给HUD。字段／版本不兼容退回提供方，程序修验证／加载后另验，不能靠改版本数字宣称迁移成功。

## 验收与退回

提供方交可解析JSON、概念PNG、用途和采用范围；引用已有素材源，不把生成概念图当像素保真依据。使用方核对接口校验、浏览器恢复、编辑／导出、必要的游戏回读及各平台证据。图片损坏、缺字段、版本不兼容、越界或保存冲突须给原稿、错误与复现步骤退回，不删原稿绕过。

历史验证见[通用工具QA](../qa/2026-10-22-ui-studio-validation.md)与[HUD QA](../qa/2026-10-22-hud-editor-validation.md)。v3层级、Agent／人工使用检查见[本批QA](../qa/2026-10-22-ui-studio-frames-validation.md)。此前v2与批量操作的独立测试、旧稿／HUD回归及失败留证见[DEV-093验证](../qa/2026-10-22-ui-studio-batch-validation.md)。此前文档拆分的[整理报告](evidence/2026-10-22-documentation-review.md)保留当时格式与检查结论。
