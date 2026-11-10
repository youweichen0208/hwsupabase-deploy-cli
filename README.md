# rds-supabase-frontend

供 AI agent 在华为云 OBS 上创建、部署、更新和回退静态前端，用自有域名提供访问入口，接入已有华为云 RDS Supabase，并准备所需构建环境。沿用已有框架，新项目未指定时采用 React＋Vite＋TypeScript。

本仓库交付 skill 和配套文档，不包含客户应用或独立部署 CLI。推送仓库不会自动创建云资源或发布前端。SSR、服务端 API 和数据库采购不属于本 skill 的工作范围。

## 安装与使用

原 skill 名为 `huawei-supabase-frontend`。更新安装时将旧 skill 目录替换为 `rds-supabase-frontend`，避免两个副本同时被发现；现有应用的 `.hwsupabase/` 发布记录目录继续沿用，无需迁移。


将 [skills/rds-supabase-frontend](skills/rds-supabase-frontend) **整个目录**复制或链接到 agent 的 skills 目录，保留 `SKILL.md`、`references` 和 `agents`。复制安装时同步更新完整目录；链接安装跟随其指向的仓库版本。更新已有安装前核实链接目标，独立副本先比对。

安装后确认 agent 能读取 `rds-supabase-frontend`，然后在实际前端项目中调用。环境与发布记录归属于该应用。先完成只读预检，再按任务或项目的授权、资源清单及预算准备环境和发布。

```text
$rds-supabase-frontend 检查当前项目的部署条件，复用已有 Supabase；先只读核实工具、权限、入口和费用，列出缺项。
$rds-supabase-frontend 创建 React 前端、部署到 OBS 并加上 www.<我的域名> 入口；探测入口可用后给我链接，失败时说明原因。
$rds-supabase-frontend 当前前端已在 OBS，只接入已有华为云 Supabase，保留现有域名和发布方式。
$rds-supabase-frontend 更新当前应用，复用已有环境并保留上一成功版本；失败时恢复原产物并验收。
```

首次执行可按 [云端测试指南](docs/cloud-testing.md) 准备输入、发布候选并验证回退。云认证按 [认证指引](skills/rds-supabase-frontend/references/authentication.md) 复用或初始化；向 agent 提供 profile、区域和项目位置，凭证只在官方终端交互中输入。仅使用已有 Supabase URL/公开 Key 接入后端时，无需为此新增华为云 CLI 认证。

## 部署架构与接入流程

![OBS 静态前端架构：构建产物上传公开读桶，自有域名直连桶或经 CDN 回源，浏览器独立调用 Supabase API](docs/deployment-flow.svg)

前端托管有两条路线，按环境显式选择：`obs-domain`（默认，入口域名直连 OBS 桶）与 `obs-cdn`（入口域名经 CDN 回源同一个公开桶）。桶对匿名读开放，前端产物本来就是公开内容；写权限与列举权限不开放。需要路径级改写、缺失资源返回 4xx 或加速层缓存时选 `obs-cdn`，其余默认直连。路线差异见 [域名与托管](skills/rds-supabase-frontend/references/hosting.md)。

入口域名由用户提供，agent 只在其已具备上线条件的根域名下派生 `www.<根域>`，不代注册域名、不代实名、不代备案。登录域名管理、绑定域名、写 DNS 与补装证书的顺序，以及创建后对入口根路径做的一次实际探测（状态码、HTML、非附件、版本标记、失败原因归类）见 [入口域名、证书与入口探测](skills/rds-supabase-frontend/references/domain-provisioning.md)。缺域名或备案未完成时先交付构建产物与预览，不报告公网完成。

源码在已有 CI、本地或构建容器生成静态产物，通过 `hcloud obs` 发布；CI 负责构建，不是前端托管服务。更新和回退保留原产物、切换入口；`obs-cdn` 还需刷新适用缓存。随后用真实入口验收。构建位置与工具链见 [构建环境](skills/rds-supabase-frontend/references/build-environment.md)。

浏览器独立调用已有华为云 RDS Supabase 的 HTTPS API，使用实际已启用的 Auth、Data、Storage 能力；API 不经过 OBS。应用用户无需华为云账号。HTTP 入口下非安全上下文缺少 `crypto.subtle` 等能力，Supabase 的 PKCE 登录可能不可用，补证书后需复验。费用按当前任务或项目预算核实，已有后端费用单独核算。

## 指引

| 文件 | 内容 |
| --- | --- |
| [SKILL.md](skills/rds-supabase-frontend/SKILL.md) | OBS 部署与接入工作流 |
| [云端测试](docs/cloud-testing.md) | 首次预检、发布、回退与收尾 |
| [前端构建](skills/rds-supabase-frontend/references/frameworks.md) | 静态边界与产物检查 |
| [构建环境](skills/rds-supabase-frontend/references/build-environment.md) | 构建位置、工具链准备及升级 |
| [认证](skills/rds-supabase-frontend/references/authentication.md) | 凭证复用、初始化与失败诊断 |
| [区域映射](skills/rds-supabase-frontend/references/regions.md) | 区域名称解析与服务能力核实 |
| [Supabase](skills/rds-supabase-frontend/references/supabase.md) | 应用发现、公开连接参数与权限隔离 |
| [域名与托管](skills/rds-supabase-frontend/references/hosting.md) | 两条托管路线、公开读桶、路由边界及费用 |
| [入口域名与探测](skills/rds-supabase-frontend/references/domain-provisioning.md) | 域名派生、绑定、DNS、证书与失败原因枚举 |
| [通用记录与验收](skills/rds-supabase-frontend/references/deployment.md) | 按路线的验收与回退标准 |
| [发布记录契约](skills/rds-supabase-frontend/references/record-contract.md) | 固定字段、状态不变量及 JSON 示例 |
| [OBS 发布与回退](skills/rds-supabase-frontend/references/obs-release.md) | 对象发布、入口切换及恢复 |
| [术语表](GLOSSARY.md) | 托管路线、稳定入口、入口探测等术语 |
| [决策记录](docs/adr) | 不代注册域名、公开读桶与双路线 |

本仓库当前不含任何云端验证记录；`tests/` 下的脚本只校验文档结构与记录契约，不接触真实账号。
