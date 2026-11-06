# 官方依据与兼容边界

调研日期：2026-11-06。以下是官方文档/源码核验，不能替代目标账号与区域实测。

| 能力 | 官方来源 | 交付影响 |
|---|---|---|
| 官方服务 Skills 与工具 | [HuaweiCloud DevKit](https://github.com/huaweicloud/huaweicloud-devkit) | 复用 FunctionGraph/APIG/OBS/IAM/VPC，不另造云 SDK |
| 通用 IaC 状态 | [huawei-iac](https://github.com/huaweicloud/huaweicloud-devkit/blob/main/plugins/huaweicloud-core/skills/huawei-iac/SKILL.md) | 上游明确会话级状态；本项目补跨会话记录 |
| OBS 配置缺口与独立凭据 | [huawei-obs](https://github.com/huaweicloud/huaweicloud-devkit/blob/main/plugins/huaweicloud-core/skills/huawei-obs/SKILL.md) | obsutil 不覆盖网站/CORS；不能把 hcloud profile 当作 OBS 配置 |
| KooCLI JSON 参数 | [cli-jsonInput](https://support.huaweicloud.com/eu/hcli_faq/hcli_19_004.html) | 必须使用 path/query/body 等分区，不能把任意 JSON 当请求 |
| OBS 独立配置 | [config 命令](https://support.huaweicloud.com/intl/en-us/utiltg-obs/obs_11_0023.html) | 每个客户用 -config 指定文件 |
| HTTP 函数 | [创建 HTTP 函数](https://support.huaweicloud.com/usermanual-functiongraph/functiongraph_01_1442.html) | bootstrap/Web server 模式；存在文档响应格式差异，先契约测试 |
| Python 依赖构建 | [依赖包](https://support.huaweicloud.com/devg-functiongraph/functiongraph_02_0616.html) | Linux/Python/架构匹配，不能打包 macOS venv |
| 官方 Django 模板 | [应用中心](https://support.huaweicloud.com/intl/en-us/usermanual-functiongraph/functiongraph_01_0377.html) | 作为验证参考，模板可用区域需查询 |
| 函数代码输入 | [CreateFunction](https://support.huaweicloud.com/api-functiongraph/functiongraph_06_0108.html) | ZIP 内容/OBS URL 与文件名不同，回查 code_size/digest |
| APIG 专享实例 | [实例说明](https://support.huaweicloud.com/usermanual-apig/apig_03_0001.html)、[CreateInstanceV2](https://support.huaweicloud.com/api-apig/CreateInstanceV2.html) | 新部署使用专享，异步就绪；subnet_id 是网络 ID |
| APIG 费用 | [计费](https://support.huaweicloud.com/price-apig/apig_08_0003.html) | 有持续费用，公网入口另算 |
| RDS Supabase 网络 | [准备工作](https://support.huaweicloud.com/usermanual-rds-pg/rds_supabase_22.html) | 8443、内外网区分、SSL 与 EIP/Auth 关系 |
| RDS Supabase 文件 | [Storage](https://support.huaweicloud.com/usermanual-rds-pg/rds_supabase_28.html) | OBS 为底层；禁止绕过 Storage 修改对象 |
| OBS HTTPS | [HTTPS 支持](https://support.huaweicloud.com/obs_faq/obs_03_0071.html) | 自定义域名证书托管，CDN 可选 |
| RDS 公共 SDK | [Python SDK](https://github.com/huaweicloud/huaweicloud-sdk-python-v3) | Supabase 配置操作可发现；main 不保证客户区域/已装版可用 |
| 现有函数部署工具 | [Serverless Devs](https://support.huaweicloud.com/devg-functiongraph/functiongraph_02_0701.html) | 可用但不作为首版完整基础设施状态引擎 |

每次正式交付保存所用 KooCLI 版本、DevKit 版本/提交、OBS SDK 版本及 Python 构建镜像 digest。未实际验证的版本只能标为候选，不能生成“兼容认证”记录。升级时重跑 HTTP 契约和续跑/回退测试。
