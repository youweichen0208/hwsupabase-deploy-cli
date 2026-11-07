# 官方资料与核实边界

维护日期：2026-11-07。执行时以目标站点/区域官方文档、API Explorer 和本地 CLI 帮助为准。此仓库交付操作指引，不包含生产部署证明。

| 资料 | 使用时机 |
| --- | --- |
| [KooCLI 概述](https://support.huaweicloud.com/intl/en-us/productdesc-hcli/hcli_01.html) | 工具安装与能力入口 |
| [JSON 参数输入](https://support.huaweicloud.com/usermanual-hcli/hcli_05_12.html) | 生成当前 API 请求文件 |
| [SSO](https://support.huaweicloud.com/usermanual-hcli/hcli_03_009.html)、[认证模式](https://support.huaweicloud.com/usermanual-hcli/hcli_05_10.html) | 认证准备；已有参数源自此前 7.3.12 帮助核对，本次未云端实测 |
| [中国站 API Explorer](https://console.huaweicloud.com/apiexplorer/)、[国际站 API Explorer](https://console-intl.huaweicloud.com/apiexplorer/) | 查询 OBS/RDS 服务终端节点、最新 API 与 schema |
| [OBS 默认域名预览限制](https://support.huaweicloud.com/usermanual-obs/obs_03_0342.html) | 缺少自有域名时说明网页下载限制 |
| [备案条件](https://support.huaweicloud.com/icprb-icp/icp_01_0008.html) | 检查首次备案的资源及身份条件 |
| [私有桶 CDN 接入](https://support.huaweicloud.com/usermanual-obs/obs_03_0600.html) | 私有桶回源、委托权限及加速范围 |
| [CDN URL 重写](https://support.huaweicloud.com/usermanual-cdn/cdn_01_0263.html) | 首页与限定 SPA 页面改写 |
| [CDN CLI v2](https://support.huaweicloud.com/intl/en-us/clir-cdn/CDN-cli_v2_en.html) | 核对版本化命令；目录检索确认 CreateRefreshTasks/v2，执行前仍需帮助核对 |
| [obsutil 上传](https://support.huaweicloud.com/utiltg-obs/obs_11_0013.html)、[对象元数据](https://support.huaweicloud.com/utiltg-obs/obs_11_0041.html) | 上传校验、MIME 与缓存元数据 |
| [RDS Supabase Data API](https://support.huaweicloud.com/usermanual-rds-pg/rds_supabase_23.html)、[Dashboard](https://support.huaweicloud.com/usermanual-rds-pg/rds_supabase_04.html) | 已有应用 SDK/RLS 与实际支持范围 |
| [Supabase API Keys](https://supabase.com/docs/guides/getting-started/api-keys) | 公开 Key 与服务端秘密的边界，华为云可用类型另验 |

本次通过官方页面/检索核对域名限制、备案条件、私有桶委托、CDN 改写、obsutil 元数据和 Key 类型。早期核对时未找到 KooCLI/obsutil；后续隔离帮助验证见下文，仍未执行真实云请求。`ListAiApplications`、`ShowSupabaseApplication` 沿用任务提供的已核实命令名；本次公开文档搜索未返回可独立核对的对应参数页，所以仅提供帮助发现入口，不编造请求字段或声称已再次验证。

区域表保留历史名称解析，OBS/RDS 能力需逐次按实际账号确认。价格、配额、可备案资源资格及委托范围均在实施时查询；预算示例不代表报价或费用上限。

## 新增路线的官方依据

| 资料 | 核实内容 |
| --- | --- |
| [Pages Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/) | 项目创建、预览与生产分支、实际默认域名 |
| [Pages 路由](https://developers.cloudflare.com/pages/configuration/serving-pages/)、[重写](https://developers.cloudflare.com/pages/configuration/redirects/)、[回退](https://developers.cloudflare.com/pages/configuration/rollbacks/) | 顶层 404.html、限定页面改写和生产部署回退 |
| [Vercel 部署](https://vercel.com/docs/cli/deploy)、[阶段发布](https://vercel.com/docs/cli/deploying-from-cli) | Build Output、生产构建与跳过域名分配 |
| [Vercel 推广](https://vercel.com/docs/cli/promote)、[回退](https://vercel.com/docs/cli/rollback)、[配置](https://vercel.com/docs/project-configuration/vercel-json) | 生产入口切换、能力边界和路由配置 |

本次另用 Wrangler 4.158.0 的本地帮助复核了 `pages deploy` 的 directory、project-name、branch 参数和 `pages deployment list` 的 project-name/environment 参数。只执行帮助查询，没有登录或发布。Vercel 65.12.1 的临时 CLI 下载未及时完成，已停止；其参数仅按上列官方文档核对，未声称本地 CLI 实测。

这些来源用于编写工作流，不意味着已在用户账号执行。新增路线没有云端创建、购买或生产部署实测。第三方 CLI 的实际版本/套餐及地区访问质量仍需执行任务时核实。

## 构建环境

版本和操作以执行时官方文档与本地帮助为准，不把示例镜像或本地验证版本当作永久推荐版本。

| 资料 | 使用时机 |
| --- | --- |
| [Node 发布状态](https://nodejs.org/en/about/previous-releases)、[发行文件](https://nodejs.org/dist/) | 选择受支持版本、系统/架构与下载校验 |
| [package.json](https://docs.npmjs.com/cli/v11/configuring-npm/package-json/)、[npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/) | 版本约束及锁文件安装 |
| [pnpm install](https://pnpm.io/cli/install)、[Yarn install](https://yarnpkg.com/cli/install) | 按已识别包管理器版本冻结安装 |
| [Node 镜像](https://github.com/nodejs/docker-node)、[构建 secrets](https://docs.docker.com/build/building/secrets/) | 固定构建环境、私有依赖凭证 |

本次补齐不代表已在客户机器安装工具或在客户云环境实测。实际本地测试与未验证项目见 README 的验证状态。

## 统一认证入口

- [DevKit 1.1.13 发布包](https://www.npmjs.com/package/huaweicloud-devkit/v/1.1.13)：固定入口及运行要求；已检查发布包初始化行为，不将 GitHub main 的能力视为已发布保证。
- [官方 DevKit](https://github.com/huaweicloud/huaweicloud-devkit)：统一认证设计与官方维护来源。
- [KooCLI 内置 OBS](https://support.huaweicloud.com/usermanual-hcli/hcli_04_009.html)：`hcloud obs`、独立配置。
- [KooCLI 配置参数](https://support.huaweicloud.com/usermanual-hcli/hcli_03_003_01.html)：认证模式和加密配置；本项目不关闭加密以提取秘密。

隔离测试覆盖虚构凭证输入、部分成功、身份失败和覆盖行为，见仓库 `docs/auth-validation.md`。没有真实云认证或 OBS 上传实测。

## GET 验收

[Issue #1 现场报告](https://github.com/youweichen0208/hwsupabase-deploy-cli/issues/1) 揭示 HEAD 与 GET 响应不一致的验收盲点。通用验收要求检查 GET 最终响应、正文并完成浏览器验证，不将单个环境的响应行为推广为所有 OBS 的特性。本地模拟与历史 CLI 验证见 [验证记录](../../../docs/obs-validation.md)。
