---
name: hw-supabase-deploy-python
description: 将 Flask 或 Django WSGI 项目部署到华为云 FunctionGraph HTTP 函数，通过 APIG 对外提供业务 API，并以内网连接已有 RDS Supabase。包含依赖打包、版本发布和框架检查；不处理常驻 worker、通用 ASGI 或数据库自动回退。
---

# Python Web 项目部署

先使用 [deliver](../hw-supabase-deliver/SKILL.md) 的配置和状态；网络及 APIG 未准备好时调用 [setup](../hw-supabase-setup/SKILL.md)。

1. 检查框架、Python 约束、WSGI 入口、requirements/lock、数据库驱动、系统库、文件持久化、定时任务。首版打包器基线是 Python 3.12；不兼容时报告差异，不静默升级客户应用或切换架构。
2. 按框架读取 [Flask/Django 适配](references/frameworks.md)。确定 `module:object` 入口、允许打包的文件，以及启动时所需环境变量。
3. 选择经验证的 Linux 构建镜像并固定 digest、CPU 架构。纯 Python 依赖与包含原生扩展的依赖分别验收；后者必须匹配 FunctionGraph 运行环境。不能上传 macOS 虚拟环境。
4. 运行 `build-python <release>`：Docker 安装项目锁定依赖，生成 `bootstrap` 和 ZIP，保存摘要与镜像信息。构建失败需要清理该失败的本地构建目录或使用新 release，不能把残留 ZIP 当作可交付产物。
5. 把 ZIP 上传私有产物桶，以官方 `CreateFunction`/`UpdateFunctionCode` 部署 HTTP 函数；代码 URL、agency、VPC、runtime/func_type 从当前 `--help`/`--skeleton` 和官方样例确定。`code_filename` 只是文件名，不能代替 ZIP 内容上传。
6. 回查函数 `code_size`、配置与代码摘要，发布不可变版本；配置 APIG 的 FunctionGraph 后端、根路径及深路径、允许的方法、CORS 和 Authorization 透传。先候选路由验收，再让 deliver 切换稳定版本。

## HTTP 契约门槛

首次部署区域先用随包提供的 Flask/Django contract 样例，按 [验收清单](../hw-supabase-deliver/references/acceptance.md) 跑状态码、原始 body、二进制、重定向和多个 Set-Cookie。官方 HTTP 文档与部分 Python 例子存在封套差异，没通过时保留探针、响应类型与请求 ID，停止宣称兼容。不能把 Django 返回的 HTML JSON 封套视为网站正常。

模板的 `/me` 通过 Supabase Auth 校验用户 token；业务已有认证流程应保留并测试。APIG 无平台认证不代表业务接口无需认证。禁止把高权限 service key 当作所有用户的默认身份。
