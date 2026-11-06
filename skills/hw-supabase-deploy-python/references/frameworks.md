# Flask / Django 适配

## 公共运行约定

使用 HTTP 函数，ZIP 根目录提供可执行 bootstrap，以当前官方 Python 3.12 解释器启动 Gunicorn，监听 127.0.0.1:8000。脚本生成的路径来自官方 HTTP 函数文档，首次接入区域必须实测。不要在函数启动时安装依赖、执行数据库迁移或启用开发服务器。

在发布候选版本前设置非敏感的 `HWSUPABASE_RELEASE`，健康接口返回该版本标记（样例使用 X-HWSupabase-Release）。验收必须确认访问到本次版本，而非仅看到旧版本的 200。

构建镜像以 digest 固定；CPU 架构匹配函数。纯 Python wheel 可做本地辅助测试，带原生扩展的依赖必须在匹配 ABI/系统库的 Linux 镜像构建，并在真实函数 import 验证。要求 requirements/lock 固定版本；构建结果保留依赖清单、ZIP SHA256、运行时与镜像信息。

函数超时和 APIG 后端超时分别设置；不能把函数最长执行时间当作 HTTP 链路上限。用户文件和 session 不依赖本地磁盘；/tmp 仅临时使用。后台任务、SQLite 持久数据库、长驻 worker 属于需要调整的项目依赖。

## Flask

- 检查 application object 或工厂，必要时生成薄 WSGI 入口导出 app，不改变业务路由。
- 配置生产 SECRET_KEY 和现有 session 策略；debug=False。
- 保留已有认证；示例 `/me` 使用 Auth /user 校验 token，返回最小用户 ID。
- 不盲目信任所有 X-Forwarded-*。只有已验证代理链会覆盖这些头时才配置 ProxyFix；验证外部 HTTPS 重定向。

## Django

- entrypoint 指向 `<project>.wsgi:application`；使用生产 settings。
- 明确 ALLOWED_HOSTS、CSRF_TRUSTED_ORIGINS、session/CSRF secure cookie；设置 SECURE_PROXY_SSL_HEADER 前验证 APIG 是否覆盖伪造头。
- 执行 `manage.py check --deploy`，解释每个剩余告警；检查 SECRET_KEY、DEBUG、TLS 重定向，不靠忽略系统检查完成验收。
- `collectstatic --noinput` 作为构建/发布步骤，产物使用网站桶和已验证 STATIC_URL。media 走 Supabase Storage，不写函数目录。
- ORM 使用客户实际 PostgreSQL host/port/driver，不能把 Supabase :8443 Data API 当成数据库连接串。华为云场景不默认套用 supabase.com 的 transaction pooler 地址。
- 若实际使用 transaction pooler，按驱动与 Django 官方要求处理 server-side cursors/prepared statements；控制实例并发与每进程连接数。
- 迁移作为独立交付步骤执行一次；先检查与旧应用版本兼容性。函数冷启动和回退流程不得自动 migrate。
- Supabase Auth 用户与 Django auth.User 不是同一体系；保留应用既有映射，不能替客户隐式迁移登录模型。

## 候选发布与回退

使用不承载生产流量的候选路由验证，保存 code_size/digest 与不可变版本。稳定 alias 的可用性与 APIG 后端引用先实测；若区域不支持所需别名语义，明确记录并使用固定版本后端发布，而不是伪造 alias。

回退只恢复已登记版本和网关/静态入口，密钥轮换、数据库 migration、Auth 配置不自动恢复。更新与回退后都重新跑真实路由和认证用例。
