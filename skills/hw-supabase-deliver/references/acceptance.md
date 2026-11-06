# 验收与交付证据

## 验证层级

1. **本地工具测试**：测试的是配置、状态、命令构造、构建/探针行为，不能证明云上可用。
2. **真实 HTTP 验证**：真实域名、APIG、函数与 Supabase 的响应符合用例。`verify` 结果绑定配置摘要和工作流状态；后续工作流变化会使报告过期。
3. **业务验收**：浏览器登录与回调、RLS、Storage、真实项目业务路径。通过自动 smoke checks 不代表这一层已完成。

## 首次区域 HTTP 契约

在临时测试函数中启用 `CONTRACT_TESTS=1`，使用安装包中的 Flask/Django 样例和 `http-contract.yaml`。测试完成关闭或移除测试路由。不要向生产业务函数注入 echo 端点。

验证 GET/POST、根与深层路径、原始 body、重复查询参数、二进制 SHA256、4xx 原样返回、302 Location、多 Set-Cookie。比较浏览器/HTTP 客户端收到的内容，防止错误地把 JSON 封套当作框架原始响应。现有样例 echo 校验 body；重复查询参数还需添加客户实际路由的断言。

检查 APIG 的 Authorization 透传、OPTIONS/CORS、允许的方法、超时，以及函数 alias/固定版本引用。先执行无登录与错误 token 的 401，再使用临时测试用户的有效 token 测试 /me；不要用 service key 替代用户 token。

## 完整应用

| 路径 | 必须观察到 |
|---|---|
| 浏览器 → OBS | HTTPS 展示 HTML、资源 MIME 正确、缓存行为符合版本策略、深链接刷新与缺失资源正确 |
| 浏览器 → APIG → 函数 | 实际版本响应、业务路径、身份验证、CORS/OPTIONS、Cookie/redirect |
| 函数 → Supabase 内网 | 真实内网 URL 可达，协议/证书正确，不靠开放全部安全组绕过 |
| 浏览器 → Supabase | 公网 HTTPS、Auth 回调、使用用户身份的 Data API/RLS 隔离 |
| Supabase Storage → OBS | 通过 Storage API 上传/下载/删除测试对象，元数据一致 |
| 发布 → 回退 | 新版本成功；切回旧函数及旧前端后仍可访问，无数据库自动回滚 |

`verify release cases.yaml` 支持 status、完整 body、contains、SHA256、精确 header、header_counts；不自动跟随重定向、不忽略 TLS 错误、不打印响应正文。每个启用的 web/api profile 和 supabase 都需有通过的用例。

每个启用的 web/api 类别还必须有 release 断言：`expect.release: {header: X-HWSupabase-Release}` 或 `{json_path: release}`，实际返回值必须等于待验收 release。仅旧版仍返回 200 不会通过新发布验收。示例函数需注入 `HWSUPABASE_RELEASE`，前端 config.json 包含 build 时的 release；客户项目也可使用自己的版本端点/头。

只有公网 URL 的健康检查无法证明函数内网链路，需部署一个权限受控的业务探针或通过真实业务请求验证。

用 `$env` 引用测试用户 Authorization 字符串（含 Bearer 前缀），不将 token 写入用例。主动写业务数据的测试必须使用客户指定测试用户、测试表或测试桶并清理测试对象。

## 交付报告

记录客户/环境、区域、工具版本、资源 ID 与创建/复用归属、函数实际代码摘要/版本、APIG 环境、网站/Supabase 地址、当前/上一 release、每项真实检查的时间和结果。

未完成的 DNS、证书、公测能力、内网检查、框架契约或业务验收逐项列出，不通过“已创建资源”掩盖。报告不包含 AK/SK、数据库连接串、认证 token 或完整云 API 响应。
