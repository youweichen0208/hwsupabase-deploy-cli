# 框架适配

## 公共运行约定

以下针对代码包形式的 HTTP 函数；容器镜像应另查当前容器运行契约，不直接套用。

- HTTP 函数通过部署包根目录的 bootstrap 启动，官方代码包示例监听 127.0.0.1:8000。入口使用 HTTP 服务，不改造成事件 handler。
- bootstrap 使用 LF 换行并保留可执行权限；先进入 RUNTIME_CODE_ROOT，再 exec 前台进程。解释器使用所选云端运行环境的实际路径。官方页面包含旧版本示例，不直接复制其旧 Node/Python 版本。
- 使用生产启动方式，关闭调试、自动重载。应用日志写 stdout/stderr；Python 使用无缓冲输出。
- 在与云端 OS、CPU 架构和解释器兼容的 Linux 环境构建原生依赖。macOS 的虚拟环境、node_modules 或二进制 wheel 不能直接视为可部署依赖。
- 在独立暂存目录组装包，根层为 bootstrap、应用和运行依赖，不能额外包一层项目目录。排除 .git、凭证、真实 .env、本机虚拟环境和无关缓存；保留运行需要的模板、迁移文件和静态产物。
- 在打包后的解压目录验证入口和依赖，不能只从源码目录启动成功。检查 ZIP 根目录、文件权限、压缩/解压大小和当前上传限额。
- 持久数据、上传文件及跨实例会话使用外部持久服务；实例本地文件只作临时用途。依赖安装、前端构建和数据库迁移不放进 bootstrap。

启动文件的组织形态：

```sh
#!/bin/sh
set -eu
cd "${RUNTIME_CODE_ROOT:?RUNTIME_CODE_ROOT is required}"
# 在生成实际文件时，将最后一行写成已核实的解释器和应用启动命令。
```

这是结构示例，不是可部署的完整启动文件。生成的文件必须包含对应框架的 exec 命令，不留示例占位内容。

## Flask

识别 app 对象或工厂函数，保留现有模板与静态目录。新项目提供主页及轻量健康检查路由，依赖清单包含选定的生产 WSGI 服务。

使用 Gunicorn 等生产 WSGI 服务。例如在已安装依赖、解释器可用时：
- 对象入口：python -u -m gunicorn --bind 127.0.0.1:8000 app:app
- 工厂入口：python -u -m gunicorn --bind 127.0.0.1:8000 'app:create_app()'

bootstrap 中用核实的云端 Python 绝对路径替换 python，并以 exec 启动。若依赖安装到独立目录，显式设置 PYTHONPATH；worker 数量和超时按实际内存及网关预算选择，不照搬服务器多核配置。

验证入口可导入、模板渲染、静态资源和相关 API。Supabase 连接方式见 [Supabase](supabase.md)。

官方参考：[Flask 的 Gunicorn 部署](https://flask.palletsprojects.com/en/stable/deploying/gunicorn/)。

## Express

保留 package.json 的模块类型、锁文件和脚本。按锁文件对应包管理器安装，在构建阶段保留开发依赖，构建后再组装运行依赖。生产入口直接使用已构建的 JS；bootstrap 以核实的 Node 绝对路径 exec 启动，监听 127.0.0.1:8000。

新项目提供主页和健康检查路由。已有 TypeScript 项目使用现有构建流程，确认编译输出包含服务端入口。

托管 React/Vue 等 SPA 时：
- 按项目配置构建前端，确认真实输出目录及资源 base 路径。
- 使用 express.static 提供该目录；以启动文件位置确定绝对目录，避免依赖调用时的工作目录。
- API 路由先注册，再静态资源及 SPA 回退。只为符合页面导航条件的 GET/HEAD 请求回退 index.html，未知 API 和缺失 JS/CSS 返回正确的 404。
- Express 4 与 5 的通配路由语法不同，按已安装版本实现；不要复制不兼容的 '*' 路由。
- 检查浏览器公开变量是否在构建阶段替换。更新函数环境变量通常不会修改已经编译的前端 bundle，需要重新构建。

验证首页、一个实际资源、深层路由刷新、缺失资源和未知 API；React/Vue SSR 应用不能当作纯静态目录托管，保留其框架服务端能力，必要时说明超出当前 Express 适配范围。

官方参考：[Express 静态文件](https://expressjs.com/en/starter/static-files/)。

## Django

识别 settings 模块及项目的 wsgi.application。使用生产 WSGI 服务，例如：
python -u -m gunicorn --bind 127.0.0.1:8000 project.wsgi:application
其中 project 应替换为实际模块；bootstrap 用核实的云端 Python 路径并 exec。

- DEBUG=False；SECRET_KEY 通过服务端配置提供。ALLOWED_HOSTS 包含真实入口域名。使用表单或会话认证时，按实际 HTTPS origin 配置 CSRF_TRUSTED_ORIGINS。
- 仅在确认网关设置和可信代理边界后配置转发头信任，避免无条件信任客户端伪造的 HTTPS/Host 头。
- 构建阶段执行 collectstatic，并明确生产静态文件服务方案，例如项目已有中间件。Gunicorn 本身不会替 Django 提供静态资源。
- 运行 manage.py check --deploy，解释并处理与目标部署有关的问题。
- 识别数据库及迁移状态。仅在用户授权数据库变更后单独执行迁移，避免多个冷启动并发 migrate。SQLite 不作为多实例生产持久数据库。
- Django ORM 直连 PostgreSQL 与调用 Supabase Data API 是两种集成方式。数据库直连凭证、网络及权限与 anon key 不同；不要把 service_role key 当成数据库密码。

验证页面、静态资源，以及适用的登录/CSRF 流程。已有 ASGI/WebSocket 应用保留其协议需求，另核实目标区域、网关和 ASGI 服务支持，不能静默切成 WSGI。

官方参考：[Django 部署检查](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)，执行时使用与项目版本匹配的文档。
