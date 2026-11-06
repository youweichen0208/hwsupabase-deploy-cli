# 华为云前端部署与 Supabase 接入 Skill

通过 AI agent 创建、部署、更新和回退 React/Vue 静态前端，默认使用私有 OBS＋CDN，并连接已有华为云 RDS Supabase。新项目未指定框架时采用 React＋Vite＋TypeScript，也支持普通静态网站和已能静态导出的项目。

## 部署选择与接入流程

![前端托管选择与 Supabase 接入流程：已有平台可保留；华为云有域名走 OBS/CDN，准备域名时先本地预览，明确选择 IP 访问时可用 ECS；也可选择其他平台默认域名。最终由浏览器调用已有 Supabase。](docs/deployment-flow.svg)

[查看完整流程图与可编辑 SVG](docs/deployment-flow.svg)

图例：**蓝色实线**表示当前 skill 已覆盖的 OBS/CDN 流程；**灰色虚线**表示可选路线，ECS 与其他平台尚未实现完整任务流程；**绿色**表示共同的浏览器访问与 Supabase 接入链路。

- 前端已在其他平台托管时，可以保留现有部署；尚未托管时，也可以选择提供默认访问域名的平台。
- 选择华为云且已有可用域名时，使用私有 OBS＋CDN；准备办理域名时，先完成本地构建与预览，待证书及适用备案条件齐备后上线。
- 不准备域名且明确需要公网 IP 访问时，可另行选择 ECS＋EIP＋Nginx，需要承担服务器维护、带宽费用并处理 HTTPS。**缺少域名不会自动购买 ECS，OBS 桶也不能直接绑定 EIP。**
- 所有路线均由用户浏览器调用已有 Supabase 的 HTTPS API；公开 Key、CORS、登录回调与 RLS 需配置并验收。流程图用于选型，不表示这些路线都已由当前 skill 实现。

采用默认 OBS＋CDN 方案时，用户使用自己的域名访问，无需登录华为云；应用登录由 Supabase Auth 处理。SSR、服务端 API 和运行时秘密密钥需要另行明确后端依赖。

## 安装与使用

将 [skills/huawei-supabase-frontend](skills/huawei-supabase-frontend) 整个目录复制或链接到 agent 的 skills 目录，保留 `references` 和 `agents`。从旧版迁移时仅替换确实指向本仓库的安装链接，独立副本先比对再处理。旧 FunctionGraph 版本保留在 Git 历史中。

四种任务共用项目环境记录，不提供独立部署 CLI：

```text
$huawei-supabase-frontend 准备北京四的前端部署环境，连接已有 Supabase，先检查域名和资源费用。
$huawei-supabase-frontend 创建 React 前端并部署到 OBS/CDN，接入已有 Supabase；没有域名时先完成本地预览。
$huawei-supabase-frontend 更新当前应用，复用已有环境并保留上一成功版本。
$huawei-supabase-frontend 回退到指定的已验证版本，刷新页面缓存并检查真实访问。
```

部署优先使用官方 KooCLI，OBS 文件操作使用内置 OBS 工具或官方 obsutil。复用已有认证，首次凭证配置与登录通过官方交互完成；秘密不写入聊天、仓库或前端构建产物。

## 首次上线条件

若采用 OBS＋CDN 路线且尚未准备可用域名，首次正式上线需先准备域名。OBS 默认域名可能强制下载网页，不能作为可靠的网页入口，见 [OBS 访问说明](https://support.huaweicloud.com/usermanual-obs/obs_03_0342.html)。缺少域名时交付本地预览、构建产物和上线清单。

中国大陆及全球 CDN 加速要求备案；首次通过华为云备案还有可备案资源条件，见 [备案条件](https://support.huaweicloud.com/icprb-icp/icp_01_0008.html)。注册域名不等于所有条件齐备；skill 不会因缺项自动购买服务器或切换地区。

前端侧以约 300 元/月为费用规划目标，按实际用量估算并设置适用告警；它不是账单硬上限。已有 Supabase 的实例与公网费用独立核算，不自动购买数据库。

## 指引

| 文件 | 内容 |
| --- | --- |
| [SKILL.md](skills/huawei-supabase-frontend/SKILL.md) | 任务入口、边界与工作流 |
| [前端构建](skills/huawei-supabase-frontend/references/frameworks.md) | 静态边界、版本资源和本地验证 |
| [认证](skills/huawei-supabase-frontend/references/authentication.md) | 凭证复用与失败诊断 |
| [区域映射](skills/huawei-supabase-frontend/references/regions.md) | 中国站/国际站名称解析与服务能力核实 |
| [Supabase](skills/huawei-supabase-frontend/references/supabase.md) | 已有应用发现、公开 Key、HTTPS 与权限隔离 |
| [域名与托管](skills/huawei-supabase-frontend/references/hosting.md) | 私有 OBS、CDN、DNS、SPA 路由和费用 |
| [发布与回退](skills/huawei-supabase-frontend/references/deployment.md) | 发布清单、缓存、恢复和真实验收 |
| [官方资料](skills/huawei-supabase-frontend/references/sources.md) | 来源与核实限制 |

## 验证状态

本仓库仅包含 skill，不包含待部署应用。格式、内部引用、shell 示例语法及六种场景推演已检查：无域名、认证失败、已有环境、多个 Supabase 候选、SSR 不兼容、发布失败恢复。命令的核对来源及未实测部分见官方资料。

- **skill 已完成**：新名称、文档与 UI 元数据已迁移。
- **本地应用已验证**：不适用，本次未创建应用。
- **环境已准备**：未执行，本次未配置云资源。
- **线上验收通过**：未执行，待域名及环境就绪后验证 HTTPS、路由、登录、隔离、更新和回退。
