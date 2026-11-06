# KooCLI 部署、更新与回退

## 发现能力

先检查 hcloud 是否安装，再运行：
```sh
hcloud --help
hcloud FunctionGraph --help
hcloud FunctionGraph CreateFunction --help
hcloud FunctionGraph UpdateFunctionCode --help
hcloud FunctionGraph UpdateFunctionConfig --help
```

仅获取本次需要的操作帮助。凭证使用已有 profile 或官方认证机制，不打印配置文件内容或把 AK/SK 写进脚本。缺少凭证时让用户通过官方配置流程准备；不要请求在聊天中粘贴密钥。

从官方 CLI 操作列表核实模板查询、函数列表/配置、触发器、版本和别名操作。新项目先查询适用模板；模板名不是 API 枚举，模板不存在则用框架标准脚手架。安装缺失工具采用官方对应平台安装流程，不自动修改已有 profile。

完成条件：明确 profile、region、project ID，目标函数 URN（新建则为唯一目标名称）、运行环境、入口方案及本次授权范围。列举查询处理分页；有多个同名候选时不猜测目标。

## 请求文件与代码包

用官方 --cli-jsonInput 传递复杂参数。文件的顶层按请求位置区分：
```json
{
  "path": {"project_id": "实际项目ID"},
  "body": {"func_name": "实际函数名称"}
}
```
这只是格式示例，缺少创建必需字段。根据当前操作 --help、API Explorer 和已核实的模板补全实际请求，完成校验后才执行。

命令形态：
```sh
hcloud FunctionGraph CreateFunction --cli-profile="$FG_PROFILE" --cli-region="$FG_REGION" --cli-jsonInput="$FG_REQUEST_FILE"
```
变量须来自当前已确认的部署目标；更新使用对应操作和包含 function_urn 的 path。KooCLI 系统选项放命令行；同一位置的参数完整放 JSON，避免部分 body 在文件、部分在命令行。

官方 JSON 输入上限为 5 MB，执行时复核当前限制。Base64 有体积膨胀，代码包较大时优先官方 OBS 代码来源或其他受支持机制。OBS 上传优先使用官方工具的已验证能力；KooCLI 覆盖不足时可使用 obsutil，无需重写对象存储签名。

CreateFunction 当前文档列出 HTTP runtime 值为小写 http；Python/Node 路径在 bootstrap 中指定。HTTP 启动契约与通用事件 handler 参数说明可能不一致，依据 HTTP 模板/API Explorer 核实 handler 值，不机械套用 index.handler 或未验证字段。代码来源的 code_type、code_filename、func_code/file、code_url 应按所选上传方式核对，不能把本地 ZIP 路径直接当成编码内容。

将实际请求文件与非敏感部署信息保存在项目约定位置；包含代码或配置秘密的请求文件按敏感临时文件管理并排除版本控制。配置输出、CLI 错误及日志展示前脱敏。

## 首次部署

1. 查询目标是否存在。已有 URN 则进入更新流程；若目标已存在但归属不明，先消除歧义。
2. 验证本地包后执行 CreateFunction，记录返回 URN。查询资源配置和就绪状态，按当前响应字段判断，设置有限等待时长（默认最多十分钟）。
3. 创建或复用访问入口。APIG 按 [复用与自动开通流程](apig.md) 执行：优先复用，缺少合适实例且需要 APIG 时，在已有购买授权内自动按需开通并等待就绪。未明确要求 APIG 时也可核实 FunctionGraph URL 是否满足需求；不要把存在 API 文档当作所有区域可用。
4. APIG 路径需覆盖主页、静态资源、深层路由和实际 API 方法。确认是否改写/移除路径前缀、是否已发布到目标环境，记录真实调用 URL。创建触发器成功不代表 API 已发布。
5. 按应用用途配置鉴权：公开网页需浏览器可访问，不能要求浏览器持有云 AK/SK；受保护业务接口保留应用认证。入口公开范围应包含在部署授权里，避免为解决 401 而扩大权限。
6. 验证外部访问并记录结果。自定义域名、HTTPS 和 CORS 按实际入口配置，不臆造域名。

## 更新与回退

- 更新前保存已知良好的代码产物或可用版本、必要配置及当前入口目标。敏感配置使用受保护位置保存。
- 查询现有配置，合并本次变更后调用 UpdateFunctionCode / UpdateFunctionConfig。读响应中的只读字段不能原样回传；按写 API schema 筛选。
- 现有版本/别名流程优先复用。先验证候选版本再切流，前提是当前入口支持绑定该版本/别名；不假设所有触发器都支持。
- 更新 latest 可能立即影响线上流量。执行前说明这一影响及可用回退方案。
- 回退使用已记录的版本和入口绑定，或恢复旧代码与相关配置；不能通过删除并重建函数模拟更新。应用回退不等于数据库回退。
- 失败时保留证据并停止扩大变更。仅在已授权的回退范围内执行恢复；不自动删除共享网关、数据库或其他资源。

## 验证和交付

本地：实际生产入口启动、依赖导入、包内静态产物和权限正确。
云端：资源状态可用，再通过实际外部 URL 检查：
- 首页返回预期页面和 Content-Type，而非网关错误页面。
- 至少一个真实 JS/CSS/图片资源返回正确内容；缺失资源保持 404。
- SPA 深层路径刷新或框架实际页面路由工作正常。
- 适用的 API、认证、CORS 与数据库连接工作正常；业务写入验证使用获授权的测试数据。
- 必要时查看函数启动日志，区分函数未启动、网关路由未发布和应用错误。

记录实际命令（脱敏）、区域、URN、版本/别名、入口 ID/URL、产物摘要、验证时间及结果。仅完成静态检查时，报告“未实测云端部署”，不能写成上线成功。

依据：[官方资料](sources.md) 中的 KooCLI、HTTP 函数、创建 API、入口 API 和触发器文档。
