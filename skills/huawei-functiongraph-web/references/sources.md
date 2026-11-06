# 官方资料与核实边界

查阅日期：2026-11-06。此 skill 是操作指引，未附带云端实测背书。执行时优先当前区域文档、API Explorer 和本地 KooCLI 帮助；不同站点/区域及旧示例可能不一致。

| 资料 | 用途 |
| --- | --- |
| [KooCLI 概述](https://support.huaweicloud.com/intl/en-us/productdesc-hcli/hcli_01.html) | 安装入口与 API 工具定位 |
| [FunctionGraph CLI 操作参考](https://support.huaweicloud.com/intl/en-us/clir-functiongraph/en-us_topic_0000002707402298.html) | 发现函数、触发器、版本等命令 |
| [JSON 参数输入](https://support.huaweicloud.com/usermanual-hcli/hcli_05_12.html) | 请求文件格式 |
| [JSON 输入注意事项](https://support.huaweicloud.com/hcli_faq/hcli_19_004.html) | 请求位置、5 MB 上限和参数混用限制 |
| [创建 HTTP 函数](https://support.huaweicloud.com/usermanual-functiongraph/functiongraph_01_1442.html) | bootstrap、语言路径、打包与 HTTP 服务 |
| [创建函数 API](https://support.huaweicloud.com/api-functiongraph/functiongraph_06_0108.html) | HTTP runtime、代码来源及参数 |
| [生命周期 API](https://support.huaweicloud.com/api-functiongraph/FunctionLifecycleManagement.html) | 更新、查询、URL 等操作入口 |
| [创建函数 URL](https://support.huaweicloud.com/api-functiongraph/functiongraph_06_1706.html) | URL 与鉴权参数；区域可用性另验 |
| [APIG 专享版触发器](https://support.huaweicloud.com/usermanual-functiongraph/functiongraph_01_0204.html) | 网关入口配置 |
| [RDS Supabase 创建应用](https://support.huaweicloud.com/usermanual-rds-pg/rds_supabase_02.html) | 产品创建路径和约束 |
| [RDS Supabase Dashboard](https://support.huaweicloud.com/usermanual-rds-pg/rds_supabase_04.html) | 功能差异及 Edge Functions 限制 |
| [RDS Supabase Data API](https://support.huaweicloud.com/usermanual-rds-pg/rds_supabase_23.html) | SDK 接入、RLS |
| [RDS Supabase MCP](https://support.huaweicloud.com/intl/en-us/usermanual-rds-pg/rds_supabase_18.html) | 已有应用的官方工具集 |

Flask、Express、Django 的适配是本 skill 的应用层指导，不代表已经确认三个同名官方模板在所有区域都存在。模板 ID、可用语言版本、函数 URL 可用性和完整 Supabase 资源创建命令均需执行时发现。

APIG 实例筛选、按需购买、公网入口及 API 发布的专门流程与官方依据见 [APIG 复用与自动开通](apig.md)。

自然语言区域解析使用 [区域名称与 region ID](regions.md)，内含官方来源、核实日期及歧义处理规则。
