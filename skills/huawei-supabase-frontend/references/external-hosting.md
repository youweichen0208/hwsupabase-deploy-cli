# 保留其他平台托管与平台默认域名

在前端已托管于其他平台，或用户选择 Cloudflare Pages/Vercel 默认域名时读取。前端可在其他云、Supabase 仍在华为云；无需迁移前端或为它采购 OBS/ECS。公共记录与验收见 [发布与验收](deployment.md)，后端配置见 [Supabase](supabase.md)。

## 保留已有部署

1. 读取源码、锁文件、部署配置、现有 CI 及非敏感项目绑定（如 `.vercel/project.json`、Wrangler 配置），查询实际账号/团队、项目 ID、生产分支、稳定地址、当前 deployment、构建脚本/目录及环境变量作用域。域名只能作为发现线索，不能据此猜测发布权限或项目归属。
2. 已有发布机制优先复用：Git 集成就沿用现有构建/生产分支；已有连接器或 CLI 就沿用其实际能力。读取当前配置，保留域名、自定义 API、重写规则和其他环境变量；不创建同名替代项目、不自动迁移平台。
3. “只接入 Supabase”先改客户端和必要的公开构建变量，按用户现有发布授权构建/发布。只有 URL、没有源码或发布权限时，完成访问与 API 可达性检查，列出需要的源码/发布渠道；不能声称给线上页面注入成功，也不要求先开华为云 CLI。
4. 将新的精确 origin/回调加入现有后端配置并保留其他环境。预览与生产分别使用适用的公开变量，变更构建变量后重新构建。需要临时预览登录时仅允许实际测试地址，不把整个 `*.vercel.app` 或 `*.pages.dev` 加入回调白名单。
5. 使用当前平台官方查询和发布机制执行更新，记录实际返回的 deployment ID/URL、构建结果和生产别名。先预览验证，再发布/推广到稳定入口；生产与预览环境不同则分别构建和验收，不能直接推广携带预览后端参数的产物。
6. 回退优先平台原生部署回退/别名恢复；先核实目标仍保留且曾验收通过。原生回退不可用时，使用归档的原产物通过既有发布机制重新发布并记录新 ID；不能仅检出旧提交重建就宣称恢复原产物。无法取得原产物或能力不支持时报告缺项，不自动升级套餐或切换平台。

对于此文未列明的平台，沿用其已有 CI/官方工具完成上述同一流程，执行前查当前官方部署、配置、路由和回退文档；没有可验证的发布能力时只交付本地变更与明确人工操作步骤，不假装已支持任意平台自动部署。

## 新建平台与账号选择

先复用已有账号和偏好；两者都没有时询问选择 Cloudflare Pages 或 Vercel，不自动注册账号或开付费计划。首次登录、组织邀请和 MFA 由用户完成。核实账号/团队归属、用途与套餐限制（包括商业使用）、区域可达性、构建配额、流量/请求、部署保留和回退能力；默认域名无需自购不等于所有使用免费。费用及用量告警按平台能力和已有授权设置。

所有 CLI 先检查本地版本/帮助；项目已有版本则复用，缺失时使用官方安装方式并记录版本，不把示例命令隐含下载的最新版当作已验证依赖。优先连接器能力，其次 CLI；网页登录未完成时继续本地构建，不索取聊天中的 token。发布仅上传扫描过的产物或明确需云端构建的源码，凭证/配置备份不随上传。

## Cloudflare Pages：静态 Direct Upload

已有 Git 集成项目继续沿用 Git 发布；新项目在用户选择此平台、无既有 CI 偏好时采用 Direct Upload。创建前说明 Direct Upload 与 Git 集成的切换限制，若用户需要 Git 自动发布则从一开始选择 Git 集成，不偷偷换模式或创建第二个项目。

操作链：登录并核实账号 → `wrangler pages project list` 查已有项目 → 缺失且授权后 `wrangler pages project create` → 本地构建 → 预览部署 → 查询/验收 → 发布生产分支。先核对这些命令的 `--help`。示例变量均为查询取得的项目、实际构建目录与用户选定分支；明确保证预览分支不等于生产分支：

```sh
wrangler pages deploy "$FRONTEND_OUTPUT" \
  --project-name="$FRONTEND_PROJECT" --branch="$FRONTEND_PREVIEW_BRANCH"
```

查 `wrangler pages deployment list` 的当前参数，保存实际 deployment ID/URL；从项目实际结果读取稳定 `pages.dev` 地址，不自行拼接。没有稳定入口时先完成项目创建或无登录预览，取得地址后配置 Supabase 回调、重新构建；预览参数与生产参数分开。验收候选后，用相同命令、**经过核实的生产分支**和生产构建产物发布；查询确认稳定地址已切换，再做生产验收。

路由：构建产物根目录保留实际错误内容的 `404.html`，避免 Pages 无该文件时的默认 SPA 全路径回退。将 `_redirects` 放入框架静态复制目录并验证其进入产物；仅对真实页面做 200 内部改写，不配置 `/* /index.html 200`。示例需按实际路由改写：

```text
/login /index.html 200
/auth/callback /index.html 200
```

Pages `_redirects` 的 `:id` 会匹配 `missing.js`，不能限制为业务 ID 格式；顶层 404.html 不能抵消已匹配的重写。因此动态路由不能直接套用 `/projects/:id`：可枚举的页面使用精确路径，需要按 ID 格式匹配而规则表达不了时，报告阻碍或复用已有支持该匹配的路由机制，不加宽泛重写或暗加 Pages Functions。动态路由验收同时检查有效的 `/projects/<id>` 与应返回 4xx 的 `/projects/missing.js`。保留/核实已有 Functions 和重定向优先级，它们可能改变静态规则。根路径由 index.html 提供；缺失资源与未知 API 必须返回 4xx，不能仅看 SPA 页面能打开。

缓存沿用 Pages 部署失效机制；必要时通过 `_headers` 设置入口重新验证、不可变资源长期缓存。检查实际响应，不叠加会掩盖发布的全域缓存规则。每次发布产物应包含保留期内旧页面依赖的不可变资源，或使用已确认可用的部署固定资源 URL；不能假设稳定地址切换后还能取得旧资源。

回退使用 Pages 控制台或已连接的官方 API 的 Rollback 能力，目标须为可回退的已成功生产部署；预览部署不是回退目标。Wrangler 缺少对应操作时明确改用控制台/API，不杜撰 CLI。回退后查询当前生产 deployment、稳定地址、页面和旧资源；失败时保留 ID，按通用流程报告实际状态。

依据：[Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/)、[默认 SPA/404](https://developers.cloudflare.com/pages/configuration/serving-pages/)、[重写规则](https://developers.cloudflare.com/pages/configuration/redirects/)、[回退](https://developers.cloudflare.com/pages/configuration/rollbacks/)。

## Vercel：已有项目或默认域名

读取已有项目绑定，核实团队和项目；没有绑定时才执行官方 `vercel link` 交互，避免把当前目录发布到错误项目。采用 Vercel 自带项目默认域名，不自行购买域名或修改 DNS。通过官方 CLI/连接器读取实际生产地址、部署保护及访问权限；需要公众访问的站点若被部署保护限制，说明原因，只在授权范围内修改。

保留 Git 集成的既有发布方式。CLI 项目先核实 `vercel pull`、`vercel build`、`vercel deploy`、`vercel promote`、`vercel rollback` 的帮助及套餐能力；拉取配置可能写入秘密文件，因此 `.vercel/` 排除 Git；其中凭证、拉取的环境文件、缓存及项目元数据不能复制到公开产物或产物归档。`.vercel/output` 是例外：单独扫描其静态输出/构建配置，确认无运行时秘密和越权服务端内容后，可作为 prebuilt 产物私下归档用于恢复，不能把整个 `.vercel/` 上传。

有预览环境时先拉取该环境配置，构建并部署预览，验证真实页面/回调。准备生产候选时使用生产配置重新构建，以下是已链接项目的命令形态，执行前核对当前版本的选项支持：

```sh
vercel pull --environment=production
vercel build --prod
vercel deploy --prebuilt --prod --skip-domain
```

`--prebuilt` 指 `.vercel/output` 的 Vercel Build Output，不是任意 dist 目录。`--skip-domain` 用于暂不分配生产域名；保存实际候选 URL/ID，查询构建成功、检查产物指向预期后端，再执行推广：

```sh
vercel promote "$FRONTEND_DEPLOYMENT_URL"
```

生产候选的 Auth 回调需要匹配候选/稳定地址；不能为了候选测试重置生产 Site URL。推广后以项目实际稳定 URL 验收，候选可访问不代表用户入口已更新。如果现有 CLI/套餐不支持阶段发布，则沿用可核实的 Git/平台生产发布机制并准备恢复点，不默认升级套餐。

在实际静态输出配置中仅合并真实页面的 rewrites，保留 framework、buildCommand、outputDirectory、headers、现有函数和域名配置。下面是 **vercel.json 部分字段示例**，不能整体覆盖项目文件，也不能与互斥的旧 routes 配置盲目混用：

```json
{
  "rewrites": [
    {"source": "/login", "destination": "/index.html"},
    {"source": "/auth/callback", "destination": "/index.html"},
    {"source": "/projects/:id([A-Za-z0-9_-]+)", "destination": "/index.html"}
  ]
}
```

检查框架生成的默认 fallback 是否仍把未知 API/资源转成 HTML；仅添加上述片段不能证明路由正确。静态多页使用实际页面映射。检查入口短缓存、资源不可变 URL、service worker 与旧资源保留；保留期内旧资源需包含在新产物中或由已验证的固定部署地址提供，不能把部署历史保留误认为生产域名仍可读取旧文件。

失败恢复/显式回退先核实项目当前生产目标与授权，再按套餐能力执行：

```sh
vercel rollback "$FRONTEND_PREVIOUS_DEPLOYMENT_URL"
```

记录实际回退结果并检查生产别名；套餐若限制目标或仅能回退前一部署，按实际能力执行，不编造任意历史回退。回退后核实自动生产域名分配/后续发布状态，避免下一次 Git 自动发布立即覆盖恢复结果；仅在对应授权内调整 CI 或保护设置。

依据：[部署命令](https://vercel.com/docs/cli/deploy)、[阶段发布](https://vercel.com/docs/cli/deploying-from-cli)、[推广](https://vercel.com/docs/cli/promote)、[回退](https://vercel.com/docs/cli/rollback)、[vercel.json](https://vercel.com/docs/project-configuration/vercel-json)。
