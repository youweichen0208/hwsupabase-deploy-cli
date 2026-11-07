# 华为云前端部署与 Supabase 接入 Skill

通过 AI agent 准备构建环境，创建、部署、更新、回退和维护 React/Vue 静态前端，并连接已有华为云 RDS Supabase。支持私有 OBS＋CDN、明确选择的 ECS＋EIP＋Nginx（宿主机或 Docker），以及保留或新建用户指定的其他云厂商/平台托管；Cloudflare Pages/Vercel 仅作为具体操作示例。新项目未指定框架时采用 React＋Vite＋TypeScript，也支持普通静态网站和已能静态导出的项目。

## 从这里开始

本仓库交付供 AI agent 使用的 skill，不是独立部署 CLI，也不包含客户应用。推送到 GitHub 只更新 skill 与文档，不会自动发布前端或创建云资源。

1. 安装或更新完整 skill 目录，随后在需要部署的前端项目中调用。
2. 选择托管路线，准备该路线所需认证、访问入口和已有 Supabase 信息。
3. 先执行只读预检；缺少工具、域名、权限或预算授权时先明确缺项。
4. 在已明确的授权范围内准备环境、构建及发布，完成真实访问、更新与回退验收。

首次云端测试请按 [云端测试指南](docs/cloud-testing.md) 操作；术语含义见 [GLOSSARY.md](GLOSSARY.md)，已完成的本地实测见 [环境验证记录](docs/environment-validation.md)。**当前尚无本项目的真实云端部署验收记录。**

## 部署选择与接入流程

![前端托管选择与 Supabase 接入流程：已有平台可保留；华为云有域名走 OBS/CDN，准备域名时先本地预览，明确选择 IP 访问时可用 ECS；也可选择其他云厂商并核实其访问入口。最终由浏览器调用已有 Supabase。](docs/deployment-flow.svg)

[查看完整流程图](docs/deployment-flow.svg) · [编辑文字版 SVG](docs/deployment-flow-editable.svg) · [Excalidraw 结构源文件](docs/deployment-flow.excalidraw)

三种部署场景横向并排，底部共用浏览器访问与 Supabase 接入链路。流程图采用 pastel-handdrawn-diagrams 风格：白底、柔和彩色节点、加粗的规整深色轮廓、直线箭头与手写字体；中文采用 HanziPen SC Bold 手写体，英文保留 Virgil 并合成加粗。展示版 SVG 的中文已转为轮廓，跨设备显示一致；文字可编辑版需本机安装 HanziPen SC Bold。Excalidraw 文件保留结构与标签，其字体回退可能与展示版不同。英文嵌入字体的来源与许可见 [字体说明](docs/diagram-fonts.txt)。

图例：**浅蓝**表示主要托管步骤，**浅橙**表示域名准备，**浅紫**表示其他平台选择，**浅绿**表示浏览器访问、Supabase 接入与验收。工作流已覆盖不等于已在真实云环境部署验收。

- 前端已在其他平台托管时，可以保留现有部署；尚未托管时，也可以选择其他云厂商及其托管服务，按实际能力使用自有域名或平台提供的可用入口。平台选择不限于 Vercel、Cloudflare，也不假设每家都提供免费默认域名。
- 选择公有华为云且已有可用域名时，默认使用私有 OBS＋CDN；准备办理域名时，先完成本地构建与预览，待证书及适用备案条件齐备后上线。
- 明确选择内部 OBS、提供实际 Endpoint 且授权访问范围时，使用 [内部 OBS 自定义域名流程](skills/huawei-supabase-frontend/references/obs-custom-domain.md)，保留独立配置，完成网站配置、产物权限、域名绑定及 GET/浏览器验收；不默认套用 DevKit 初始化或 CDN 刷新。
- 不准备域名且明确需要公网 IP 访问时，可选择 ECS＋EIP＋Nginx，需要承担服务器维护、带宽费用并处理 HTTPS。**缺少域名不会自动购买 ECS，OBS 桶也不能直接绑定 EIP。**
- 所有路线均由用户浏览器调用已有 Supabase 的 HTTPS API；公开 Key、CORS、登录回调与 RLS 需配置并验收。更新与回退沿用所选路线；未列明的第三方平台按官方文档核实能力，通过已有或新配置的 CI/官方工具发布，能力不足时交付明确缺项。

采用默认 OBS＋CDN 方案时，用户使用自己的域名访问，无需登录华为云；应用登录由 Supabase Auth 处理。SSR、服务端 API 和运行时秘密密钥需要另行明确后端依赖。

## 安装与使用

将 [skills/huawei-supabase-frontend](skills/huawei-supabase-frontend) 整个目录复制或链接到 agent 的 skills 目录，保留 `references` 和 `agents`。从旧版迁移时仅替换确实指向本仓库的安装链接，独立副本先比对再处理。旧 FunctionGraph 版本保留在 Git 历史中。

安装后确认 agent 能读取 `huawei-supabase-frontend`；复制安装需要同步更新完整目录，链接安装则跟随其指向的仓库版本。任务在实际应用项目中执行，部署记录也归属于该应用。

环境检查、构建环境准备、创建并部署、只接入 Supabase、更新、回退和服务维护共用项目环境记录：

```text
$huawei-supabase-frontend 准备北京四的前端部署环境，连接已有 Supabase，先检查域名和资源费用。
$huawei-supabase-frontend 创建 React 前端并部署到 OBS/CDN，接入已有 Supabase；没有域名时先完成本地预览。
$huawei-supabase-frontend 更新当前应用，复用已有环境并保留上一成功版本。
$huawei-supabase-frontend 回退到指定的已验证版本，刷新页面缓存并检查真实访问。
$huawei-supabase-frontend 不买域名，我明确选择已有 ECS 的公网 IP，用 Nginx 发布静态前端。
$huawei-supabase-frontend 前端已在其他平台，只接入已有华为云 Supabase，保留原托管与发布方式。
$huawei-supabase-frontend 用 Cloudflare Pages 默认域名部署这个项目，并准备更新和回退。
$huawei-supabase-frontend 用我指定的其他云厂商部署，先核实具体托管服务、访问入口、费用和回退能力。
```

华为云资源优先使用官方 KooCLI，OBS 文件默认用 KooCLI 内置 `hcloud obs`，兼容已有独立 obsutil，ECS 站点用 SSH/Nginx；第三方平台优先已有连接器、官方 CLI 或 CI。只接入任务已有可用 Supabase URL/公开 Key 时，不强制配置华为云 CLI。复用已有认证，首次凭证配置与登录通过官方交互完成；秘密不写入聊天、仓库或前端构建产物。

## 认证入口与工具分工

**首次接入用官方 DevKit 一次初始化，云资源操作用 KooCLI（`hcloud`），项目部署由 skill 协调。** 配置成功还需要通过目标服务只读查询验证认证与权限。

| 工具或信息 | 本项目中的作用 |
| --- | --- |
| DevKit 统一初始化 | 首次在终端输入一次永久 AK/SK，配置 KooCLI 与 OBS；不必安装整套插件 |
| KooCLI / profile | 保存或选择云认证上下文，查询及管理获授权的云资源 |
| AK/SK / SecurityToken | 云 API 认证；临时 AK/SK 还需 SecurityToken，不放进聊天或前端产物 |
| Region ID / Project ID | 前者确定目标区域；后者是账号下的项目，按 API 需要解析，不相互替代 |
| `hcloud obs` / 已有 obsutil | 上传、校验前端对象；统一初始化后仍单独核实 OBS 身份与桶权限 |
| SSH | 登录 ECS 操作系统，检查及管理站点软件、文件与服务；云 API 密钥不能替代 SSH 身份 |
| Node.js / 包管理器 | 按项目要求安装依赖和构建，仅在选定的构建环境运行，OBS 不安装 Node |
| Nginx / Docker Compose | ECS 静态文件服务与可选容器管理；Docker 不属于 OBS 托管前置条件 |
| Supabase URL / 公开 Key | 浏览器访问后端的连接参数；与云 AK/SK 分开，权限仍由业务策略与 RLS 控制 |

首次永久 AK/SK 接入且没有配置冲突时，skill 先检查工具，客户只需在自己的终端执行一次初始化。下面以 macOS/Linux 的北京四为例（区域按实际目标修改）：

```sh
HW_REGION=cn-north-4 npx --yes huaweicloud-devkit@1.1.13 auth init
```

按提示输入 AK、SK，永久凭证的 Security Token 留空。DevKit 需要现有 Node.js ≥22；这与前端项目的构建版本无关，skill 不会自动升级或切换本地 Node。KooCLI 缺失时由 skill 在工具准备授权内通过官方安装入口准备；无需再单独安装 obsutil。

已有认证可用时直接复用，不要求重配。**此版本初始化可能重建当前 KooCLI profile、覆盖默认 OBS 配置**，已有多账号或自定义配置先按 [认证指引](skills/huawei-supabase-frontend/references/authentication.md) 核实迁移范围并保护原配置。凭证只在客户终端输入及官方工具的用户目录存储，不进入聊天或仓库。临时凭证、SSO、ECS 委托及 AssumeRole 沿用专用流程，不强制切换认证方式。

初始化后分别检查云 API 和目标桶权限；“配置已写入”不等于“环境已准备”。固定版本的测试范围及兼容限制见 [认证验证记录](docs/auth-validation.md)。

配置完成后，只向 agent 提供 profile 名、目标区域、项目位置和所选路线，不提供密钥值。例如：

```text
$huawei-supabase-frontend 使用已配置的 profile <名称>，目标北京四，检查当前项目是否可部署到 <所选路线>，复用已有 Supabase <应用标识>。先只读预检并列出权限、工具、入口和费用缺项，不购买、不安装、不发布。
```

OBS/CDN 还需要域名、证书及相关资源权限；ECS 还需要 SSH 和必要系统权限；其他平台沿用其自身认证和发布渠道。只有既有前端及公开后端参数的接入任务，不必先新增华为云 CLI 认证。

## 构建环境与服务管理

先确定构建位置，再按项目的 Node.js、包管理器、锁文件和 CI 配置检查工具链。优先复用已有产物或 CI；本地构建使用现有兼容工具，版本不匹配时报告缺项，不自动下载、升级或切换本地 Node/包管理器。只有明确要求准备本地工具链时才修改本地环境。OBS 仅保存静态产物；ECS 默认用宿主机 Nginx，也可明确选择 Docker 构建和 Nginx 容器托管。普通更新沿用已验证版本，环境升级单独验证；检查任务只读，远端或容器工具在选定目标及授权范围内准备。

```text
$huawei-supabase-frontend 使用已有 CI 按项目版本和锁文件构建，再发布静态产物；不要修改本地 Node 或包管理器。
$huawei-supabase-frontend 使用 Docker 构建并在已有 ECS 上用 Nginx 容器发布静态前端，准备更新和回退。
$huawei-supabase-frontend 检查当前应用的构建环境、Nginx 或容器状态，先报告问题，不修改服务。
```

云资源用 KooCLI，ECS 内部软件与服务通过 SSH 管理。服务自启动和退出重启由系统服务或 Docker 策略承担，skill 按调用检查和维护；健康检查失败不等于 Docker 会自动重启。SSR/API 不属于本 skill 的静态发布范围。

## 首次上线条件

若采用 OBS＋CDN 路线且尚未准备可用域名，首次正式上线需先准备域名。OBS 默认域名可能强制下载网页，不能作为可靠的网页入口，见 [OBS 访问说明](https://support.huaweicloud.com/usermanual-obs/obs_03_0342.html)。缺少域名时交付本地预览、构建产物和上线清单。

中国大陆及全球 CDN 加速要求备案；首次通过华为云备案还有可备案资源条件，见 [备案条件](https://support.huaweicloud.com/icprb-icp/icp_01_0008.html)。注册域名不等于所有条件齐备；skill 不会因缺项自动购买服务器或切换地区。

前端侧以约 300 元/月为费用规划目标，按实际用量估算并设置适用告警；它不是账单硬上限。已有 Supabase 的实例与公网费用独立核算，不自动购买数据库。

## 指引

| 文件 | 内容 |
| --- | --- |
| [术语表](GLOSSARY.md) | 托管、身份、版本和完成状态的统一定义 |
| [云端测试](docs/cloud-testing.md) | 首次预检、发布、验收、回退、留证与清理 |
| [SKILL.md](skills/huawei-supabase-frontend/SKILL.md) | 任务入口、边界与工作流 |
| [前端构建](skills/huawei-supabase-frontend/references/frameworks.md) | 静态边界、版本资源和本地验证 |
| [构建环境](skills/huawei-supabase-frontend/references/build-environment.md) | Node/包管理器识别、隔离安装、Docker 构建与升级 |
| [Docker 静态托管](skills/huawei-supabase-frontend/references/docker-hosting.md) | Engine/Compose 准备、Nginx 容器、检查、发布与恢复 |
| [认证](skills/huawei-supabase-frontend/references/authentication.md) | 凭证复用与失败诊断 |
| [区域映射](skills/huawei-supabase-frontend/references/regions.md) | 中国站/国际站名称解析与服务能力核实 |
| [Supabase](skills/huawei-supabase-frontend/references/supabase.md) | 已有应用发现、公开 Key、HTTPS 与权限隔离 |
| [域名与托管](skills/huawei-supabase-frontend/references/hosting.md) | 私有 OBS、CDN、DNS、SPA 路由和费用 |
| [通用记录与验收](skills/huawei-supabase-frontend/references/deployment.md) | 路线标识、兼容旧记录、版本与验收 |
| [内部 OBS 自定义域名](skills/huawei-supabase-frontend/references/obs-custom-domain.md) | 明确选择的内部环境、独立 Endpoint、域名绑定、诊断与恢复 |
| [OBS 发布与回退](skills/huawei-supabase-frontend/references/obs-release.md) | 对象上传、入口切换、CDN 刷新与恢复 |
| [ECS 发布与回退](skills/huawei-supabase-frontend/references/ecs-hosting.md) | 资源复用/创建、EIP 绑定、Nginx、SSH 发布与恢复 |
| [其他平台](skills/huawei-supabase-frontend/references/external-hosting.md) | 保留或新建指定平台托管、通用发布与回退、Pages/Vercel 示例 |
| [官方资料](skills/huawei-supabase-frontend/references/sources.md) | 来源与核实限制 |

## 验证状态

Issue #1 修复增加 GET 最终响应与正文验收、内部 OBS 自定义域名流程，保持 schema_version=2。HEAD 不能证明无强制下载；旧记录保留，下一次部署/回退补验。模拟及 CLI 解析结果见 [GET 与自定义域名验证](docs/obs-validation.md)；未验证客户内部站点。

统一认证入口已按 DevKit 1.1.13 发布包核对，并完成无网络隔离测试、虚构凭证交互及 KooCLI 7.3.12 OBS 帮助验证；未执行真实云认证。详见 [认证验证记录](docs/auth-validation.md)。

此前补齐构建环境与 Docker 管理：skill 格式、内部链接和 shell 示例检查通过；本地 Node 构建与 Nginx/Compose 的 23 项检查通过，覆盖挂载、路由、更新、回退和配置失败恢复。另完成版本冲突、缺工具、只读检查、已有 CI 等场景推演。测试版本、文件共享限制及未执行范围见 [环境验证记录](docs/environment-validation.md)。

本仓库交付由 agent 执行的 skill 指引，不是独立部署程序，也不包含用户应用。命令的核对来源及未实测部分见官方资料；当前支持的路线均有准备、发布、更新和回退流程，缺少权限或平台能力时明确停止对应操作。

此前版本已执行本地检查：skill 格式、内部引用、shell/JSON 示例、UI 元数据和流程图渲染；在官方 Nginx 1.30.6 容器中通过 20 项测试，覆盖页面路由、负面路径、MIME/缓存、资源先上传、旧资源 URL、更新/回退和错误配置拒绝。独立前向推演覆盖无域名待选择、ECS 发布中断、外部平台无源码/权限、Vercel 发布与回退，并据此修正指引。

- **skill 已完成**：OBS/CDN、ECS/EIP、保留或新建其他云厂商托管的通用工作流（含 Pages/Vercel 示例）及 UI 元数据已同步；新增构建工具准备、Nginx/Docker 服务维护指引。
- **本地应用已验证**：临时测试样例已验证；尚未验证客户应用。
- **环境已准备**：未执行，本次未配置云资源。
- **线上验收通过**：未执行，待域名及环境就绪后验证 HTTPS、路由、登录、隔离、更新和回退。
