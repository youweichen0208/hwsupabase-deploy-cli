# 验证记录

日期：2026-11-06。

## 已完成

- macOS 本地 Python 3.9.6 执行 27 项单元/行为测试，覆盖状态恢复、隔离、打包、发布记录和独立安装。
- 四个 Skill 通过 skill-creator 的 quick_validate，具备 frontmatter 和 agents/openai.yaml。
- Python 源码语法编译检查；示例工作流本地 plan 校验。
- 静态前端示例实际执行 Node 构建，校验公开配置注入、产物快照及服务端密钥未被传入构建环境。
- 在临时目录安装整个 Skill Set，并从安装后的独立入口运行 preflight；无需原仓库 import 路径。
- 独立行为评审发现的 OBS absence 探针、跨项目输入、超时 ID 恢复、OpenSSH 私钥问题已修复并增加回归测试。
- 第二轮场景评审发现的失败发布回退目标、版本登记与云端证据不一致问题已修复；增加版本响应断言，旧版返回 200 不再通过新版本验收。

Python ZIP 构建的 Docker 参数、bootstrap 权限和依赖路径通过模拟构建验证。已确认本机 Docker 可启动现有 Python 3.12.16 镜像，但**没有将该 Debian 镜像认证为 FunctionGraph 原生依赖构建镜像**。

## 当前环境无法完成的验证

- 本机没有 KooCLI，也没有客户配置/云凭据；未创建或修改任何云资源。
- `uv sync --extra obs` 下载依赖时因本机执行环境的 PyPI DNS 解析失败而中止。因此官方 OBS SDK 的真实调用及 Flask/Django 固定依赖安装尚未验证；SDK交互使用 mock 测试。
- 未实测 APIG → FunctionGraph HTTP 函数 → Gunicorn → Supabase 内网。包括原始 HTTP/封套差异、多 Cookie、路由、SSL、Auth/Storage/RLS 都须按交付验收清单在客户环境确认。
- 尚无经真实云部署验证的 KooCLI/DevKit 版本锁。示例 Python 直接依赖及 OBS SDK 固定为调研时的候选版本；正式交付需生成完整依赖锁并保存验证过的工具版本、镜像 digest。

这些限制是验收证据的边界，不会被本地工具自动标成成功。生产交付前参考 [验收清单](../skills/hw-supabase-deliver/references/acceptance.md)。
