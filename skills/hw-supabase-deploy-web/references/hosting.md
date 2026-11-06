# OBS 网站发布

## 构建与文件

构建输出必须是可由浏览器直接读取的文件。检查入口路径、静态资源 public/base path、动态路由、运行时注入配置方式。默认构建助手对 HTML 和非内容哈希文件设置 no-cache；带内容哈希文件可长期缓存。

`build-web release` 保存完整本地快照，不直接上传。agent 使用 manifest 生成官方 OBS 上传命令/工作流，设置 Content-Type 与 Cache-Control。不要把整个源码目录上传到网站桶。

发布新版本时先上传资产，再更新 HTML 与公开运行配置；最后验证入口引用的文件都存在。保留旧资产，回退从保存的完整快照恢复。不同版本引用相同名字的可变 JS/CSS 可能发生短暂混合版本；优先使用项目构建器的内容哈希输出。

## 网站、域名和 SPA

用官方 DevKit `huaweicloud_obs_set_website_config` / `huaweicloud_obs_set_cors`；未装 MCP 时用共享入口 `obs-site <settings.yaml>`，依赖官方 OBS SDK。此辅助命令只处理网站桶，并执行配置回读；它不自动配置公开桶策略、DNS、TLS或 CDN，这些由 setup 的官方操作完成。

桶默认域名在一些区域下载 HTML 而不展示。正式交付必须检查实际自定义域名。OBS 自定义域名已有证书托管，CDN 不是 HTTPS 的强制依赖。

按现有项目区分多页、hash SPA、history SPA。多页保持真实 404；hash SPA 不需要服务端路径回退；history SPA 需要验证 OBS 网站规则实际能否满足深链接。错误文档返回 index.html 不等价于正确的 HTTP 200 重写，不能把所有缺失 JS/CSS 也转成 HTML。若目标托管能力无法满足客户路由约定，应明确阻点，提出有证据的 CDN/路由调整方案，不静默改前端路由。

## 公开数据边界

前端直连 Supabase 的公开 URL/key，业务权限靠认证和 RLS。CORS 不是身份认证。service_role/secret key、数据库密码、OBS AK/SK 不进入浏览器 bundle/config/source map。

Storage 和 Realtime 直接连接 Supabase，不默认经 Python 函数代理大文件或 WebSocket。登录的 Site URL、redirect allowlist 必须与实际网站地址一致。
