# KooCLI 认证与只读预检

部署只需有效的认证上下文和目标区域，不强制创建永久 AK/SK。优先复用用户指定或当前有效 profile，确认目标账号；需要补充认证时按运行环境选择。只读取模式、区域、profile 名称等必要元数据，展示前过滤秘密字段，不输出整个配置文件。

| 环境 | 认证选择与前提 |
| --- | --- |
| 已有有效 profile | 沿用其 AKSK、SSO、ecsAgency 或 AssumeRole 模式，不覆盖配置或擅自切换账号。 |
| 本机且组织已启用 IAM 身份中心 | 使用 SSO；需要门户 URL、身份中心所在区域及获分配的账号/权限集，用户完成登录。 |
| 已绑定 IAM 委托的 ECS | 使用 ecsAgency，KooCLI 根据 ECS 委托自动获取临时凭证；委托需具备目标服务权限。普通本机不能仅凭这个选项取得身份。 |
| CloudShell | 可作为用户登录控制台后的在线执行环境；先验证当前 shell 的 KooCLI 认证。浏览器登录不代表本机 CLI 已登录，不复制 CloudShell 凭证到本机，也不假定 CloudShell 等同于已配置委托的 ECS。 |
| 以上条件不具备 | 使用官方配置流程配置 AKSK；临时 AK/SK 必须连同 SecurityToken 使用。不要让用户在聊天中粘贴密钥。 |

已有 AssumeRole 配置需保留其源 profile 和委托关系；认证失败不自动创建委托、启用身份中心或授予额外权限。

## SSO

先核实本地 `hcloud configure set --help` 和 `hcloud configure sso --help`。以下变量来自已有配置或用户的身份中心信息；FG_PROFILE 使用已选定或新建且不冲突的名称。FG_SSO_REGION 是身份中心所在区域，可能与部署区域 FG_REGION 不同。

```sh
hcloud configure set --cli-profile="$FG_PROFILE" --cli-mode=SSO \
  --cli-region="$FG_REGION" --cli-sso-start-url="$FG_SSO_START_URL" \
  --cli-sso-region="$FG_SSO_REGION"
hcloud configure sso --cli-profile="$FG_PROFILE"
```

账号和权限集已明确时，可配置 `--cli-sso-account-name` 和 `--cli-sso-permission-set-name`；否则按官方交互选择已授权目标。登录、MFA 或门户授权交由用户完成，不索取密码、验证码或会话令牌。登录过期时续登相同 profile，成功后恢复只读预检。没有门户或权限分配时明确缺少的条件，不宣称普通控制台账号可直接 SSO 登录。

## ECS 委托

仅在已确认的、具有适当委托的 ECS 执行：

```sh
hcloud APIG ListInstancesV2 --cli-mode=ecsAgency \
  --cli-region="$FG_REGION" --limit=20 --offset=0
```

由 KooCLI 获取并使用临时凭证，无需自行读取元数据服务或导出 AK/SK。此命令用于预检；完整资源发现仍按 APIG 指引分页。

## 自动获取 ID 与错误诊断

使用已选认证执行本次任务需要的只读操作，例如：

```sh
hcloud APIG ListInstancesV2 --cli-profile="$FG_PROFILE" \
  --cli-region="$FG_REGION" --limit=20 --offset=0
```

保留用户指定的项目；未指定时先让 KooCLI 自动获取 project ID。全局 API 可能需要自动解析账号 ID；只有实际操作需要时才解析，不要求全部预填。明确认证成功且自动项目发现受限时，才按 [部署指引](deployment.md) 查询 IAM 或补充已知目标 ID。

- `APIGW.0301 / Unauthorized`：先处理认证。检查模式、凭证有效性、临时令牌、SSO 会话或 ECS 委托条件；保留请求 ID 和脱敏错误。仅凭这个错误不判定密钥必然错误，也不循环改查 IAM。
- 前置解析失败后出现 `project_id` 或 `cli-domain-id` 缺失：报告前置失败；手填 ID 不能修复无效身份。指定服务 endpoint 也不证明 CLI 的前置认证解析已走该 endpoint。
- 403：按实际错误区分策略拒绝与权限不足，指出缺少的操作；不自动扩大权限。
- DNS、TLS、超时：报告网络阶段，不能当作认证或区域不支持。保留 TLS 校验。

认证预检成功须以目标只读 API 的真实成功响应为证；配置保存成功或 SSO 登录成功不等于具有 APIG/FunctionGraph 权限。查询为空与查询失败分开报告。

## 官方依据

核实日期：2026-11-06；命令选项已与 KooCLI 7.3.12 本地帮助核对，SSO 和 ECS 委托尚未实测。

- [访问凭证最佳实践](https://support.huaweicloud.com/bestpractice-iam/iam_0516.html)
- [SSO 登录](https://support.huaweicloud.com/usermanual-hcli/hcli_03_009.html)
- [认证模式](https://support.huaweicloud.com/usermanual-hcli/hcli_05_10.html)
