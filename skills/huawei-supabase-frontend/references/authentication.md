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

先核实本地 `hcloud configure set --help` 和 `hcloud configure sso --help`。以下变量来自已有配置或用户的身份中心信息；FRONTEND_PROFILE 使用已选定或新建且不冲突的名称。FRONTEND_SSO_REGION 是身份中心所在区域，可能与部署区域 FRONTEND_REGION 不同。

```sh
hcloud configure set --cli-profile="$FRONTEND_PROFILE" --cli-mode=SSO \
  --cli-region="$FRONTEND_REGION" --cli-sso-start-url="$FRONTEND_SSO_START_URL" \
  --cli-sso-region="$FRONTEND_SSO_REGION"
hcloud configure sso --cli-profile="$FRONTEND_PROFILE"
```

账号和权限集已明确时，可配置 `--cli-sso-account-name` 和 `--cli-sso-permission-set-name`；否则按官方交互选择已授权目标。登录、MFA 或门户授权交由用户完成，不索取密码、验证码或会话令牌。登录过期时续登相同 profile，成功后恢复只读预检。没有门户或权限分配时明确缺少的条件，不宣称普通控制台账号可直接 SSO 登录。

## 只读预检与错误诊断

已确认委托的 ECS 可由 KooCLI 的 ecsAgency 模式获取临时凭证；这只是认证方式，不需要为静态前端新购 ECS。本机复用选定 profile。先查看本地 `hcloud RDS ListAiApplications --help`、`hcloud CDN --help` 和 OBS 工具帮助，再选择本次任务所需的只读查询；分页按对应命令规则读完。

只有目标 API 需要 project ID 时，才优先让 KooCLI 自动解析；保留用户指定项目。全局服务、桶访问与 RDS 区域项目不能混用同一 ID。自动解析受限且认证有效时，再查询官方 IAM 项目接口或使用已知目标 ID。

- 401、Unauthorized 或 APIGW.0301：先检查凭证有效期、临时令牌、SSO 会话和委托条件；保留脱敏请求 ID。不能仅凭错误认定密钥错误，也不能靠改填 project ID 绕过无效认证。
- 403：区分权限不足与策略拒绝，指出具体操作，不自动授予管理员权限。
- DNS、TLS、超时：报告网络阶段，保留 TLS 校验，不标记区域不支持。
- 查询为空：仅在查询成功且分页完整后报告不存在，不自动购买替代资源。

认证成功以目标只读 API 响应为证；某一服务成功不代表其他服务权限足够。认证失败时继续可独立完成的本地构建与配置计划，云端状态标记未核实。首次凭证配置和 MFA 由用户通过官方交互完成，聊天及仓库不接收秘密。

## 官方依据

核实日期：2026-11-06；SSO 参数沿用此前 KooCLI 7.3.12 帮助核对记录，执行时复核；本次未实测云端认证。

- [访问凭证最佳实践](https://support.huaweicloud.com/bestpractice-iam/iam_0516.html)
- [SSO 登录](https://support.huaweicloud.com/usermanual-hcli/hcli_03_009.html)
- [认证模式](https://support.huaweicloud.com/usermanual-hcli/hcli_05_10.html)
