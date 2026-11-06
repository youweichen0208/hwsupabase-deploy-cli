# 资源准备顺序

官方服务工具作为实现，以下是交付依赖和必须回读的结果，不是固定地域的参数表。

| 顺序 | 操作 | 完成证据 |
|---|---|---|
| 1 | 查询已有 RDS Supabase、区域项目、VPC/子网/安全组 | 应用 ID、真实内外网 URL、资源归属 |
| 2 | 配置/复用 FunctionGraph 委托与必要网络规则 | 同区域 VPC；只放通需要的 Supabase/DB 端口 |
| 3 | 创建/复用私有制品桶、网站桶、可选 Storage 桶 | 桶归属/区域及权限符合预期 |
| 4 | 创建/复用 APIG 专享实例 | 实例 ID、异步 job ID、就绪状态和公网入口 |
| 5 | 部署函数，再配置分组、API、发布环境 | 函数 URN/版本、分组/API/环境 ID、发布结果 |
| 6 | 绑定域名证书并验证 DNS/TLS | 浏览器与 HTTP 检查使用正式域名成功 |
| 可选 | 将独立 OBS 桶绑定到已有 Supabase Storage | RDS 状态成功，Supabase Storage API 上传下载测试通过 |

## KooCLI 命令发现

```sh
hcloud FunctionGraph CreateFunction --help
hcloud FunctionGraph CreateFunction --skeleton
hcloud APIG CreateInstanceV2 --help
hcloud APIG CreateApiGroupV2 --help
hcloud APIG CreateApiV2 --help
hcloud APIG CreateOrDeletePublishRecordForApiV2 --help
hcloud RDS --help
hcloud obs help
hcloud obs help mb
```

FunctionGraph 代码部署优先 OBS URL 或明确的 base64 ZIP 内容；只给 code_filename 不代表上传完成。更新配置之前读取当前配置，保留业务已有环境项。

APIG CreateInstanceV2 的 subnet_id 文档指网络 ID，应从 VPC 子网记录映射，不可直接假设等于 FunctionGraph 的 subnet_id。创建返回 202/job_id 只是受理。公网模式随区域实现不同，避免写死已废弃 loadbalancer_provider。实例规格、可用区和公网入口要从当前官方元数据核验。

对于 API，使用 FunctionGraph 后端类型，检查当前 func_info 支持的版本/别名引用。覆盖根路由、深路径和实际业务方法；不要猜测通配语法，也不要只建一个 GET 路由便称整个 Django 已部署。发布环境使用真实环境 ID。

## RDS Supabase 可选配置

官方 SDK 源码已有 ShowSupabaseApplication、ModifySupabaseApplicationStorage、ModifySupabaseApplicationAuthConfig、SwitchSupabaseApplicationSsl 等能力。先检查已安装 KooCLI 是否公开对应操作以及区域是否支持；源码 main 的存在不等于客户区域已开放。可用则复用官方 API/SDK；不可用则明确控制台交接，保持检查点未完成。

Storage 配置需要独立桶和桶范围 AK/SK。不要把部署团队管理账号的广泛权限密钥交给应用。已配置时不更换底层桶；直接修改 OBS 内部对象会破坏 Storage 元数据。

Supabase SSL/EIP 变更需同时核对 Auth Site URL、API External URL、回调白名单。不要在增量更新时关闭已有邮箱/GitHub配置、重置 API key 或修改数据库密码。
