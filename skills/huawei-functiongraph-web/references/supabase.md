# 可选：接入已有 RDS Supabase

## 确定连接方式

先读取应用现有配置，确认 Supabase URL、客户端 anon key 的安全来源及所需能力。不要将 Supabase Cloud 的项目创建、管理 API 或 Edge Functions 发布流程直接用于华为云。

- 浏览器访问 Data API/Auth/Storage：复用对应 Supabase SDK，使用浏览器可达且证书有效的 HTTPS 地址；anon key 不是绕过 RLS 的授权。
- Flask/Express/Django 服务端使用 SDK：遵循当前用户会话；只有明确需要管理员操作时才使用服务端 service_role。
- Django ORM 或其他数据库直连：需要 PostgreSQL 地址、端口、数据库、账号、密码及连接加密配置，与 Supabase HTTP URL/API key 分开管理。直接数据库角色的权限和 RLS 行为须独立检查。

service_role、数据库密码、云 AK/SK 只能位于服务端秘密配置，不能进入前端环境变量、构建产物或部署报告。Supabase Auth、表授权及 RLS 按应用需求配置，不能为连通性测试关闭 RLS。

## 网络与发布域名

浏览器直连需要浏览器能到达 Supabase；仅让 FunctionGraph 与 Supabase VPC 互通不能解决浏览器访问。服务端访问则检查 FunctionGraph 实际网络、DNS、安全组和出口。沿用已有可用地址，不默认购买 EIP/NAT 或开放数据库公网。

拿到部署域名后，按需更新 Auth Site URL/回调允许列表及 CORS。静态前端的公开变量通常在构建时写入，改函数环境变量后需判断是否重新构建。HTTPS 页面应调用有效 HTTPS 后端，避免混合内容。

## 官方能力复用

华为云提供 Supabase SDK 与 MCP 对接文档。已配置官方 MCP 时，可在授权范围内复用库表查询、SQL 和其他已支持工具；缺少 MCP 不自动安装或复制自制管理客户端。

当前检索到的创建应用文档走 RDS 控制台，尚未验证完整 KooCLI 创建 Supabase 应用链路。只有用户要求创建后端时才继续核实当前公开 API 与区域支持；普通 RDS CreateInstance 不等同于创建 Supabase 应用。缺少公开 API 时说明具体人工步骤，不抓取未公开控制台接口。

华为云 Dashboard 文档当前注明不支持 Edge Functions；业务函数可部署到 FunctionGraph。执行时复核该限制是否改变。

验收按实际业务检查登录/退出、数据读取和授权隔离；写操作或迁移需在已有授权范围内使用指定测试对象。无需后端的前端项目直接跳过本节。

依据：[Data API](https://support.huaweicloud.com/usermanual-rds-pg/rds_supabase_23.html)、[Dashboard 限制](https://support.huaweicloud.com/usermanual-rds-pg/rds_supabase_04.html)、[创建应用](https://support.huaweicloud.com/usermanual-rds-pg/rds_supabase_02.html)、[MCP 对接](https://support.huaweicloud.com/intl/en-us/usermanual-rds-pg/rds_supabase_18.html)。
