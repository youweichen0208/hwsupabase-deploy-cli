# GET 验收与历史验证记录

当前 skill 已按用户要求移除内部 OBS 专属流程；以下保留原始验证范围与结果，域名命令检查仅为历史记录，不代表当前支持路线。

验证日期：2026-11-07。交付为 Issue #1 的 skill 修复，不是客户内部站点修复；未连接真实云环境，未修改客户权限、桶、DNS 或证书。

## 本地 HTTP 模拟

执行 `/usr/bin/python3 tests/obs-get-regression.py`，14 项检查通过。脚本启动回环 HTTP 服务，使用真实 curl 保存跳转链响应头、最终 URL 与正文，并按通用验收要求断言样例结果；不作为完整网站验收程序，不代替浏览器。

| 场景 | 观察与结论 |
| --- | --- |
| 正常 HTML、JS、CSS、SVG（4 项） | GET 200，最终 MIME 与内容匹配，无附件；仅本地 HTTP 通过 |
| HEAD 正常（1 项） | 无 Content-Disposition，复现旧验收盲点 |
| GET 附件、跳转后附件（2 项） | 最终响应含 attachment，均应判失败；跳转最终 URL 指向附件 |
| 根路径 XML（1 项） | 200 + ListBucketResult，不可判首页通过 |
| 错误 MIME、200 错误页（2 项） | 分别按类型或实际正文拒绝，200 不足以证明可用 |
| 缺失资源、未知 API、SPA 深链（3 项） | 前两项 404 且非首页符合负面路径；SPA 深链 404 必须报告路由失败 |
| resolve 与正常 DNS（1 项） | 指定 IP/Host 成功；保留域名 site.invalid 正常解析失败（curl 6），只能记诊断通过 |

未执行客户应用的浏览器、TLS、Auth、跨用户隔离或实际云回退。PowerShell 示例已静态核对使用 curl.exe，本环境未执行 Windows。

## KooCLI 隔离解析

复用此前认证验证下载的官方 KooCLI **7.3.12 Linux arm64**，Docker `node:22-bookworm-slim`、`--network none`；仅只读挂载工具目录，容器临时用户目录，无客户配置。容器内接受测试工具隐私交互，使用虚构 AK/SK，独立配置 Endpoint 为 `http://127.0.0.1:9`（无监听服务）、重试 0。未安装本机工具，未发出真实云变更。

| 命令 | 实际结果 |
| --- | --- |
| `hcloud obs help custom-domain` | Syntax/Options 列出 cname 和证书参数，但遗漏 method |
| `custom-domain obs://test-bucket -cname=site.invalid -config=...` | Invalid args，拒绝缺少 method |
| 加 `-method=put` | 通过解析，尝试 PUT `/test-bucket?customdomain=site.invalid`；回环连接拒绝 |
| 加 `-method=get` | 通过解析，尝试 GET `/test-bucket?customdomain`；回环连接拒绝 |
| 加 `-method=delete` | 通过解析，尝试 DELETE `/test-bucket?customdomain=site.invalid`；回环连接拒绝 |

后三项仅证明参数解析到正确 HTTP 操作，退出失败来自隔离端点拒绝连接，不是绑定/读取/删除成功。生产示例 get 不传多余 cname。证书配置和 HTTPS 均未实测。

## 文档检查与来源边界

88 个 Markdown 本地链接目标、15 个 shell 代码块语法及 git diff 空白检查通过；核对路线入口、独立配置、发布/回退、记录兼容和 CDN 适用范围。GET 留证只保存脱敏摘要；旧 HEAD 记录保留但下次补验。

[Issue #1](https://github.com/youweichen0208/hwsupabase-deploy-cli/issues/1) 提供内部附件注入与绑定后表现的现场报告；本地模拟仅复现关键响应差异。官方依据见 [sources.md](../skills/huawei-supabase-frontend/references/sources.md#get-验收)。两者均不能代替目标内部环境的网站、权限、域名、DNS、证书和浏览器实测。
