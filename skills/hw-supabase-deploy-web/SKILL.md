---
name: hw-supabase-deploy-web
description: 将连接华为云 RDS Supabase 的静态前端构建并部署到 OBS，处理公开配置、网站路由、HTTPS、缓存、跨域和可回退产物。不部署 Next.js 等需要服务端运行的 SSR 输出。
---

# OBS 静态前端交付

使用 [deliver](../hw-supabase-deliver/SKILL.md) 的配置、release 与状态。缺少桶/域名时先用 [setup](../hw-supabase-setup/SKILL.md)。

1. 检查 package scripts、构建输出、路由模式。区分纯静态导出与依赖 Node 服务器的产物；后者不能当作静态文件上传。
2. 保留客户框架与包管理器，通过项目自己的构建机制注入 Supabase **公网 HTTPS URL、公开客户端 key** 和业务 APIG URL。构建进程不接收服务端 key、AK/SK、数据库密码；Vite/React 等变量前缀按现有项目映射。
3. 运行共享辅助入口 `build-web <release>`。它生成独立快照与 `web-manifest.json`，记录摘要、MIME、缓存策略。现有 release 不覆盖；秘密扫描是附加检查，仍需检查构建变量和输出内容。
4. 使用 `hcloud obs cp/sync` 上传发布资源。网站托管与 CORS 使用 DevKit 已有 OBS 工具；没有 MCP 时使用 `obs-site settings.yaml` 官方 SDK 辅助命令。详见 [网站发布](references/hosting.md)。
5. 验证候选资源后，最后更新入口 HTML；缓存策略按 manifest 设置。保存旧版快照和对象，发布过程中不运行带删除选项的 sync。
6. 真实域名验证页面显示、HTTPS、深层链接刷新、资源 MIME/404、登录回调、跨域；仅 `200` 或 OBS 上传成功不代表前端可用。把用例交给 deliver 的最终验收。

回退从前一发布快照恢复所有入口与必要资源，并再次验证。多 HTML 页面逐对象更新不是全站原子切换，应明确短暂混合版本窗口；不宣称零停机原子发布。
