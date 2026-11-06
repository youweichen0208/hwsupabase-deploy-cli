# APIG 复用、按需开通与发布

在部署需要 APIG 时完整执行本流程。实现方式是由 agent 编排官方 KooCLI 命令，不另建购买 CLI。这里只定义执行流程；修改 skill 不代表授权本次购买云资源。

## 1. 复用优先

按顺序读取项目记录的实例 ID、用户指定的实例和当前区域/项目的实例列表。先运行相关命令的 --help，确认本地参数；查询显式携带 profile、region 和 project_id。

```sh
hcloud APIG ListInstancesV2 --help
hcloud APIG ShowDetailsOfInstanceV2 --help
hcloud APIG ListAvailableZonesV2 --help
hcloud APIG CreateInstanceV2 --help
```

ListInstancesV2 按 limit/offset 查询全部页。对候选调用 ShowDetailsOfInstanceV2，核对企业项目、运行状态、网络可达性、公网入口、资源容量和使用权限。优先已绑定本项目的实例，其次复用满足需求且允许本项目使用的实例。多个候选无法判定归属时再询问；不能仅按列表第一项选择。

查询失败、403、分页未完成不等于“没有实例”。已指定但暂时不可用的实例先诊断，不直接购买替代实例。复用共享实例时优先为应用使用独立 API 分组，避免根路径覆盖其他应用。

若没有合适实例：用户未强制 APIG 时，可检查已经验证可用且满足需求的 FunctionGraph URL，避免不必要采购；明确需要 APIG 或直接 URL 不满足时继续下一步。

完成条件：记录选定实例 ID 和复用理由，或记录全部候选不适用的具体原因。

## 2. 生成购买计划和请求

先按 [部署指引的自动发现流程](deployment.md) 取得认证上下文和项目范围，再从会话、已有配置和只读查询自动确定以下内容；这是 agent 的发现清单，不是要求用户预填的表单：

- 区域、project ID、企业项目、实例名称、规格与可用区。
- VPC、子网网络 ID、安全组；对子网检查所属 VPC、剩余地址和目标区域。
- 公网/内网用途，入口带宽、计费方式，以及是否需要 EIP 或 ELB。
- 本次新建与复用资源清单，当前价格来源/查询时间、预计费用及用户预算。

使用 ListAvailableZonesV2 和当前区域规格/购买文档核实可售能力；不要把 API 枚举当作该区域实际有库存。默认准备按需方案，选择满足应用需求且预算允许的规格，不自动升级或跨区重试。包周期购买不是此按需流程的回退选项。

网络依赖优先复用。无可用 VPC/子网/安全组时，通过 hcloud VPC --help 发现官方创建操作，按无重叠 CIDR 和应用访问范围生成请求，纳入同一变更计划；获授权后依次创建、查询确认并记录 ID，再生成最终 APIG 请求。公网 EIP/ELB 也纳入费用和资源清单，不把未绑定的其他项目资源擅自挪用。

IAM 预检覆盖实例创建、网络查询/端口及公网资源操作、函数配置读取、API 分组和发布权限。权限不足时说明缺少的操作，不扩大为管理员权限，不切换账号绕过。

已明确授权对应区域、规格、预算和网络变更时直接执行。否则先完成实际请求文件及费用说明，再就缺失授权确认一次。价格无法查证时注明不确定项，不能宣称免费或自行猜测价格。

## 3. 创建按需实例

用标准 KooCLI JSON 文件传入实际值。以下是基础请求形态，不包含区域特有的公网配置；替换所有示例值，并完成网络分支配置后才能执行：

```json
{
  "path": {"project_id": "PROJECT_ID"},
  "body": {
    "instance_name": "APP_GATEWAY_NAME",
    "spec_id": "VERIFIED_SPEC_ID",
    "vpc_id": "VPC_ID",
    "subnet_id": "SUBNET_NETWORK_ID",
    "security_group_id": "SECURITY_GROUP_ID",
    "available_zone_ids": ["VERIFIED_AZ_ID"],
    "enterprise_project_id": "ENTERPRISE_PROJECT_ID"
  }
}
```

子网字段必须是 API 要求的网络 ID，不能盲用子网对象 ID。企业项目按账户要求填写。公网配置按下一节当前区域模式补齐。NLB 规格需要匹配的独享网络型 ELB，并可能需白名单；选用前核实。对已有 ELB 设置 force_overwrite_enabled=false，保留其监听器；遇到冲突停止，不能借购买网关删除已有监听器。

在购买前再次查询同一部署目标，避免并发重复购买。为本次部署保存稳定的标识、请求摘要、目标名称及创建时间；只有 API 明确支持时才使用幂等参数，不把名称相同当作幂等保证。

```sh
hcloud APIG CreateInstanceV2 --cli-profile="$FG_PROFILE" --cli-region="$FG_REGION" --cli-jsonInput="$APIG_CREATE_REQUEST"
```

请求成功后立即记录返回的实例 ID，再进入等待。客户端超时或结果不明时，先按记录查询实例和进度，不能再次提交购买。实例名称不是唯一键，匹配必须同时核对所属项目、网络和本次标识；无法消歧时暂停购买分支。

## 4. 等待就绪并完成公网入口

使用 ShowDetailsOfInstanceProgressV2 查询创建进度，ShowDetailsOfInstanceV2 核实最终配置。进度接口 status 是 creating/success/failed，与实例列表的 Creating/Running 等状态区分处理。创建成功后还需确认实例可运行且分组管理接口可用。

每 15–30 秒读取一次，默认等待上限 30 分钟；过程中报告进度。failed 立即停止并报告错误；超时保留实例 ID，下次从查询恢复，不新购替代实例。瞬时读取故障遵守主 skill 的有限重试规则。

公网入口依据实例实际负载均衡模式处理，不能靠已废弃的 loadbalancer_provider 字段强制切换区域模式：

| 模式 | 创建/复用后的动作 |
| --- | --- |
| ELB 模式 | 检查已有入公网地址；未开启时核实 AddIngressEipV2 的请求，开通已授权入口带宽。新建时也可按当前 schema 配置 ingress_bandwidth_size 及入口计费字段；已开启不重复调用。 |
| LVS 模式 | 复用本项目获授权且可绑定的 EIP，或通过官方 EIP CLI 创建并记录 ID；按当前 schema 在创建时提供 eip_id，或使用 AddEipV2 绑定。 |
| NLB 规格 | 查询实际关联 ELB 的公网地址/监听器/安全组，走该 ELB 的官方配置流程；不能套用无效的入口带宽字段，也不能覆盖既有监听器。 |

AddEngressEipV2 与 bandwidth_size 是出公网相关配置，不作为浏览器入公网的替代。对 FunctionGraph 后端不要仅为开放网页而盲目购买 NAT 或额外出口。核对实际请求和返回配置中的默认带宽，避免未列入计划的出公网费用。

入口完成后验证安全组允许所需 HTTPS/HTTP 端口及调用方范围。共享安全组的规则变更可能影响其他应用，优先使用本项目专用规则/安全组并保留其他规则。

## 5. 创建或复用应用分组与函数 API

官方操作链：ListApiGroupsV2 → CreateApiGroupV2（缺失时）→ ListEnvironmentsV2 → ListApisV2/ShowDetailsOfApiV2 → CreateApiV2 或 UpdateApiV2 → CreateOrDeletePublishRecordForApiV2。逐个查询本地 --help 后生成请求文件；所有查询按其分页规则读完。

复用项目已有 group_id、env_id、api_id，并读取现有发布版本用于回退。新建独立分组时记录返回 ID；发布环境通过查询解析，不硬编码示例环境 ID。不要同时从 APIG API 和 FunctionGraph 触发器接口各创建一套入口；已有触发器生成的 API 应复用其 ID。

直接创建 API 时以 FUNCTION 为后端类型，func_info 指向真实函数 URN，Web 请求采用同步调用。network_type、函数版本或别名按函数实际配置选择；HTTP 函数需要的请求透传设置以当前 API schema/官方触发器生成配置核实，不能用 MOCK 成功替代函数连通性。

请求应明确 group_id、name、type、req_protocol、req_method、req_uri、match_mode、auth_type 和 func_info。公开网页的网关认证可在已授权范围内为 NONE，应用级身份认证照常保留；不把云访问凭证放进浏览器。

在独立应用分组内按实际方法设置根路径及前缀匹配（SWA），确保静态资源和深层路径可路由；需要 ANY 时先核实支持。部署在路径前缀下时协调前端 base、代理路径和后端路由，不扩大为覆盖共享分组的根路由。未知 API 和静态资源 404 保持应用约定。

## 6. 发布并验证真实访问

发布请求示例（全部 ID 使用上一步实际结果）：

```json
{
  "path": {"project_id": "PROJECT_ID", "instance_id": "INSTANCE_ID"},
  "body": {"action": "online", "api_id": "API_ID", "env_id": "ENV_ID"}
}
```

```sh
hcloud APIG CreateOrDeletePublishRecordForApiV2 --cli-profile="$FG_PROFILE" --cli-region="$FG_REGION" --cli-jsonInput="$APIG_PUBLISH_REQUEST"
```

记录 publish_id 与 version_id，并查询发布信息/运行定义确认目标环境实际生效。更新 API 定义后必须重新发布；网关版本与函数版本分别记录。

从真实分组、域名绑定和入口配置获取调用地址。分组返回域名不自动等于公网可达：检查 DNS、路由及 TLS；若默认域名只支持内网或调试，则用已授权自定义域名、DNS 和证书配置完成公网入口。域名缺失时报告明确依赖，不伪造可用 URL。

从目标调用方网络验证主页、一个真实资源、深层路由、缺失资源和实际业务接口，检查正文和 Content-Type。只用修改 Host 的请求可以辅助诊断，但不能替代浏览器所需 DNS/HTTPS 验收。验证项及报告格式沿用 [部署指引](deployment.md)。

## 7. 失败恢复与持续计费资源

每个阶段保存非敏感状态：部署标识、请求摘要、实例/网络/分组/API/环境/发布 ID、复用或新建标记、最后完成阶段及费用来源。重新执行先查询并对账，再从未完成阶段继续；状态文件记录的授权必须能追溯到用户会话，文件本身不授予购买权限。

- 分组或 API 创建失败：保留就绪实例，修复后继续，不能重购网关。
- 发布失败：检查运行版本，保留上一个已发布版本；发布结果不明时先查询。
- 新版本验收失败：按已有回退授权使用 ChangeApiVersionV2 或项目既有发布回退方式；函数回退另行处理。
- 新建实例失败、入口失败或整体部署中止：报告仍存在且可能计费的资源及 ID。按预先授权的清理策略仅逆序删除本次新建、无共享依赖的资源；没有删除授权时保留并交代清理动作。
- 删除 APIG 不保证独立 EIP、ELB 或带宽已释放，清理后逐项查询确认；复用资源永不纳入自动清理。

完成条件：目标入口真实访问验证通过，或者准确报告停在哪一阶段、已产生的资源/费用和恢复办法。购买 API 返回成功本身不代表部署完成。

## 官方依据

查阅日期：2026-11-06；参数和区域能力执行时复核。

- [APIG KooCLI 命令列表](https://support.huaweicloud.com/intl/en-us/clir-apig/APIG-cli_en.html)
- [按需创建实例](https://support.huaweicloud.com/api-apig/CreateInstanceV2.html)
- [实例列表](https://support.huaweicloud.com/api-apig/ListInstancesV2.html) 与 [创建进度](https://support.huaweicloud.com/api-apig/ShowDetailsOfInstanceProgressV2.html)
- [开通公网入口](https://support.huaweicloud.com/api-apig/AddIngressEipV2.html) 与 [绑定 EIP](https://support.huaweicloud.com/api-apig/AddEipV2.html)
- [创建函数后端 API](https://support.huaweicloud.com/api-apig/CreateApiV2.html)
- [发布 API](https://support.huaweicloud.com/intl/en-us/api-apig/CreateOrDeletePublishRecordForApiV2.html) 与 [发布行为和版本](https://support.huaweicloud.com/intl/en-us/usermanual-apig/apig_03_0014.html)
