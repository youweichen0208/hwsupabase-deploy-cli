# 内部 OBS 自定义域名发布与回退

仅在用户明确选择内部 OBS、提供实际 Endpoint 且授权目标桶、对象与访问范围时进入；缺项时继续构建和只读诊断，列出阻碍。公有云默认仍为 [私有 OBS＋CDN](hosting.md)，不因默认域名下载自动切换路线或开放桶。

## 已知现场与进入条件

[Issue #1](https://github.com/youweichen0208/hwsupabase-deploy-cli/issues/1) 报告：该内部环境默认域名 GET 对 HTML/JS/CSS/SVG 注入 `Content-Disposition: attachment`，HEAD 未显示；设置 inline、预签名及 path-style 均无效，默认域名根路径返回 ListObjects XML。绑定自定义域名后首页配置与资源访问正常。这是现场报告，不是所有 OBS 环境的统一特性；本仓库未访问客户环境。观察到此行为后停止反复尝试 inline/预签名/path-style 绕过，转向获授权的域名方案或报告入口缺项。

保留独立 OBS 配置，用 `-config="$FRONTEND_OBS_CONFIG"` 显式选择；配置内 Endpoint 必须与用户提供值一致。KooCLI profile 不等于 OBS 配置；不运行默认 DevKit 初始化/同步覆盖内部 Endpoint，不将管理 Endpoint 替换成网页域名。凭证通过用户终端配置，配置及备份在项目外限制访问，不记录秘密。先查看 `hcloud obs help` 及相关子命令帮助，确认工具版本和目标环境支持；权限/参数失败先纠正，不重复尝试变更。

## 配置与发布顺序

1. **核实与快照。** 只读确认专用前端桶的归属、Endpoint、现有网站配置、桶策略、对象 ACL、域名绑定和适用 DNS/证书配置；将配置快照及原入口字节/元数据保存在 web root 外。确认不含用户上传或私密数据，记录本次差异与恢复范围。不能将现有私有桶自动改为公共读；若必须扩大访问范围而未获授权，停止该变更。
2. **网站与权限。** 按当前工具帮助/目标 API 配置网站首页（如 index.html）和真实错误文档（如 404.html），保存原配置。按已授权范围设置必要读取策略及目标环境要求的逐对象 ACL，仅限前端产物；不授予匿名写入或无关对象读取，不以全桶公共读代替最小范围。若环境只能提供更宽权限，列明限制，等待该范围授权。确认实际读取者能读前端资源且授权外对象仍不可读。
3. **上传与切换。** 使用唯一版本/内容哈希资源路径，清单包含 HTML、JS/CSS、图片、字体、动态 import、错误页及可变文件；仅上传清单对象，每条 OBS 命令显式选择独立配置。先上传资源，核对大小、SHA-256 与 MIME/缓存元数据（分段 ETag 不当作 MD5），确认依赖可读再更新入口。HTML/service worker 短缓存或重新验证，不可变资源长缓存。切换前复核远端入口仍等于快照，发现并发发布先对账；多页面不声称原子切换。
4. **绑定域名。** 先查询已有绑定，核实域名控制权和本次授权，再执行下节 put 并用 get 确认结果。按目标环境返回/文档确认实际 DNS 目标，不拼接公有云后缀。保留无关 DNS 记录，记录 TTL 与配置状态。证书参数、格式、HTTPS 支持及部署位置按目标环境核对；帮助中出现 `-certificate` 不代表内部 HTTPS 已实测可用。私钥不写入记录，不在聊天或命令示例中填真实内容。
5. **验收与记录。** 按 [通用 GET 与浏览器验收](deployment.md) 检查首页、实际资源、缓存、负面路径及适用 Supabase 功能。无 CDN 改写时逐一验收 SPA 深层直接访问、刷新和带查询的回调；深链 404 即该项失败并报告限制，不自动改成哈希路由或全站首页回退。仅全部适用验收通过才更新成功版本；schema_version=2、hosting_kind=obs-custom-domain，不填虚构 CDN ID 或刷新任务。

## 域名命令与诊断

KooCLI 7.3.12 的 `hcloud obs help custom-domain` 已核实遗漏必需的 `-method`，只传 `-cname` 会报 Invalid args；put/get/delete 必须显式指定。以下参数在无网络隔离环境通过解析，**不代表真实云调用成功**；执行时复核实际版本。命令依据见 [官方资料](sources.md#内部-obs-自定义域名与-get-验收)。变量必须来自已核实环境：

```sh
hcloud obs custom-domain "obs://$FRONTEND_BUCKET" -method=get \
  -config="$FRONTEND_OBS_CONFIG"
hcloud obs custom-domain "obs://$FRONTEND_BUCKET" -method=put \
  -cname="$FRONTEND_DOMAIN" -config="$FRONTEND_OBS_CONFIG"
```

DNS 就绪前可用已核实的 OBS IP 诊断 Host 路由，以下为 HTTP 示例；同样核对最终响应头、正文和 URL，并用实际资源路径重复检查：

```sh
curl --silent --show-error --location --max-redirs 5 --max-time 30 \
  --resolve "$FRONTEND_DOMAIN:80:$FRONTEND_OBS_IP" \
  --dump-header "$CHECK_DIR/resolve-headers.txt" --output "$CHECK_DIR/resolve-body.bin" \
  --write-out 'method=GET status=%{http_code} final_url=%{url_effective}\n' \
  "http://$FRONTEND_DOMAIN/"
```

PowerShell 使用 `curl.exe`。HTTPS 诊断使用对应 443 映射与 https URL，保持证书校验；跳转到不同域名/端口需另行核实，80 映射不证明 443 可用。`--resolve` 只证明指定 IP/Host 的诊断链路；正常 DNS、目标用户网络访问及适用 HTTPS 验收完成前，只报告“诊断通过”，不能报告上线。HTTP 调试不输入真实登录凭证。

## 更新、失败恢复与清理

更新沿用以上资源先上传、入口后切换顺序，保留上个成功版本及旧页面依赖；该路线没有 CDN 时无需 CDN 刷新，按实际缓存策略验证普通 URL 和 service worker。

请求超时先查询绑定/配置和远端字节，判断实际状态再恢复；入口切换前失败不影响原入口。切换后失败或显式回退，在已有恢复授权内恢复归档入口、元数据及本次改动的网站/权限/域名/DNS/证书配置，保留无关配置并重新 GET 与浏览器验收。使用原产物，不重新构建旧源码；旧 HEAD 证据不足时补验。首次部署无旧版本时按快照恢复部署前状态，不宣称回退到已验证版本。恢复失败记录实际服务版本、最近成功版本与未完成项。

仅在域名绑定属于本次临时测试且删除获授权、无共享依赖时执行：

```sh
hcloud obs custom-domain "obs://$FRONTEND_BUCKET" -method=delete \
  -cname="$FRONTEND_DOMAIN" -config="$FRONTEND_OBS_CONFIG"
hcloud obs custom-domain "obs://$FRONTEND_BUCKET" -method=get \
  -config="$FRONTEND_OBS_CONFIG"
```

复用绑定不能进入临时清理；本次 DNS/权限变更按快照恢复，不删除整个共享策略。资源清理另按保留期限与授权，保留旧页面仍引用的对象。
