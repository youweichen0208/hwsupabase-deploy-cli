# 区域名称与 region ID

核实日期：2026-11-06。此表缓存官方区域名称和 ID，供自然语言输入优先本地匹配；不是 FunctionGraph/APIG 的可用区域或可售规格清单。部署前仍需查询目标服务和账号可用性。project ID 属于账号，不能写成公共映射。

## 匹配规则

1. 用户提供完整 region ID 时保留该 ID；不在表内不等于无效，查官方资料核实后继续。
2. 中文区域名称先在下表匹配。可忽略空格及连字符样式，将同一名称中的数字写法归一，例如“北京4”“北京四”“华北北京四”对应同一条目。保留城市后的编号以及“汽车”“友好用户环境”“OP5”等限定词。
3. 下表常用简称仅是本 skill 的输入别名，官方对应关系以“官方名称”列为准。英文输入先按官方英文显示名称核实，不能把不确定的翻译加成别名。
4. “北京”“上海”“乌兰察布”“墨西哥城”等未指明编号的输入不能任意选一项。已有明确的同一部署目标配置可用来消歧；否则展示候选并询问一次。“华北”“华东”“亚太”等大范围描述也不足以唯一选区。
5. 普通“广州”按标准广州区域匹配，只有明确提及“友好用户环境”才使用特殊区域；汽车、联盟或其他专用区域也必须保留其使用条件。不得因为标准区域无库存而切换到特殊区域。
6. “华东二”是 cn-east-4，“上海二”是 cn-east-2；“华北三”是 cn-north-12。地区名称中的序号不一定等于 ID 后缀，必须查表，不能拼接推算。
7. 未命中、官方信息冲突、区域更名或服务报告区域不存在时，查询官方区域/终端节点资料或本地 KooCLI 支持的区域查询能力。查到唯一对应后继续，无法确定才询问；不得以网络或认证错误为理由换区域。

## 中国站 FunctionGraph 服务筛选

2026-11-06 实际读取 [中国站 API Explorer：FunctionGraph 地区和终端节点](https://console.huaweicloud.com/apiexplorer/#/endpoint/FunctionGraph) 全部三页，共 27 条。下面是其中中国境内的 12 条（内地 11 条、香港 1 条）。中国站是账号/交易站点，不等于仅有中国境内区域；该页面还列有海外及联盟区域，不能由页面站点推断当前账号全部可购买。

### 未带汽车或友好环境限定的境内条目

| 区域 | region ID | 官方 Endpoint |
| --- | --- | --- |
| 华北-北京一 | cn-north-1 | functiongraph.cn-north-1.myhuaweicloud.com |
| 华北-北京四 | cn-north-4 | functiongraph.cn-north-4.myhuaweicloud.com |
| 华北-乌兰察布一 | cn-north-9 | functiongraph.cn-north-9.myhuaweicloud.com |
| 华东-上海一 | cn-east-3 | functiongraph.cn-east-3.myhuaweicloud.com |
| 华东-上海二 | cn-east-2 | functiongraph.cn-east-2.myhuaweicloud.com |
| 华东二 | cn-east-4 | functiongraph.cn-east-4.myhuaweicloud.com |
| 华南-广州 | cn-south-1 | functiongraph.cn-south-1.myhuaweicloud.com |
| 西南-贵阳一 | cn-southwest-2 | functiongraph.cn-southwest-2.myhuaweicloud.com |
| 中国-香港 | ap-southeast-1 | functiongraph.ap-southeast-1.myhuaweicloud.com |

### 带专用限定的境内条目

| 区域 | region ID | 官方 Endpoint |
| --- | --- | --- |
| 华北-乌兰察布-汽车一 | cn-north-11 | functiongraph.cn-north-11.myhuaweicloud.com |
| 华南-广州-友好用户环境 | cn-south-4 | functiongraph.cn-south-4.myhuaweicloud.com |
| 西南-贵阳-汽车二 | cn-southwest-3 | functiongraph.cn-southwest-3.myhuaweicloud.com |

这三项仅在用户明确选择、账号权限及产品支持核实后使用，不作为普通区域缺货时的替代。

中国站部署先用本节筛选 FunctionGraph 候选，再进行账号、HTTP 函数和 APIG 可用性检查。Endpoint 存在只证明官方列出该服务入口，不保证当前账号已开通、HTTP 模板/运行时可用或 APIG 可售。参见 [FunctionGraph 产品功能](https://support.huaweicloud.com/productdesc-functiongraph/functiongraph_01_0141.html)，官方要求按控制台查询具体功能的区域支持。

通用表中的北京二、深圳、青岛、华北三未出现在此次 FunctionGraph 列表中。用户明确选择时先核实最新服务支持，不直接发起创建，也不擅自换区；表中未列出不等于永久不支持。海外部署仍使用官方 FunctionGraph 对应条目核实，不能把本节的境内子集称作中国站完整可售列表。

## 通用区域名称映射（不代表 FunctionGraph 支持）

下列 25 项来自 [IAM 官方区域表](https://support.huaweicloud.com/intl/zh-cn/usermanual-iam5/iam_01_1334.html)。来源是 IAM 文档，仅借用区域名称与 ID，不推导其他产品可用性。

| 官方名称 | 常用简称 | region ID |
| --- | --- | --- |
| 华北-北京一 | 北京一、北京1 | cn-north-1 |
| 华北-北京四 | 北京四、北京4 | cn-north-4 |
| 华北-乌兰察布一 | 乌兰察布一、乌兰察布1 | cn-north-9 |
| 华北-乌兰察布-汽车一 | 乌兰察布汽车一 | cn-north-11 |
| 华北三 | 华北3 | cn-north-12 |
| 华东-上海一 | 上海一、上海1 | cn-east-3 |
| 华东-上海二 | 上海二、上海2 | cn-east-2 |
| 华东二 | 华东2 | cn-east-4 |
| 华东-青岛 | 青岛 | cn-east-5 |
| 华南-广州 | 广州 | cn-south-1 |
| 华南-广州-友好用户环境 | 广州友好用户环境 | cn-south-4 |
| 西南-贵阳一 | 贵阳一、贵阳1 | cn-southwest-2 |
| 中国-香港 | 香港 | ap-southeast-1 |
| 亚太-曼谷 | 曼谷 | ap-southeast-2 |
| 亚太-新加坡 | 新加坡 | ap-southeast-3 |
| 亚太-雅加达 | 雅加达 | ap-southeast-4 |
| 亚太-马尼拉 | 马尼拉 | ap-southeast-5 |
| 非洲-约翰内斯堡 | 约翰内斯堡 | af-south-1 |
| 非洲-开罗 | 开罗 | af-north-1 |
| 拉美-墨西哥城一 | 墨西哥城一、墨西哥城1 | na-mexico-1 |
| 拉美-墨西哥城二 | 墨西哥城二、墨西哥城2 | la-north-2 |
| 拉美-圣保罗一 | 圣保罗一、圣保罗1 | sa-brazil-1 |
| 拉美-圣地亚哥 | 圣地亚哥 | la-south-2 |
| 中东-利雅得 | 利雅得 | me-east-1 |
| 土耳其-伊斯坦布尔 | 伊斯坦布尔 | tr-west-1 |

以下 5 项补自 [IAM 官方终端节点表](https://support.huaweicloud.com/api-iam/iam_01_0001.html)。特定站点/联盟区域需另外核实账号和服务支持；不能将 IAM 的全局 global 当作应用部署区域。

| 官方名称 | 常用简称 | region ID |
| --- | --- | --- |
| 华北-北京二 | 北京二、北京2 | cn-north-2 |
| 华南-深圳 | 深圳 | cn-south-2 |
| 欧洲-都柏林 | 都柏林 | eu-west-101 |
| 欧洲-巴黎 | 巴黎 | eu-west-0 |
| 中东-阿布扎比-OP5 | 阿布扎比OP5 | ae-ad-1 |

## 用法与维护

- “帮我部署到北京四” → cn-north-4，再交给 KooCLI 解析账号下的项目。
- “上海2区” → 若上下文明确指区域则为 cn-east-2；若指可用区 AZ，则需先确定 region，再查询 AZ，不把 AZ 当区域。
- “部署到北京” → 结合已有目标消歧，否则列出北京一/二/四。
- “广州友好用户环境” → cn-south-4，之后核实账号与目标服务是否支持。

此表不是穷尽列表。新增条目必须由官方名称/ID 对确认，记录来源和核实日期；只读部署过程遇到新信息可在当前任务使用，用户要求维护 skill 时再更新文件。已确认的区域解析结果在同一次任务中复用，无需为同一名称反复联网。
