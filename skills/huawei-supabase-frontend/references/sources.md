# 官方资料与核实边界

维护日期：2026-11-06。执行时以目标站点/区域官方文档、API Explorer 和本地 CLI 帮助为准。此仓库交付操作指引，不包含生产部署证明。

| 资料 | 使用时机 |
| --- | --- |
| [KooCLI 概述](https://support.huaweicloud.com/intl/en-us/productdesc-hcli/hcli_01.html) | 工具安装与能力入口 |
| [JSON 参数输入](https://support.huaweicloud.com/usermanual-hcli/hcli_05_12.html) | 生成当前 API 请求文件 |
| [SSO](https://support.huaweicloud.com/usermanual-hcli/hcli_03_009.html)、[认证模式](https://support.huaweicloud.com/usermanual-hcli/hcli_05_10.html) | 认证准备；已有参数源自此前 7.3.12 帮助核对，本次未云端实测 |
| [中国站 API Explorer](https://console.huaweicloud.com/apiexplorer/)、[国际站 API Explorer](https://console-intl.huaweicloud.com/apiexplorer/) | 查询 OBS/RDS 服务终端节点、最新 API 与 schema |
| [OBS 默认域名预览限制](https://support.huaweicloud.com/usermanual-obs/obs_03_0342.html) | 缺少自有域名时说明网页下载限制 |
| [备案条件](https://support.huaweicloud.com/icprb-icp/icp_01_0008.html) | 检查首次备案的资源及身份条件 |
| [私有桶 CDN 接入](https://support.huaweicloud.com/usermanual-obs/obs_03_0600.html) | 私有桶回源、委托权限及加速范围 |
| [CDN URL 重写](https://support.huaweicloud.com/usermanual-cdn/cdn_01_0263.html) | 首页与限定 SPA 页面改写 |
| [CDN CLI v2](https://support.huaweicloud.com/intl/en-us/clir-cdn/CDN-cli_v2_en.html) | 核对版本化命令；目录检索确认 CreateRefreshTasks/v2，执行前仍需帮助核对 |
| [obsutil 上传](https://support.huaweicloud.com/utiltg-obs/obs_11_0013.html)、[对象元数据](https://support.huaweicloud.com/utiltg-obs/obs_11_0041.html) | 上传校验、MIME 与缓存元数据 |
| [RDS Supabase Data API](https://support.huaweicloud.com/usermanual-rds-pg/rds_supabase_23.html)、[Dashboard](https://support.huaweicloud.com/usermanual-rds-pg/rds_supabase_04.html) | 已有应用 SDK/RLS 与实际支持范围 |
| [Supabase API Keys](https://supabase.com/docs/guides/getting-started/api-keys) | 公开 Key 与服务端秘密的边界，华为云可用类型另验 |

本次通过官方页面/检索核对域名限制、备案条件、私有桶委托、CDN 改写、obsutil 元数据和 Key 类型。当前执行环境未找到 KooCLI/obsutil，因此未执行 CLI 帮助或云端请求。`ListAiApplications`、`ShowSupabaseApplication` 沿用任务提供的已核实命令名；本次公开文档搜索未返回可独立核对的对应参数页，所以仅提供帮助发现入口，不编造请求字段或声称已再次验证。

区域表保留历史名称解析，OBS/RDS 能力需逐次按实际账号确认。价格、配额、可备案资源资格及委托范围均在实施时查询；预算示例不代表报价或费用上限。
