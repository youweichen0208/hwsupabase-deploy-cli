# 华为云 Supabase 应用交付 Skills

为交付团队提供四个可组合 Skills：准备客户资源、部署 OBS 静态前端、部署 Flask/Django、协调验证和版本回退。连接**已有华为云 RDS Supabase**，复用官方 KooCLI、DevKit 与 OBS SDK。

这是 agent 驱动的交付工具集：agent 按客户项目及当前官方 API 生成执行清单，共享 Python 脚本负责可重复的状态、构建和验证。示例配置不是任何客户的生产配置。

## 完成状态与文档导航

首版四个 Skills、共享脚本、安装器和三类应用样例已实现。已记录的本地验证包括 27 项测试及四个 Skill 格式校验；**真实云端交付尚未验收**，不能据此宣称已可直接用于客户生产环境。具体证据与未完成项见验证记录。

| 文档 | 用途 |
|---|---|
| [GLOSSARY.md](GLOSSARY.md) | 客户环境、发布版本、切流、续跑、两类回退及验收术语 |
| [调研记录](docs/research.md) | 已确认的需求范围、复用方案与实现取舍 |
| [官方依据](skills/hw-supabase-deliver/references/sources.md) | 官方文档、源码及能力边界 |
| [执行与状态契约](skills/hw-supabase-deliver/references/workflow.md) | 配置、工作流、检查点、发布记录和回退操作 |
| [交付验收清单](skills/hw-supabase-deliver/references/acceptance.md) | 目标区域 HTTP 契约、真实业务检查及交接证据 |
| [验证记录](docs/validation.md) | 已完成的检查，以及依赖安装和云端验证的实际阻点 |

首次使用先阅读术语和安装说明；准备实际客户交付时，结合配置示例、执行契约与验收清单。`current` 表示当前已验收版本，新版本切流失败时它不一定等于云端正在响应的版本。

## 安装

工程师本地使用 Python ≥3.9、uv、KooCLI；Python 应用打包另需 Docker。当前文件锁支持 macOS/Linux，Windows 使用 WSL。

```sh
uv sync --extra obs
python3 scripts/install_skills.py --destination /path/to/your/agent/skills
```

安装器一次安装四个 Skills，附带共享模块与样例；拒绝覆盖已有同名 Skills。安装后可直接调用 `$hw-supabase-deliver`，无需原仓库仍在。安装只写指定目标，不自动修改全局 agent 配置或云凭据。

| Skill | 功能 |
|---|---|
| [hw-supabase-deliver](skills/hw-supabase-deliver/SKILL.md) | 统一入口、工作流、验证、续跑与回退 |
| [hw-supabase-setup](skills/hw-supabase-setup/SKILL.md) | OBS/APIG/委托/网络及可选 Storage 接入 |
| [hw-supabase-deploy-web](skills/hw-supabase-deploy-web/SKILL.md) | 静态前端构建、网站发布和回退快照 |
| [hw-supabase-deploy-python](skills/hw-supabase-deploy-python/SKILL.md) | Flask/Django HTTP 函数与 APIG |

## 从客户项目开始

复制并填写 [配置示例](examples/hwsupabase.yaml)，按客户情况保留 web、python 或两者。配置文件中只有密钥环境变量名；实际秘密不入 Git/聊天/日志。OBS 使用客户独立 config 文件。

```sh
uv run --extra obs hwsupabase --config /customer/project/hwsupabase.yaml preflight
uv run --extra obs hwsupabase --config /customer/project/hwsupabase.yaml status
```

`preflight` 不调用云 API。即使配置语法通过，也必须进一步查询账号、权限、区域、规格、网络、域名和费用。示例的 replace-with 值必须替换。

agent 按 [执行契约](skills/hw-supabase-deliver/references/workflow.md) 生成客户工作流，然后使用：

```sh
uv run --extra obs hwsupabase --config /customer/project/hwsupabase.yaml plan setup.yaml
uv run --extra obs hwsupabase --config /customer/project/hwsupabase.yaml run setup.yaml
uv run --extra obs hwsupabase --config /customer/project/hwsupabase.yaml build-web r1
uv run --extra obs hwsupabase --config /customer/project/hwsupabase.yaml build-python r1
```

发布顺序：setup → build → stage → 候选验证 → register-release → promote → verify → activate。回退：rollback-plan → 真实云端 rollback 工作流 → verify → activate。新版本切流/验收失败时用 `rollback-plan --failed-promotion` 恢复最后成功的 current；撤销已成功激活版本时，默认恢复 previous。**修改本地发布记录不代替云端切换。**

Python 构建镜像必须填写已测试的 Linux/Python 3.12 镜像 digest。构建器不提供未经验证的默认镜像，不自动升级应用运行时或替换客户数据库。Django migrate 是独立步骤。

## 本地验证

```sh
python3 -m unittest discover -s tests -v
```

测试使用模拟官方工具和临时目录，覆盖重复执行、超时续跑、漂移、客户隔离、密钥不入 argv、产物检查、HTTP 断言、激活门槛及独立安装。

Flask、Django 和静态页面位于 [examples](examples)，用于实际云端验收。HTTP 函数官方示例对响应格式有差异，必须在目标区域验证状态码、重定向、多 Cookie 和二进制。完整检查见 [验收清单](skills/hw-supabase-deliver/references/acceptance.md)。

## 当前边界

- 不创建 Supabase 本身；不支持 SSR、常驻 worker 或通用 ASGI 托管。
- 不自研通用云 SDK；区域参数、RDS 公测 API 可用性由官方工具发现。
- 不提供基础设施自动销毁、数据库回滚或多机器并行部署锁。
- 自动 HTTP 用例不替代浏览器、RLS、Storage 与真实业务验收。
- 本地状态和产物需要随客户环境完整交接；不能只复制 YAML 后宣称可回退。

调研依据与实测状态见 [调研记录](docs/research.md) 和 [验证记录](docs/validation.md)。
