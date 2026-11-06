# 配置、工作流与发布契约

## 工具分工

共享脚本是确定性辅助层，不是独立的云 API SDK。agent 负责理解客户项目、读取官方工具元数据，生成本次真实参数；KooCLI/官方 OBS SDK 执行云请求。脚本负责本地校验、互斥、检查点、构建、HTTP 检查和发布记录。

源仓库示例位于 `examples/`；完整安装后位于 deliver 的 `assets/examples/`。配置中的相对路径均相对 `hwsupabase.yaml` 所在目录。辅助入口参数顺序：`deploy.py --config <path> <command> ...`。

## 项目配置

`version: 1`；固定身份字段：`customer`、`environment`、`region`、`profile`、`project_id`。改变同一状态目录中的身份会被拒绝。

- `supabase`：现有应用 ID、`public_url`（必须 HTTPS）、`internal_url`（实际 HTTP/HTTPS）、`public_key_env`、可选 `service_key_env`/`database_url_env`。
- `network`：现有 Supabase 的 `vpc_id`、`subnet_id`、`security_group_id`。
- `obs`：HTTPS endpoint、客户专用 `config_file`、私有 `artifact_bucket`、可选 `site_bucket`/`storage_bucket`，SDK 凭据环境变量名称。三种用途不能同桶。
- `apig`：`mode: reuse` + 实例 ID，或 `mode: create` + `spec_id`、`network_id`、`available_zone_ids`。公网入口模式由该区域官方 API 确定，额外真实参数写入客户工作流。
- `web`：源码目录、构建 argv 数组、输出目录、域名。构建器只传入基本系统变量、公开 key、`SUPABASE_PUBLIC_URL` 和 `HWSUPABASE_RELEASE`。项目自己的公开变量映射写入构建脚本；禁止传整份部署环境。
- `python`：源码目录、框架、`module:object`、`version: '3.12'`、requirements 路径、显式 include 列表、镜像 digest 和平台。

配置文件保存名称/引用；实际 secrets 放环境或客户的秘密管理系统。不要把 `.hcloud`、`.obsutilconfig`、`.env`、SSH key、数据库 dump 放入应用产物。

## 工作流

文件格式为 YAML/JSON；`version: 1`、不可变 `id`、`phase: setup|stage|promote|rollback`，非 setup 阶段必须有 `release`。同一工作流 ID 的内容或配置改变会被拒绝。

```yaml
version: 1
id: customer-stage-r1
phase: stage
release: r1
steps:
  - id: published-version
    ownership: created
    apply:
      kind: api
      service: FunctionGraph
      operation: CreateFunctionVersion
      input:
        path:
          project_id: {$ref: config.project_id}
          function_urn: '<actual latest function URN>'
        body: {version: r1, description: 'customer staging r1'}
    capture: {function_urn: func_urn, version: version}
    probe:
      call:
        kind: api
        service: FunctionGraph
        operation: ListFunctionVersions
        input:
          path:
            project_id: {$ref: config.project_id}
            function_urn: '<actual latest function URN>'
          query: {maxitems: '100'}
      select:
        path: versions
        where: {version: r1}
      expect: {version: r1}
      capture: {function_urn: func_urn, version: version}
```

示例表达结构，agent 必须填入实际 URN，并根据当前官方帮助确认字段。列表探针必须完整；遇到未遍历的分页时脚本会阻止创建。可改为针对已有资源的 Show/Get 探针，或由 agent 完成分页发现后生成精确清单。不能只查第一页后断言“不存在”。

- `ownership: created|reused|updated`；reused 探针不符合时拒绝写入。一个资源已存在但要更新其配置时使用 updated。
- `probe.call` 只能只读。`expect` 是点分路径到精确预期值的映射；不要只检查资源存在，更新应检查版本、代码摘要、配置标记等本次期望。
- `probe.select` 在数组中按 `where` 精确选择，零条表示未满足，多条表示歧义。数组嵌套字段用点分路径。
- `capture` 只保存标量 ID、名称、版本、摘要。apply 导出的所有名字必须也在 probe.capture 中，保证创建超时后可恢复。
- `{$ref: steps.published-version.outputs.version}` 引用当前工作流；`{$ref: state.runs.some-run.steps.some-step.outputs.id}` 引用先前状态；`{$ref: config.project_id}` 引用配置。
- `{$env: NAME}` 在执行时读取环境；`{$json: {KEY: {$env: NAME}}}` 生成官方 API 需要的 JSON 字符串。参数通过 0600 临时 JSON 文件传给 KooCLI，并在 finally 删除；不进入 shell/argv/日志。
- `input` 仅允许官方 JSON 参数分区 `path/query/body/header/formData/cookie`。全局 profile/region 由配置提供，不能在清单里覆盖。

OBS 创建和上传用官方命令，观察用结构化 SDK 探针：

```yaml
- id: artifact-bucket
  ownership: created
  apply:
    kind: obs
    command: mb
    args: ['obs://actual-customer-artifacts', '-location=cn-north-4']
  probe:
    call:
      kind: obs-read
      target: bucket
      bucket: {$ref: config.obs.artifact_bucket}
    expect: {exists: true}
```

`obs-read` 支持 bucket/object/website/cors；object 还需 `key`，返回 `exists/etag/size/content_type`。仅 404 视为不存在，403/网络错误不可当不存在。对象探针应校验内容：小文件单段上传可使用本地 MD5 对比 ETag；多段对象不能用这个假设，需要下载校验或 agent 的额外验收，不能只比较 size。网站/CORS 探针的 exists 不能代替配置内容和浏览器检查。

`obs` 支持 `mb/cp/sync/bucketpolicy` 及读取命令，始终使用指定 config。禁止修改 Supabase Storage 用户对象，禁止 sync 删除。前端/制品上传由 agent 将构建清单编译成步骤；不同路径/类型可以分别设置官方支持的 MIME、缓存选项。

## 状态机与失败处理

`pending → in_flight → waiting → complete`。写调用异常为 `uncertain`，工作流为 `partial`。状态通过原子文件替换保存，持有进程级文件锁。锁支持 macOS/Linux；Windows 使用 WSL。

每次 run 先探针；符合即恢复 capture 并跳过写入。waiting 每次最多观察 45 秒，超时保留已返回 ID；下一次继续观察。uncertain 无匹配时禁止自动重发。确定未创建后，生成新工作流 ID并保留原记录；若创建了错误配置，应读取具体 ID，生成 updated 修复清单。

状态保存在 `.hwsupabase/<customer>/<environment>/state.json`，不入 Git。目录和状态文件权限分别 0700/0600。同一目录单进程互斥，**不提供多机器分布式锁**；团队交接需完整传递该环境状态、产物与报告，并约定单一操作者。

## 发布记录

`register-release metadata.yaml` 要求该 release 的 stage 工作流已完成。metadata 支持：

```yaml
id: r1
stage_workflow: customer-stage-r1
function_urn: '<actual function URN>'
function_version: r1
alias: production
apig_snapshot: .hwsupabase/customer/staging/artifacts/r1/apig.json
web_manifest: .hwsupabase/customer/staging/artifacts/r1/web-manifest.json
python_manifest: .hwsupabase/customer/staging/artifacts/r1/python-manifest.json
```

只保留启用的应用类型字段；Python 必须有不可变版本和 APIG 快照，函数 URN 与版本必须同时匹配 stage 某一步的云端回读输出。APIG 快照保存路由、后端、发布环境与域名关联等可恢复参数，先移除密钥/证书私钥。登记后 metadata 与 manifest 不允许改变。

`activate r1 promote-workflow-id` 要求同 release 的 promote/rollback 工作流完成，且 verify 报告与当前配置、所有工作流状态匹配。激活只更新本地记录，真正切换已在工作流中完成；修改状态不能替代远端操作。

新版本 promote/verify 失败但尚未 activate 时，用 `rollback-plan --failed-promotion`，目标是最后通过验收的 current；撤回已成功激活的版本时，用 `rollback-plan`，目标是 previous。也可 `--release <id>` 明确指定。检查旧产物仍在、数据库变更兼容；生成绑定目标 release 的 rollback 工作流，恢复函数版本别名及 APIG/前端入口，验证后 activate。基础设施与数据库不自动销毁/回退。
