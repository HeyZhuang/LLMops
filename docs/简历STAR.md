# 企业级 LLMOps 大模型应用开发运维平台 — 简历项目经历

> **技术栈**：Python Flask / LangGraph / LangChain / Weaviate / PostgreSQL / Redis / Celery / Vue 3 / TypeScript / Vue Flow / ECharts

---

## 一、完整 STAR 描述（面试口述版）

### STAR 1：多策略 AI Agent 智能体系统

- **S（情境）**：平台需要支持不同能力层级的大模型接入（部分模型支持原生 Function Call，部分不支持），且需要支持多 Agent 协作的复杂任务场景。
- **T（任务）**：设计并实现可扩展的多策略 Agent 框架，支持单 Agent 推理和多 Agent 协同编排，并实现 SSE 实时流式输出。
- **A（行动）**：
  - 基于 **LangGraph StateGraph** 设计 Agent 状态机架构，抽象 `BaseAgent` 基类（实现 LangChain Runnable 协议），派生出 `FunctionCallAgent`（原生工具调用）、`ReACTAgent`（推理-行动循环，手动解析 JSON 工具调用）、`SupervisorAgent`（多 Agent 监督编排）三种策略
  - 实现 **AgentQueueManager** 线程安全事件队列，工作线程执行 LangGraph 编译图，主线程通过 Generator 模式将 11 种事件类型（思维链、工具调用、知识库检索、Agent 委派等）实时推送为 SSE 流
  - SupervisorAgent 通过 LLM 动态路由选择子 Agent，转发子 Agent 事件流并标记来源，最终由 Synthesizer 节点综合生成回答
  - 集成输入审查（内容安全过滤）、长期记忆注入、Token 用量与成本实时追踪（input/output price 计算）
- **R（结果）**：实现了兼容 5 大模型提供商（OpenAI/Moonshot/通义/文心/Ollama）的统一 Agent 框架，支持有/无 Function Call 能力模型的无缝切换；多 Agent 协作模式使复杂任务的回答质量显著提升；流式架构实现了 600 秒长连接的稳定输出，每 10 秒心跳保活。

---

### STAR 2：可视化工作流引擎（DAG 编排系统）

- **S（情境）**：用户需要以低代码方式编排 AI 应用流程，将 LLM 推理、知识库检索、代码执行、API 调用等能力灵活组合。
- **T（任务）**：设计并实现支持 8 种节点类型的 DAG 工作流引擎，包含前端可视化编辑器和后端执行引擎。
- **A（行动）**：
  - 后端实现 `WorkflowConfig` 实体，包含完整的 **DAG 校验器**：BFS 连通性检测、Kahn 拓扑排序检测环路、节点输入变量引用合法性校验、入度/出度约束检查
  - 实现 8 种节点执行器（Start/End/LLM/Code/Tool/HttpRequest/DatasetRetrieval/TemplateTransform），每个节点继承 `RunnableSerializable`，通过状态归约器（reducer）合并输出，支持跨节点变量引用解析
  - Workflow 实现 `BaseTool` 接口，可作为 Agent 的工具被调用，实现 Agent + Workflow 嵌套编排
  - 前端基于 **Vue Flow + Dagre** 实现可视化编辑器，8 种自定义节点组件 + 8 种配置面板，支持自动层次布局、拖拽编辑、实时草稿保存、发布/草稿版本分离
- **R（结果）**：用户可通过拖拽方式构建复杂 AI 流水线，支持草稿实时编辑与一键发布；DAG 校验在编译阶段拦截了无效图结构（环路、断开节点、非法引用），保障了工作流运行时稳定性。

---

### STAR 3：混合检索 RAG 系统（语义 + 全文）

- **S（情境）**：平台的知识库问答场景需要高召回率和高精度的文档检索，单一检索策略（纯向量或纯关键词）无法满足中文场景需求。
- **T（任务）**：实现混合检索架构，结合语义向量检索和中文全文检索，并支持三级知识库结构（Dataset → Document → Segment）的精细化管理。
- **A（行动）**：
  - 实现 **SemanticRetriever**：基于 Weaviate 向量数据库进行相似度检索，构建复合过滤链（dataset_id + document_enabled + segment_enabled 三级开关），返回带相关性分数的文档
  - 实现 **FullTextRetriever**：使用 Jieba 中文分词提取查询关键词，查询 PostgreSQL JSONB 倒排索引表（KeywordTable），通过 Counter 频率排序实现 BM25 风格的关键词召回
  - 在 Agent 和 Workflow 的 DatasetRetrieval 节点中集成混合检索，支持 Cross-Encoder 重排序
  - 前端 `AgentThought` 组件实现 **知识库引用溯源**：结构化展示检索到的文档片段，显示来源数据集、文档名、相关度分数，实现回答可追溯
- **R（结果）**：混合检索策略相比单一语义检索提升了中文场景下的召回覆盖率；引用溯源功能让用户可验证 AI 回答的依据来源，增强了可信度；三级开关机制支持细粒度的知识库内容管控。

---

### STAR 4：全链路 Token 成本分析与运营数据看板

- **S（情境）**：企业使用大模型 API 面临成本不可控的痛点，需要对每个应用的 Token 消耗、调用量、用户活跃度进行量化分析。
- **T（任务）**：构建全链路 Token 成本追踪体系和数据分析看板，支持周环比趋势分析。
- **A（行动）**：
  - 在 Agent 的 LLM 节点中埋点追踪每次调用的 input_tokens、output_tokens，结合 `providers.yaml` 中各模型的定价元数据（input_price/output_price/unit）实时计算单次调用成本
  - 后端实现时间序列聚合：按日分组统计 5 大指标（消息总量、活跃用户、平均会话长度、Token 输出率、成本消耗），支持过去 7 天 vs 过去 14-7 天的**周环比（PoP）** 计算
  - 引入 Redis 缓存策略（按日+应用ID 为 key，24 小时过期），避免高频查询打爆数据库
  - 前端基于 ECharts 构建数据看板，5 个指标卡片（含环比涨跌箭头）+ 4 条趋势折线图 + 用户反馈满意率统计
  - 实现用户反馈系统（点赞/点踩），聚合计算满意率指标，形成质量+成本双维度运营视图
- **R（结果）**：实现了从模型调用到成本核算的全链路可观测性，管理者可按应用维度监控 Token 消耗趋势和周环比变化；Redis 缓存使分析接口响应时间从秒级降至毫秒级；反馈满意率指标为模型选型和 Prompt 优化提供了数据依据。

---

### STAR 5：多提供商大模型统一接入层

- **S（情境）**：平台需要对接国内外多家大模型提供商（OpenAI、Moonshot、通义千问、文心一言、Ollama 本地部署），各家 SDK 接口差异大，且需要在 Agent/Workflow 中灵活切换。
- **T（任务）**：设计 YAML 驱动的多模型统一抽象层，支持动态加载、特性探测（Function Call/多模态/思维链）和参数模板化。
- **A（行动）**：
  - 实现 **LanguageModelManager（单例）**，通过 `providers.yaml` 声明式注册提供商，动态导入各 Provider 的模型类（反射加载 `internal.core.language_model.providers.{provider}.{model_type}`）
  - 每个模型通过独立 YAML 配置文件定义：上下文窗口、最大输出 Token、参数模板、特性标签（TOOL_CALL / AGENT_THOUGHT / IMAGE_INPUT）、定价信息
  - Agent 框架根据模型 `features` 自动选择执行策略：有 TOOL_CALL 特性走 FunctionCallAgent，无则走 ReACTAgent
  - 实现 OpenAPI 3.0 动态工具生成器：解析 OpenAPI Spec，自动生成 Pydantic Schema 和 LangChain StructuredTool，支持 Path/Query/Header/Cookie/Body 五种参数位置
- **R（结果）**：新增模型提供商只需添加 YAML 配置和 Provider 类，无需修改框架代码；模型特性探测机制实现了 Agent 策略的自动适配；动态工具生成让用户可通过上传 OpenAPI 文档即可扩展 Agent 能力，极大降低了工具集成门槛。

---

## 二、简历精炼版（写在简历上）

### 多策略 AI Agent 智能体系统

- 基于 **LangGraph StateGraph** 设计三层 Agent 架构（FunctionCallAgent / ReACTAgent / SupervisorAgent），支持原生工具调用与推理-行动循环两种执行策略，根据模型特性自动适配
- 实现 **多 Agent 监督编排模式**：Supervisor 通过 LLM 动态路由分发子 Agent，转发事件流并标记来源，Synthesizer 节点综合生成最终回答
- 设计线程安全的 **AgentQueueManager** 事件队列，支持 11 种事件类型（思维链/工具调用/知识检索/Agent委派等），通过 Generator 模式实现 SSE 实时流式推送，600 秒长连接 + 10 秒心跳保活
- 集成输入内容安全审查、长期记忆注入、**Token 用量与成本实时计算**（按模型定价元数据计算单次调用成本）

### DAG 可视化工作流引擎

- 设计并实现支持 **8 种节点类型**（LLM/Code/Tool/HttpRequest/DatasetRetrieval/TemplateTransform/Start/End）的 DAG 执行引擎，每个节点实现 LangChain Runnable 协议，支持跨节点变量引用解析
- 实现完整的 **DAG 编译期校验**：BFS 连通性检测、Kahn 拓扑排序环路检测、节点输入变量引用合法性校验、入度/出度约束检查，编译阶段拦截无效图结构
- Workflow 实现 BaseTool 接口，可作为 Agent 工具被调用，实现 **Agent + Workflow 嵌套编排**
- 前端基于 **Vue Flow + Dagre** 构建可视化编辑器，8 种自定义节点组件与配置面板，支持自动层次布局、拖拽编辑、草稿/发布版本分离

### 混合检索 RAG 系统

- 实现 **双通道混合检索架构**：SemanticRetriever（Weaviate 向量检索 + 复合过滤链）+ FullTextRetriever（Jieba 中文分词 + JSONB 倒排索引 + 频率排序），配合 Cross-Encoder 重排序提升检索精度
- 设计三级知识库结构（Dataset → Document → Segment），支持文档/片段级别的独立启停开关，实现细粒度知识管控
- 前端实现 **知识库引用溯源**：结构化展示检索片段的来源数据集、文档名、相关度分数，增强 AI 回答可信度

### 全链路 Token 成本分析与运营看板

- 在 Agent LLM 节点埋点追踪 input/output tokens，结合 YAML 模型定价元数据实现**全链路成本核算**
- 后端实现时间序列聚合分析：5 大指标（消息量/活跃用户/会话长度/Token输出率/成本消耗）的按日统计与**周环比（PoP）**计算，Redis 缓存策略（日+应用维度 key，24h 过期）将接口响应从秒级降至毫秒级
- 前端基于 ECharts 构建数据看板（5 指标卡片 + 4 趋势图 + 满意率统计），集成用户反馈系统（点赞/点踩 + 满意率聚合），形成质量+成本双维度运营视图

### 多提供商大模型统一接入层与动态工具系统

- 设计 **YAML 驱动的多模型抽象层**（LanguageModelManager 单例），支持 OpenAI/Moonshot/通义/文心/Ollama 五大提供商，动态反射加载 Provider 类，新增提供商仅需配置无需改框架代码
- 每个模型声明式配置上下文窗口、参数模板、**特性标签**（TOOL_CALL/AGENT_THOUGHT/IMAGE_INPUT），Agent 框架据此自动选择执行策略
- 实现 **OpenAPI 3.0 动态工具生成器**：解析 OpenAPI Spec 自动生成 Pydantic Schema 与 LangChain StructuredTool，支持 Path/Query/Header/Cookie/Body 五种参数位置，用户上传 API 文档即可扩展 Agent 能力

---

## 三、简历一句话总结

> **企业级 LLMOps 平台** | 独立/核心开发
> 基于 LangGraph 实现多策略 Agent 框架（ReACT/FunctionCall/多Agent监督编排），设计 DAG 工作流引擎（8 种节点、拓扑校验、可视化编辑器），构建混合 RAG 检索系统（Weaviate 语义检索 + Jieba 全文检索 + 重排序），实现多提供商模型统一接入层与全链路 Token 成本追踪，支撑 SSE 实时流式交互。

---

## 四、技术亮点速查表（面试前快速过一遍）

| 面试考点 | 关键词回答 |
|---------|-----------|
| Agent 架构 | LangGraph StateGraph + 三策略派生（FunctionCall/ReACT/Supervisor） |
| 多 Agent 协作 | Supervisor 动态路由 → 子 Agent 执行 → 事件流转发 → Synthesizer 综合 |
| 流式输出 | 工作线程执行图 + 主线程 Queue Generator → SSE 推送，11 种事件类型 |
| RAG 方案 | 向量检索(Weaviate) + 全文检索(Jieba+倒排) + Cross-Encoder 重排序 |
| 工作流 | DAG 拓扑校验 + 8 种节点 Runnable + 变量引用解析 + Workflow 可作为 Tool |
| 模型管理 | YAML 声明式 + 反射加载 + 特性探测自动适配 Agent 策略 |
| 工具扩展 | 内置工具 + OpenAPI 3.0 动态解析生成 StructuredTool |
| 成本控制 | LLM 节点埋点 + 模型定价元数据 + 时序聚合 + Redis 缓存 |
| 前端架构 | Vue 3 Composition API + Hooks 分层 + Vue Flow 图编辑器 + SSE 流解析 |

---

## 五、使用建议

1. **简历上**：放「第二部分 精炼版」，控制在半页到一页
2. **面试时**：用「第一部分 完整 STAR」展开讲述，每个 STAR 控制在 2-3 分钟
3. **面试前**：快速浏览「第四部分 速查表」，确保关键技术点能脱口而出
4. **根据 JD 调整侧重**：
   - Agent/智能体岗 → 重点讲 STAR 1 + STAR 5
   - RAG/知识库岗 → 重点讲 STAR 3 + STAR 2
   - 全栈/平台岗 → 重点讲 STAR 2 + STAR 4
   - 大模型应用岗 → STAR 1 + STAR 3 + STAR 5 组合
