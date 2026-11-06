# 华为云 FunctionGraph Web 部署 Skill

通过 AI agent 创建或部署 Flask、Express、Django 项目，优先使用官方 KooCLI 管理 FunctionGraph 和 APIG。React/Vue 静态构建产物可由 Express 托管；按需接入已有华为云 RDS Supabase。

## 功能

- 识别已有项目，或使用适用的官方模板及框架脚手架创建项目。
- 准备 HTTP 函数启动文件、依赖和部署包，执行创建、更新与回退。
- 优先复用现有 APIG；缺少合适实例时，在购买授权范围内按需开通，配置入口并发布 API。
- 检查页面、静态资源、深层路由及应用接口，记录实际部署结果。

## 安装与使用

将 [skills/huawei-functiongraph-web](skills/huawei-functiongraph-web) 整个目录复制到 agent 的 skills 目录中。保留 `references` 和 `agents` 子目录。已有同名安装时先检查版本，再更新。

调用示例：

```text
$huawei-functiongraph-web 将当前 Express 项目部署到华为云 FunctionGraph，优先复用已有 APIG。
```

```text
$huawei-functiongraph-web 创建一个 Flask 项目，并连接已有 RDS Supabase。
```

部署需要安装官方 KooCLI，并安全配置具有相应权限的 AK/SK 和目标区域。Skill 优先复用 KooCLI 自动获取 project ID，查询现有函数、APIG 和网络资源；首次创建返回的 ID 和访问地址自动记录，无需预填。已有有效认证配置可直接使用，临时凭证还需安全令牌。仅在资源选择有歧义、自动发现受阻或操作超出已有授权时询问。真实凭证不写入仓库或聊天。

## 指引

| 文件 | 内容 |
| --- | --- |
| [SKILL.md](skills/huawei-functiongraph-web/SKILL.md) | 工作流与工具选择 |
| [框架适配](skills/huawei-functiongraph-web/references/frameworks.md) | Flask、Express、Django 打包和启动 |
| [部署与回退](skills/huawei-functiongraph-web/references/deployment.md) | KooCLI 参数、函数部署和验收 |
| [APIG 自动开通](skills/huawei-functiongraph-web/references/apig.md) | 实例复用、按需购买、入口、发布及失败恢复 |
| [Supabase 对接](skills/huawei-functiongraph-web/references/supabase.md) | 已有后端的 SDK、网络和权限配置 |
| [区域映射](skills/huawei-functiongraph-web/references/regions.md) | 中国站/国际站区域名称、region ID 和不支持提示规则 |
| [官方资料](skills/huawei-functiongraph-web/references/sources.md) | 文档来源与核实边界 |

## 验证状态

本仓库交付的是由 agent 执行的 skill 指引，复用官方 CLI，不包含独立部署程序。Skill 格式、文档引用、JSON 示例及 shell 语法已检查；真实云端购买、部署及业务验收尚未完成。
