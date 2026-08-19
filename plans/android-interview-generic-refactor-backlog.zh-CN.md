# Android Interview 通用化改造 Backlog

## 1. 目标

将当前 `android-interview` 从 Android 定向 skill 逐步演进为“通用面试运行时 + 岗位模板层 + 用户自定义模板 + 材料采集入口”的可扩展体系。

## 2. 优先级原则

按下面顺序推进：

1. 先拆“配置层”，让运行时不再依赖写死常量。
2. 再补“材料采集”，让主入口从一开始就是对话闭环。
3. 再补“用户模板创建与保存”，形成可复用能力。
4. 最后扩第二、第三个岗位模板，验证抽象是否成立。

## 3. Backlog

## P0 运行时解耦基础层

目标：

- 引入模板 schema、模板存储、模板解析能力
- 抽出 Android 首个 preset
- 让运行时常量开始从模板加载，而不是全部写死在代码里

任务：

- [x] 输出完整改造方案文档
- [x] 输出 backlog 文档
- [x] 新增模板 schema 定义
- [x] 新增 preset / user template 存储目录
- [x] 新增模板加载器
- [x] 新增模板解析器
- [x] 提供 Android 默认 preset
- [x] 让 `interview_core.py` 的轮次标签 / focus / persona 默认值来自模板
- [x] 让 `question_bank.py` 的 round / level 校验规则支持模板化
- [x] 补最小验证

验收标准：

- 仓库内存在正式 Android preset 文件
- 不改调用方式时，现有 Android 主链路行为不回归
- 运行时代码可以拿到“当前模板”的结构化配置

当前状态：

- `completed`

## P1 面试前材料采集闭环

目标：

- 在正式开始面试前，通过对话补齐 JD 和简历
- 支持本地路径、URL、直接粘贴文本三种方式

任务：

- [x] 新增 materials 标准结构
- [x] 新增 `material_collector.py` 基础能力
- [x] 在 references 中补充 `template_resolution -> material_collection -> profile_normalization`
- [x] 支持缺少 JD / 缺少简历时的脚本降级策略
- [x] 将材料信息写入 session / artifact metadata

验收标准：

- 用户不提供 JD / 简历时，系统会主动追问
- 只提供部分材料时，系统会明确提示精度影响

当前状态：

- `in_progress`

## P2 用户模板优先与本地复用

目标：

- 支持用户自定义模板本地落盘
- 同岗位模板冲突时优先使用用户模板

任务：

- [x] 新增 `data/user-templates/`
- [x] 支持 user template 覆盖 preset
- [x] 支持继承 preset 并覆写局部字段
- [x] 支持按 `template_id`、`display_name`、`aliases` 匹配
- [x] 在 session / artifact 中回显当前命中的模板来源

验收标准：

- 用户模板和预设模板同时存在时，会优先命中用户模板
- 用户模板可以被后续面试直接复用

当前状态：

- `in_progress`

## P3 自然语言创建模板

目标：

- 支持用户说“帮我新建一个岗位模板”，然后通过问答创建模板并保存

任务：

- [x] 新增最小 CLI 模板创建向导
- [ ] 设计必填字段采集顺序
- [x] 支持从预设模板继承
- [ ] 支持预览确认后保存
- [ ] 支持更新已有用户模板

验收标准：

- 用户可以通过对话创建模板并保存
- 模板保存前必须有预览和确认步骤

当前状态：

- `in_progress`

## P4 多岗位模板验证

目标：

- 验证通用架构不只适用于 Android

任务：

- [x] 增加 `backend_senior` preset
- [ ] 增加 `product_manager_senior` preset
- [x] 校验 intro / screening / round focus 是否仍可复用
- [x] 校验 question bank 规则是否能按模板切换

验收标准：

- 至少一个技术岗和一个非技术岗可以跑通主链路

当前状态：

- `in_progress`

## 4. 本轮开发范围

本轮已扩展到 `P0 + P1 + P2/P3/P4` 的一部分，具体包括：

1. backlog 落盘
2. 模板 schema 与模板加载 / 解析模块
3. Android preset 抽离
4. `interview_core.py`、`question_bank.py` 接入模板基础能力
5. 最小运行验证
6. 材料输入标准化基础能力
7. per-session 模板切换
8. 第二个技术岗 preset 与最小用户模板向导

## 5. 下一轮候选

优先考虑：

1. `P1` 材料采集
2. `P2` 用户模板优先级与本地复用
3. `P3` 模板创建向导
