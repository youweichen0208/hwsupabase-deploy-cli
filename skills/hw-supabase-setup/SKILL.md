---
name: hw-supabase-setup
description: 为已有华为云 RDS Supabase 准备应用部署环境，创建或复用 OBS 桶、APIG 专享实例、FunctionGraph 委托与网络配置，并按需接入 Supabase Storage。不部署完整 Supabase，也不替换客户已有数据库。
---

# 准备客户应用环境

共用配置与状态由 [deliver](../hw-supabase-deliver/SKILL.md) 管理；先读其 [执行契约](../hw-supabase-deliver/references/workflow.md)。

## 先发现，再补齐

1. 读取客户现有 RDS Supabase 的应用 ID、关联区域、VPC/子网、安全组、SSL/EIP、Storage、Auth URL。已有可用配置优先复用。
2. 确认 KooCLI profile 对应的账号与项目。OBS 使用独立 `config_file`，不能假设 `hcloud configure` 自动配置了 OBS。用 `hcloud obs config -interactive -config=<客户配置路径>` 在客户本地输入；不覆盖其他客户的默认配置。结构化 OBS 探针所需 SDK 凭据也通过配置指定的环境变量注入。
3. 用官方 `huawei-functiongraph`、`huawei-cloud-apig-instance-management`、`huawei-obs`、IAM/VPC 服务知识和当前 API 元数据组织操作。具体顺序见 [资源流程](references/resources.md)。
4. 输出创建/复用清单与费用来源。APIG 专享实例、EIP/公网带宽具有持续费用；缺规格或预算时只补问影响购买的参数，不能用共享版绕过。
5. 生成 `phase: setup` 工作流；每个创建步骤必须有精确身份探针、只读回查和可恢复 ID。完成资源准备后，仍需 [验收](../hw-supabase-deliver/references/acceptance.md)。

## 网络与存储选择

- 后端沿用 Supabase 的同区域 VPC，按真实地址与协议访问 8443。HTTPS 必须校验证书，不能为内网 IP 直接关闭验证。
- FunctionGraph 启用 VPC 后，外部 AI API、SMTP 等出网需求单独检查。仅访问内网 Supabase 不自动增加 NAT。
- 正式前端与 API 配置域名、证书、DNS。已有 Supabase 公网 HTTPS 不动；没有公网入口时优先按 RDS Supabase 官方 EIP 流程配置，Auth 使用邮箱/GitHub 时不要改为不兼容的 DNAT 路径。
- 网站桶公开范围只含网站对象；部署包私有；可选用户文件桶只交给 Supabase Storage。桶名第一次确定后写入配置/状态，续跑不重新生成随机桶名。
- Storage 已配置时只核验；未配置且客户需要时，新建独立桶，使用桶范围凭据调用官方 RDS Storage 配置能力。不要自行迁移已有 Storage 桶或直接同步其内部对象。

无法自动完成的证书、域名验证、区域公测能力，输出具体待办与已保存资源 ID。不得将其写成 setup 成功后的隐含手工步骤。
