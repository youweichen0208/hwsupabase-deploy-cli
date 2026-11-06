---
name: hw-supabase-deliver
description: 为交付团队编排华为云 RDS Supabase 客户应用上线、更新、验收、失败续跑和应用版本回退。组合 setup、静态前端和 Flask/Django 部署技能；不创建 Supabase 本身，不负责通用云资源销毁或数据库回滚。
---

# RDS Supabase 应用交付

目标：客户现有 RDS Supabase + OBS 静态前端 + APIG 专享实例 + FunctionGraph HTTP 函数。前端直连 Supabase 公网 HTTPS；Python 后端走现有 VPC。

## 入口与路由

先读客户仓库和 `hwsupabase.yaml`，识别单体/前后端分离、构建命令、WSGI 入口、持久化依赖与已部署资源。不要因为仅需更新应用而重新创建基础设施。

- 首次部署、缺少云资源或需要 Storage 接入：读 [setup](../hw-supabase-setup/SKILL.md)。
- 静态前端：读 [deploy-web](../hw-supabase-deploy-web/SKILL.md)。
- Flask/Django：读 [deploy-python](../hw-supabase-deploy-python/SKILL.md)。
- 编写执行清单、续跑与发布：读 [执行与状态契约](references/workflow.md)。
- 真实验收与回退：读 [验收清单](references/acceptance.md)。
- 官方工具能力和待实测限制：读 [官方依据](references/sources.md)。

本 Skill Set 必须四个一起安装。共享辅助入口是本目录 `scripts/deploy.py`：

```sh
uv run /absolute/path/to/hw-supabase-deliver/scripts/deploy.py --config /customer/project/hwsupabase.yaml preflight
```

以下所有辅助命令使用同一入口和绝对配置路径。源代码仓库也支持 `uv run --extra obs hwsupabase ...`。

## 一次交付

1. 运行 `preflight` 和 `status`。前者仅本地检查；另以官方 KooCLI 只读命令确认账号项目、区域、资源归属、网络与工具版本。缺少凭据时给出环境变量名或官方交互配置入口，不让客户把秘密贴进聊天。
2. 为本次环境生成配置和资源清单，明确创建/复用、专享 APIG 持续费用、域名证书和缺失前提。沿用会话已确认的授权，不对每个常规步骤重复询问。
3. 确认当前工具能力：复用官方 DevKit 服务 Skills/工具，运行目标 API 的 `--help`/`--skeleton`。不要把 DevKit 的临时 `huawei-iac` 状态作为本项目的持久状态，也不要复制其沙箱优先选型去改变已选 OBS/FunctionGraph 架构。
4. 将本次官方操作写入工作流。使用 `plan workflow.yaml` 生成不含密钥的摘要，再按授权范围 `run workflow.yaml`。没有官方 API 的区域能力转为明确人工交接，不能编造接口或把步骤标成功。
5. 用独立 release ID 构建前后端，部署候选函数版本，完成候选链路验证。保存函数版本、APIG 脱敏快照、构建清单，通过 `register-release metadata.yaml` 登记。
6. 执行绑定该 release 的 `promote` 工作流：切换稳定函数别名、必要时发布 APIG，先上传前端资源再更新入口。执行真实生产地址的 `verify release cases.yaml`，成功后 `activate release promote-workflow-id`。
7. 输出访问地址、当前/上一版本、创建与复用的资源、验证证据及未完成项。`http-verified` 只表示自动 HTTP 用例通过，浏览器登录/Storage/RLS 未验证时不能称“完整生产验收通过”。

## 恢复

- `waiting`：运行原配置、原工作流 ID，继续观察；不要重建。
- `uncertain`/`in_flight`：只核对云端。探针找到预期资源可恢复 ID 并继续。仍无法确认时保留状态，报告实际阻点；确认请求未执行后才生成新的工作流 ID。
- 已完成步骤发生漂移：先解释差异，再生成新的修复工作流，不能静默覆盖共享资源。
- 新版本 promote 或 verify 失败：`rollback-plan --failed-promotion` 恢复最近验收通过的 current。撤回已成功激活的版本：`rollback-plan` 选择 previous。也可用 `--release <id>` 明确目标。
- rollback-plan 只输出历史信息。按其中版本和清单生成 `rollback` 工作流，执行后重新验证和激活；单改本地 `current` 不等于云端回退。

## 不变条件

配置、工作流、状态、日志只含密钥引用；运行期环境通过 FunctionGraph 受保护配置注入。前端只允许公开客户端 key。数据库连接数、数据迁移、RLS、Auth 与 Supabase Storage 元数据不随应用代码回退。

首次接入区域必须先跑 HTTP 契约样例。当前文档存在响应格式差异，未经实测不能承诺任意 Django 无改造运行；不要先实现一套 event-to-WSGI 框架。
