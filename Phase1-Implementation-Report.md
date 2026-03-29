# Phase 1 实现报告：核心差异化功能

> 实施日期：2026-03-18
> 状态：全部完成（5/5功能）

---

## 一、功能总览

| # | 功能模块 | 状态 | 后端新增 | 后端修改 | 前端新增 | 前端修改 |
|---|---------|------|---------|---------|---------|---------|
| 1 | 用户反馈系统 | ✅ | 5 | 2 | 3 | 2 |
| 2 | Token成本统计面板 | ✅ | 0 | 2 | 0 | 3 |
| 3 | 应用导入/导出 | ✅ | 3 | 0 | 4 | 1 |
| 4 | Prompt模板库 | ✅ | 5 | 0 | 7 | 3 |
| 5 | 知识库引用溯源 | ✅ | 0 | 1 | 0 | 1 |
| **合计** | | | **13** | **7** | **14** | **7** |

---

## 二、功能详情

### 功能 1：用户反馈系统（👍👎 + 反馈统计）

**数据模型 `MessageFeedback`：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 主键 |
| app_id | UUID | 关联应用 |
| conversation_id | UUID | 关联会话 |
| message_id | UUID | 关联消息 |
| rating | String(20) | `like` / `dislike` |
| content | Text | 用户反馈内容（可选） |
| created_by | UUID | 创建者 |
| created_at / updated_at | DateTime | 时间戳 |

**API端点（3个）：**

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/messages/<message_id>/feedback` | 创建/更新反馈 |
| GET | `/messages/<message_id>/feedback` | 获取反馈 |
| GET | `/apps/<app_id>/feedback-stats` | 获取应用反馈统计 |

**前端变更：**
- `AiMessage.vue` 底部添加👍👎按钮，点击即时提交
- `AnalysisView.vue` 新增反馈统计卡片（总反馈数、好评、差评、满意度）
- 消息响应中自动携带 `feedback` 字段

**文件清单：**
```
# 后端新增
internal/model/message_feedback.py
internal/handler/feedback_handler.py
internal/service/feedback_service.py
internal/schema/feedback_schema.py
internal/migration/versions/c4d5e6f7a8b9_.py

# 后端修改
internal/schema/app_schema.py          — 消息响应增加feedback字段+observation_data
internal/model/__init__.py             — 注册MessageFeedback

# 前端新增
src/models/feedback.ts
src/services/feedback.ts
src/hooks/use-feedback.ts

# 前端修改
src/components/AiMessage.vue           — 添加👍👎按钮
src/views/space/apps/AnalysisView.vue  — 添加反馈统计卡片
```

---

### 功能 2：Token成本统计面板

**API端点（1个）：**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/analysis/<app_id>/token-cost` | Token成本分析 |

**返回数据结构：**
```json
{
  "total_token_count": 12345,
  "total_cost": 0.0523,
  "avg_token_per_message": 456,
  "message_count": 27,
  "token_trend": { "x_axis": [...], "y_axis": [...] },
  "cost_trend": { "x_axis": [...], "y_axis": [...] }
}
```

**数据来源：** Message模型已有 `total_token_count`、`total_price` 字段，无需新表。

**前端变更：**
- `AnalysisView.vue` 新增三张统计卡片：总Token消耗、总费用(RMB)、平均每次Token

**文件清单：**
```
# 后端修改
internal/service/analysis_service.py   — 新增 get_token_cost_analysis()
internal/handler/analysis_handler.py   — 新增 get_token_cost_analysis 端点

# 前端修改
src/models/analysis.ts                 — 添加 GetTokenCostAnalysisResponse
src/services/analysis.ts               — 添加 getTokenCostAnalysis()
src/hooks/use-analysis.ts              — 添加 useGetTokenCostAnalysis
```

---

### 功能 3：应用导入/导出

**API端点（2个）：**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/apps/<app_id>/export` | 导出应用为JSON |
| POST | `/apps/import` | 从JSON导入应用 |

**导出JSON格式：**
```json
{
  "version": "1.0",
  "type": "app",
  "name": "应用名称",
  "description": "描述",
  "icon": "图标URL",
  "config": {
    "model_config": {},
    "preset_prompt": "",
    "dialog_round": 5,
    "tools": [], "workflows": [], "datasets": [],
    "retrieval_config": {}, "long_term_memory": {},
    "opening_statement": "", "opening_questions": [],
    "speech_to_text": {}, "text_to_speech": {},
    "suggested_after_answer": {}, "review_config": {},
    "multi_agent_config": {}
  },
  "exported_at": "2026-03-18T00:00:00"
}
```

**导入逻辑：**
- 验证JSON结构（version + type == "app"）
- 工具引用：内置工具保留，API工具校验存在性，不存在则跳过+返回warnings
- 知识库引用：校验存在性+权限，不存在则跳过+返回warnings
- 创建新App + AppConfigVersion(draft)

**前端变更：**
- `ListView.vue` 新增"导入应用"卡片 + 下拉菜单"导出应用"选项
- `ImportAppModal.vue` 文件选择 → 预览应用名称 → 确认导入

**文件清单：**
```
# 后端新增
internal/handler/app_export_handler.py
internal/service/app_export_service.py
internal/schema/app_export_schema.py

# 前端新增
src/models/app-export.ts
src/services/app-export.ts
src/hooks/use-app-export.ts
src/views/space/apps/components/ImportAppModal.vue

# 前端修改
src/views/space/apps/ListView.vue      — 导入卡片+导出菜单项
```

---

### 功能 4：Prompt模板库

**数据模型 `PromptTemplate`：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 主键 |
| account_id | UUID | 创建者 |
| name | String(255) | 模板名称 |
| description | Text | 描述 |
| content | Text | Prompt内容（支持`{{变量名}}`） |
| category | String(100) | 分类标签 |
| is_public | Boolean | 是否公开 |
| created_at / updated_at | DateTime | 时间戳 |

**API端点（5个）：**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/prompt-templates` | 分页列表（search_word + category） |
| POST | `/prompt-templates` | 创建模板 |
| GET | `/prompt-templates/<id>` | 获取详情 |
| POST | `/prompt-templates/<id>` | 更新模板 |
| POST | `/prompt-templates/<id>/delete` | 删除模板 |

**前端变更：**
- 新页面 `/space/prompt-templates`：模板卡片列表 + 搜索 + 创建/编辑/预览弹窗
- `SpaceLayoutView.vue` 顶部导航栏新增"Prompt模板"Tab
- `PresetPromptTextarea.vue` 新增"模板"按钮，下拉选择模板一键填入

**文件清单：**
```
# 后端新增
internal/model/prompt_template.py
internal/handler/prompt_template_handler.py
internal/service/prompt_template_service.py
internal/schema/prompt_template_schema.py
internal/migration/versions/d5e6f7a8b9c0_.py

# 前端新增
src/models/prompt-template.ts
src/services/prompt-template.ts
src/hooks/use-prompt-template.ts
src/views/space/prompt-templates/ListView.vue
src/views/space/prompt-templates/components/CreateOrUpdateTemplateModal.vue
src/views/space/prompt-templates/components/TemplatePreviewModal.vue

# 前端修改
src/router/index.ts                    — 添加 /space/prompt-templates 路由
src/views/space/SpaceLayoutView.vue    — 导航栏添加"Prompt模板"Tab
src/views/space/apps/components/PresetPromptTextarea.vue — "模板"选择按钮
```

---

### 功能 5：知识库引用溯源

**后端变更：**
- `app_schema.py` 的消息响应中，`agent_thoughts` 新增 `observation_data` 字段
- 新增 `_parse_observation()` 静态方法，将 `dataset_retrieval` 事件的 JSON observation 解析为结构化数组：`[{content, score}]`

**前端变更：**
- `AgentThought.vue` 中 `dataset_retrieval` 事件改为结构化引用卡片展示
- 每个引用片段显示：序号、内容（可折叠）、相似度分数
- 回退兼容：若无结构化数据，尝试解析 observation JSON

**文件清单：**
```
# 后端修改
internal/schema/app_schema.py          — observation_data + _parse_observation()

# 前端修改
src/components/AgentThought.vue        — 结构化引用卡片
```

---

## 三、数据库迁移链

```
775e752e0220 (已有)
  └── b3f5a8c61d42 (multi_agent_config，已有)
        └── c4d5e6f7a8b9 (message_feedback表，新增)
              └── d5e6f7a8b9c0 (prompt_template表，新增)
```

---

## 四、注册变更汇总

以下4个文件统一注册了3个新模块（Feedback、AppExport、PromptTemplate）：

| 文件 | 新增内容 |
|------|---------|
| `internal/model/__init__.py` | `MessageFeedback`, `PromptTemplate` |
| `internal/handler/__init__.py` | `FeedbackHandler`, `AppExportHandler`, `PromptTemplateHandler` |
| `internal/service/__init__.py` | `FeedbackService`, `AppExportService`, `PromptTemplateService` |
| `internal/router/router.py` | 18-20号模块路由（反馈3条、导入导出2条、模板5条、分析1条） |

---

## 五、验证步骤

### 功能1 — 用户反馈
1. 运行数据库迁移 `python migrate_db.py`
2. 在调试对话中发送消息，对AI回复点👍
3. 调用 `GET /apps/<id>/feedback-stats` 验证统计
4. 在分析页面查看反馈统计卡片

### 功能2 — Token成本
1. 调用 `GET /analysis/<app_id>/token-cost`
2. 验证返回 total_token_count、total_cost、趋势数据
3. 在 AnalysisView 中查看成本统计卡片

### 功能3 — 导入导出
1. 在应用列表中，点击更多菜单 → "导出应用"，下载JSON
2. 在应用列表中，点击"导入应用"卡片 → 选择JSON → 确认导入
3. 验证新应用配置与原应用一致

### 功能4 — Prompt模板
1. 运行数据库迁移
2. 进入个人空间 → "Prompt模板"Tab
3. 创建/编辑/删除模板
4. 在应用编排页 → 人设区域 → 点击"模板"按钮 → 选择模板

### 功能5 — 引用溯源
1. 配置知识库的应用，发起调试对话
2. 查看运行流程中"搜索知识库"步骤
3. 验证展示引用片段卡片（内容+相似度）

---

## 六、技术要点

- **依赖注入**：所有新Handler/Service遵循 `@inject @dataclass` 模式
- **三层架构**：Handler(参数校验) → Service(业务逻辑) → Model(ORM)
- **双框架验证**：FlaskForm+WTForms(请求) / Marshmallow(响应)
- **前端分层**：Models(类型) → Services(HTTP) → Hooks(状态+逻辑) → Views(组件)
- **无破坏性变更**：所有新功能为增量添加，不影响现有功能
