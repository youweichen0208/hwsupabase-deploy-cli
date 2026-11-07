# Docker 构建与 ECS 静态托管

用户选择 Docker 或维护已有容器部署时读取。构建版本判断见 [构建环境](build-environment.md)；ECS/EIP/SSH、静态路由、资源保留与原子发布约定见 [ECS 发布](ecs-hosting.md)。Docker 是可选方式，不因为工具缺失自动迁移现有宿主机 Nginx，也不引入 SSR/API 服务。

## 安装和识别

先查询目标 Docker context/daemon，确保操作在预期主机；ECS 通过已核实的 SSH 管理，不开放 Docker TCP 管理端口。检查 Linux 发行版/版本、架构、磁盘、已有 Docker/Compose、容器及端口占用。macOS/Windows 构建端复用已有受支持 Docker 环境；需要首次桌面安装或交互授权时说明缺项，不能套用 Linux Engine 安装命令。

目标缺少 Docker 时，在安装/部署授权范围内按该发行版官方文档安装 Engine 与 Compose 插件，核实软件源、签名和具体版本。先查发行版支持矩阵；衍生系统或不受支持版本不直接套 Ubuntu 命令、不使用无来源的一键脚本。冲突包的移除、共享 daemon 重启及升级先识别对其他应用的影响，超出授权则保持现状。Docker 管理权限等同高权限访问，不自动把所有用户加入 docker 组。

用 `docker version`、`docker info` 的必要字段、`docker compose version` 核实 daemon 可用、实际版本与架构；记录可用状态。镜像无法拉取时报告网络/凭证原因，不静默更换镜像源。Docker 发布端口可能绕过部分主机防火墙规则，必须同时核对绑定地址、安全组和实际外部可达端口。

## 新站点默认布局

新建容器静态站点使用官方 Nginx 固定版本镜像，记录实际摘要；复用 ECS 文档的 `releases/<版本>/site`、`static/releases/<版本>` 和 `current`。容器只读挂载应用父目录，而不是把 current 符号链接直接作为挂载源，避免挂载固定在旧目标。符号链接应为挂载范围内的相对链接。备份、清单与 Compose 文件放在 web root 外，Nginx 仅映射公开路径。

下面为候选服务的 Compose 示例；变量均由实际环境判断取得，镜像用 `nginx:<精确版本及变体>@sha256:<已核实摘要>`。`FRONTEND_SITE_PARENT` 是只含公开 releases/static/current 的目录；若沿用混合父目录，先将私有记录移到外部私有位置。配置目录仅包含完整且通过验证的 Nginx server 配置，按 ECS 路由示例把根改为 `/srv/site/current`、版本资源根改为 `/srv/site/static`，监听容器内 80，并保留 MIME 映射和 `open_file_cache off`。

```yaml
services:
  web:
    image: ${FRONTEND_NGINX_IMAGE:?set a verified pinned image}
    restart: unless-stopped
    ports:
      - "${FRONTEND_BIND_IP:-127.0.0.1}:${FRONTEND_PORT:?set a free port}:80"
    volumes:
      - type: bind
        source: ${FRONTEND_SITE_PARENT:?set public release parent}
        target: /srv/site
        read_only: true
        bind:
          create_host_path: false
      - type: bind
        source: ${FRONTEND_NGINX_CONF_DIR:?set config directory}
        target: /etc/nginx/conf.d
        read_only: true
        bind:
          create_host_path: false
    healthcheck:
      test: ["CMD-SHELL", "wget -q -O /dev/null http://127.0.0.1/ || exit 1"]
      interval: 15s
      timeout: 3s
      retries: 3
      start_period: 10s
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

健康检查命令须存在于所选镜像；此示例在包含 wget 的 Alpine 变体使用，其他变体改为实际可用探针。首页探针仅验证进程能服务页面，发布验收仍检查目标版本和全部路由。`unless-stopped` 处理进程退出及 daemon 重启；仅变为 unhealthy 不会自动重启。daemon 自启动由目标系统服务管理；skill 仅在用户调用时检查/处理，不宣称持续监控。

候选绑定 127.0.0.1 的空闲端口，不抢占既有 80/443。已有反向代理时候选继续仅绑定回环地址，由代理配置切换入口；没有代理时，验证后在已授权公网站点端口运行，报告单服务重建可能短暂中断，不承诺零停机。HTTPS 沿用已确认的终止位置及有效证书；需要容器终止 TLS 时另配 443 和只读证书挂载，不把上面的 HTTP 示例称为 HTTPS 部署成功。

已有镜像内置静态产物的部署继续使用原镜像发布方式：构建并扫描新镜像、保存不可变摘要与原镜像、候选验收后切换，失败恢复原摘要。按原有共享资源机制或在新旧镜像中保留所需哈希资源，验证生产入口上的旧资源 URL；仅保留旧镜像不足以保证旧页面资源可访问。不能把下述 current 切换步骤强套到没有挂载发布目录的部署。

## 检查、发布和恢复

所有命令显式指定本应用的 project 与 Compose 文件，参数用实际值，先核对当前帮助；私有环境文件不输出到日志。以下命令在目标 daemon 所在主机执行：

```sh
docker compose -p "$FRONTEND_COMPOSE_PROJECT" -f "$FRONTEND_COMPOSE_FILE" config --quiet
docker compose -p "$FRONTEND_COMPOSE_PROJECT" -f "$FRONTEND_COMPOSE_FILE" run --rm --no-deps web nginx -t
docker compose -p "$FRONTEND_COMPOSE_PROJECT" -f "$FRONTEND_COMPOSE_FILE" up -d --no-deps web
docker compose -p "$FRONTEND_COMPOSE_PROJECT" -f "$FRONTEND_COMPOSE_FILE" ps web
docker compose -p "$FRONTEND_COMPOSE_PROJECT" -f "$FRONTEND_COMPOSE_FILE" logs --tail 100 web
```

1. 保存当前服务镜像摘要、配置、端口、current 目标与已验证版本；保留旧镜像和原产物。候选使用独立 project、配置目录和端口，避免修改线上共享配置；检查健康状态和候选页面，启动命令返回成功不等于就绪。
2. 普通内容发布沿用 ECS 的应用独占锁、清单校验和资源先上传规则；在 Linux 同一文件系统中原子 rename 相对符号链接。容器挂载的父目录保持不变，无需为每次内容更新重建容器。以普通入口 URL 限时查询目标版本（默认最多 30 秒），并验证旧资源 URL；超时先核对实际链接、挂载及文件缓存，不能加 cache-busting 掩盖问题。回退时原子切回已验证归档。macOS/Windows 文件共享的符号链接行为需另验，不能代替 Linux ECS 同文件系统验证。
3. 配置更新先在独立候选中测试完整配置，再备份并原子替换线上配置目录内的文件；挂载配置目录而非单个文件，使替换可见。在运行容器执行 `exec -T web nginx -t` 成功后才 `exec -T web nginx -s reload`；失败恢复配置，验证仍由原配置服务。
4. 镜像/Compose/端口升级在候选通过后，受控执行本应用的 `up -d --no-deps web`；不要重启 daemon 来更新应用。失败恢复旧镜像摘要、Compose 和配置，再重建本应用并验收。若首次部署无恢复点，恢复部署前入口状态，明确没有旧版本。
5. SSH 中断、命令超时或健康异常时先查询本应用容器、实际镜像、current 和入口响应，区分已切换/未切换/不明，再恢复。记录失败及未验证项，不仅按进程退出码判断成功。

独立维护任务先只读检查：版本、重启次数/健康、必要脱敏日志、磁盘和当前发布。修复/升级按用户授权执行，应用重启不连带其他容器；不使用全局 prune、全局 stop 或 `down -v` 清理。日志可能有用户信息，展示前脱敏。清理仅针对本任务资源且遵守保留期，不能移除旧页面仍引用的资源。

依据：[Engine 安装](https://docs.docker.com/engine/install/)、[Compose 生产部署](https://docs.docker.com/compose/how-tos/production/)、[只读 bind mount](https://docs.docker.com/engine/storage/bind-mounts/)、[重启策略](https://docs.docker.com/engine/containers/start-containers-automatically/)、[端口发布](https://docs.docker.com/engine/network/port-publishing/)。
