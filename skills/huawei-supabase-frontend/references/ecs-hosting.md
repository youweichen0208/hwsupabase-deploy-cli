# ECS＋EIP＋Nginx 静态前端

仅在用户选择服务器托管时使用。此路线提供准备环境、静态发布、更新和回退，不因无域名自动购买，也不承担 SSR/API 服务部署。公共记录及完成标准见 [发布与验收](deployment.md)，后端接入见 [Supabase](supabase.md)。

## 1. 发现并准备资源

已有主机、应用目录与入口明确，且仅更新/回退站点文件时，可通过现有 SSH、记录和真实入口核实目标，直接执行第 2–4 节；不为此强制配置新的 KooCLI/IAM 认证。需要创建/查询云资源、绑定 EIP 或变更安全组时才执行本节云侧发现。

先读取环境记录、已有 SSH 别名和用户指定 ECS；SSH 身份与 KooCLI 账号是两种认证，不能互相替代。只读取必要配置，不输出私钥或整份云配置。用官方命令帮助核实当前 schema：

```sh
hcloud ECS ListServersDetails --help
hcloud ECS ShowServer --help
hcloud ECS CreatePostPaidServers --help
hcloud ECS ShowJob --help
hcloud EIP ListPublicips/v2 --help
hcloud EIP CreatePublicip/v2 --help
hcloud EIP UpdatePublicip/v2 --help
hcloud EIP ShowPublicip/v2 --help
```

查询带选定 profile/region，按帮助读取所有页。核实实例归属、状态、Linux 发行版、CPU/内存/磁盘余量、现有站点与监听端口、VPC/子网/安全组、已绑定 EIP 和 SSH 访问条件。多个候选无法确定时询问；已有实例不可达先诊断，不直接购买替代品。

没有适用实例时，先生成具体资源请求和费用计划：区域/AZ、实际可售规格、维护中的 Linux 镜像、系统盘、密钥对、VPC/子网/安全组、EIP 线路、按流量或固定带宽计费、预算和恢复/清理策略。包周期与按需分别核实，不能用新客年价作为长期月价。约 300 元/月是前端预算目标；OBS/CDN、ECS/磁盘/EIP、后端公网及域名/证书独立估算，按实际产品支持配置费用和用量告警，不视为硬限额。

已有授权覆盖这些资源时执行；否则只就缺少授权确认。使用当前官方 schema 生成 KooCLI JSON 请求，数量为一台；VPC、镜像、可用区、规格和密钥名称都从真实查询取得。选按需时用 CreatePostPaidServers；已授权包周期时核实对应创建 API 的计费字段。EIP 单独创建/复用时，ECS 请求中不同时自动购买另一 EIP。

创建成功立即记录 job/server ID，以 ShowJob 和 ShowServer 核实完成。查询默认每 15–30 秒一次、最多 30 分钟；失败或超时保留 ID 下次续查。返回不明先按本次请求记录查询任务及资源，不重发购买；名称不是唯一幂等键。

EIP 通过网卡端口绑定：查询 ECS 对应主网卡的实际 port ID、所属区域及租户，按 UpdatePublicip/v2 的当前 schema 更新；不是把 server ID 当 port_id，更不是绑定 OBS。已有 EIP 属于别的实例时不抢占。绑定后 ShowPublicip/v2 与 ECS 信息双向核对，再记录实际公网 IP。

在授权范围内配置应用端口（通常 80/443），SSH 限定管理来源；同时检查系统防火墙。保留共享安全组及其他服务，不开放数据库端口作为浏览器接入方式。首次 SSH 主机指纹通过可信渠道核实，保留主机密钥校验；不使用 StrictHostKeyChecking=no。缺少管理入口时让用户完成密钥/堡垒机等前置配置。

完成条件：实例、绑定、SSH 和目标站点端口均已核实；仅创建成功不算环境就绪。

## 2. 准备站点和路由

检查系统包管理器及现有 Nginx；缺失时在授权内使用发行版官方仓库安装，不覆盖其他站点、不执行无来源安装脚本。本地按锁文件构建，只将已扫描的静态产物上传。构建配置、源码、`.env`、SSH 密钥和发布清单不放 web root。

复用已有目录；新站点采用 `/srv/frontend/<应用>/`，应用名使用经过验证的单段目录名。站点目录约定：

- `releases/<版本>/site/`：完整构建归档；`current` 指向当前版本的 site。
- `static/releases/<版本>/`：按清单发布的不可变公开资源；URL 为 `/releases/<版本>/...`，独立于 current，切换后旧资源仍可访问。
- `private/`：配置快照、清单和恢复信息，Nginx 不映射此目录。

首次采用此布局时，先盘点当前线上 HTML/CSS/懒加载引用的真实旧资源 URL。旧版若使用 `/assets/<hash>` 等路径，必须在切换前保留其原 URL：复用已有共享哈希资源目录，或把保留期内旧文件按原路径合并到每个候选 site。不能仅保留旧 release 目录却让旧 URL 落到新 current 后 404。同一旧 URL 对应不同字节时停止，先制定可兼容的版本化/过渡方案；回退也要保证新页面的已发布资源仍可取到。

发布用户拥有这些目录，Nginx 仅需读取权限。所有层级限制到本应用，不能使用宽泛 chmod 777 或修改整个 /srv。构建器的资源 base 指向版本前缀，页面 router basename 仍是实际站点路径；不能仅搬移文件而不检查动态 import、CSS 图片和 public 资源的 URL。

下面是 HTTP 连通验证的 **server 块示例**，安装到已确认会被 http 块包含的站点配置文件，使用全局 MIME 映射。替换示例 IP、目录和页面路由；已有站点只合并必要配置，不能删除默认站点来抢占流量。

```nginx
server {
    listen 80;
    server_name 203.0.113.10;
    root /srv/frontend/app/current;
    index index.html;
    autoindex off;
    open_file_cache off;

    location = /api { return 404; }
    location ^~ /api/ { return 404; }
    location ~ /\. { return 404; }

    # 正则顺序：文件与资源优先，页面规则只匹配真实路由。
    location ~ ^/releases/ {
        root /srv/frontend/app/static;
        try_files $uri =404;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }
    location ~* \.(js|mjs|css|map|png|jpg|jpeg|svg|ico|webp|woff|woff2)$ {
        try_files $uri =404;
        add_header Cache-Control "no-cache";
    }
    location = / {
        rewrite ^ /index.html last;
    }
    location = /index.html {
        try_files $uri =404;
        add_header Cache-Control "no-cache";
    }
    location ~ ^/(login|auth/callback|projects/[A-Za-z0-9_-]+)$ {
        rewrite ^ /index.html last;
    }
    location / {
        try_files $uri =404;
        add_header Cache-Control "no-cache";
    }
}
```

资源路径不依赖宽泛的 404→首页规则。多页静态导出改用逐页映射；已有 `/api` 代理若属本应用且仍需使用，保留明确已知路由，仅未知 API 返回错误。未知路径、缺失 JS/CSS 和点文件都不得返回入口 HTML。若已有证书验证目录例外，仅放行该目录和实际验证文件。

HTTP IP 可用于明确要求的页面连通调试；HTTPS 正式入口必须有可信且覆盖实际 IP 的证书、完整链和续期方式，按当前 CA 能力核实，不能承诺任意免费域名证书可用于 IP。不使用自签名或忽略证书错误宣称 HTTPS 成功。配置 TLS 后先验证证书和应用，再启用适用的 HTTP 跳转。没有合适证书时报告“HTTP 页面可达、HTTPS/Auth 未验收”，不在明文页面测试真实登录；后续域名是用户选择，不能自动购买。

## 3. 发布与更新

1. 保存当前 current 的真实目标、配置、入口摘要及成功版本；检查磁盘容量，获取本应用独占发布锁。切换前再次比较 current，防止覆盖并发发布。
2. 经 SSH 上传到本次独立暂存目录；若用归档，先检查无绝对路径、`..` 逃逸或越界符号链接。按 manifest 核对大小、SHA-256、入口及引用，完成后移入版本目录；不可变 URL 已存在但内容不同则停止。禁止 `rsync --delete` 清理共享目录或旧版本。
3. 先上传并验证 static 中的全部版本资源，再安装/更新经过备份的站点配置。使用完整有效配置执行 `nginx -t`，失败则恢复配置文件、保留旧运行配置和 current；成功才做受控 reload。首次无 current 时先将候选站点限制在本地测试端口，验证后启用公网站点。
4. 在 Linux 同一文件系统下创建临时符号链接，再以原子 rename 替换 current；不要先删除 current 再创建。切换后检测首页、深层路由、带查询回调、真实资源、缺失资源与未知 API，并验证旧版本资源仍在。若有共享 CDN/代理按既有发布机制处理缓存；没有 CDN 不调用 OBS/CDN API。
5. 入口、资源、缓存及适用的 Supabase 检查全部通过才记录成功。HTTP-only 调试仍保留 HTTPS/Auth 未完成状态，不能提升为完整生产成功版本。

## 4. 回退与中断恢复

回退前确认目标版本已验证、归档资源齐备、当前后端兼容。持有同一发布锁，核对远端 current 未被别人更新；必要时恢复配套 Nginx 配置并 `nginx -t`，原子切回指定 site 后受控 reload，重新验收。无需配置变更时只切链接；open_file_cache 或其他文件缓存若由现有配置启用，按其失效机制清除。

上传失败不切换。reload 失败时检查当前运行配置，恢复配置与旧链接后验证；请求超时或 SSH 断开先读取实际链接/服务状态再恢复，不能假定回退已完成。首次发布没有成功版本时恢复本次变更前的站点状态，说明没有可用回退点。

报告仍存在且可能计费的 ECS、EIP、磁盘等资源。仅按已授权清理策略删除本次新建且无共享依赖的资源，逐项核实；服务器停机不代表磁盘/EIP停止计费。保留旧页面引用的资源，清理另定期限。

依据：[ECS CLI](https://support.huaweicloud.com/clir-ecs/ecs_cli_02.html)、[EIP CLI v2](https://support.huaweicloud.com/intl/zh-cn/clir-eip/EIP-cli_v2.html)、[EIP 绑定](https://support.huaweicloud.com/usermanual-eip/eip_0009.html)、[Nginx location 与 try_files](https://nginx.org/en/docs/http/ngx_http_core_module.html)、[Nginx 配置重载](https://nginx.org/en/docs/beginners_guide.html)。
