# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## 项目概述

**企业级LLMOps平台**——大语言模型应用开发与运维平台。前后端分离：后端Flask + 前端Vue 3。

核心能力：AI智能体(Agent)、知识库管理(Dataset)、工作流编排(Workflow)、工具集成(Tools)。

## 项目结构

```
LLMops/
├── imooc-llmops-api/imooc-llmops-api-master/    # 后端（Python Flask）
├── imooc-llmops-ui/imooc-llmops-ui-master/      # 前端（Vue 3 + TypeScript）
├── docker/docker/                               # Docker配置
│   ├── docker-compose-weaviate-only.yaml        # 仅Weaviate（开发推荐）
│   ├── docker-compose-local.yaml                # 本地开发配置
│   └── docker-compose.yaml                      # 完整服务栈（含API和UI容器）
├── start-local.bat / stop-local.bat             # 本地开发启停（本地PG+Redis，Docker仅Weaviate）
└── start.bat / stop.bat                         # 完整Docker栈启停
```

## 常用命令

### 后端（Flask）

```bash
cd imooc-llmops-api/imooc-llmops-api-master

# 虚拟环境
.venv\Scripts\Activate.ps1           # Windows PowerShell
source .venv/bin/activate            # Linux/Mac

# 启动服务
python -m app.http.app

# 测试（pytest.ini配置：addopts = -v -s）
pytest                                # 全部测试
pytest test/internal/xxx_test.py     # 单文件
pytest -k "test_name"                 # 按名称匹配

# 数据库
python init_db.py                     # 初始化表结构
python migrate_db.py                  # 迁移
python create_user.py                 # 创建用户

# Celery异步任务
celery -A app.http.app:celery worker --loglevel=info             # Linux/Mac
celery -A app.http.app:celery worker --loglevel=info --pool=solo # Windows
```

### 前端（Vue 3）

```bash
cd imooc-llmops-ui/imooc-llmops-ui-master

npm install                           # 安装依赖
npm run dev                           # 开发服务器 (localhost:5173)
npm run build                         # TypeScript检查 + 生产构建
npm run type-check                    # vue-tsc严格检查
npm run lint                          # ESLint + 自动修复
npm run format                        # Prettier格式化
npm run test:unit                     # Vitest单元测试
```

### Docker

```bash
cd docker/docker

# 开发环境（推荐）：仅Weaviate向量数据库
docker-compose -f docker-compose-weaviate-only.yaml up -d

# 完整服务栈（Weaviate + API + UI）
docker-compose up -d
```

## 后端架构

**三层分层架构 + 依赖注入**（injector库，配置在`app/http/module.py`）。

入口：`app/http/app.py` → `Http`类（继承Flask），依次初始化扩展、中间件、路由蓝图。

### 请求处理流程

```
请求 → Router(蓝图分发) → Middleware(认证) → Handler(参数校验) → Service(业务逻辑) → Model(ORM) → PostgreSQL
```

### 双蓝图认证机制

`internal/router/router.py` 注册两个蓝图，`internal/middleware/middleware.py` 根据蓝图选择认证方式：
- **`llmops`蓝图**：主业务路由（约460条），JWT Bearer Token认证
- **`openapi`蓝图**：外部API调用路由，API Key认证

### Schema验证模式

`internal/schema/` 使用两套验证框架：
- **请求验证**：FlaskForm + WTForms（`XxxReq`类，Handler中 `req.validate()`）
- **响应序列化**：Marshmallow（`XxxResp`类）

### 依赖注入模式

所有Handler、Service通过 `@inject @dataclass` 装饰器自动注入依赖。`ExtensionModule` 绑定 SQLAlchemy/Redis/LoginManager 等基础设施。

### Celery异步任务

`internal/extension/celery_extension.py` 定义 `FlaskTask` 确保任务在Flask上下文中执行。任务定义在 `internal/task/`（文档处理、知识库删除、自动创建应用等）。Redis作为broker和result backend。

### 核心模块 (`internal/core/`)

| 模块 | 关键类 | 说明 |
|------|--------|------|
| `agent/` | `BaseAgent` → `ReACTAgent`, `FunctionCallAgent` | LangGraph编译状态图，支持流式输出，`AgentQueueManager`管理事件队列 |
| `workflow/` | `Workflow(BaseTool)` | DAG状态图，节点类型：Start/End/LLM/Code/Tool/HttpRequest/DatasetRetrieval/TemplateTransform |
| `language_model/` | `LanguageModelManager(@singleton)` | 读取`providers.yaml`配置，支持OpenAI/Moonshot/Tongyi/Wenxin/Ollama |
| `tools/` | `BuiltinProviderManager`, `ApiProviderManager` | 内置工具（DuckDuckGo/天气/时间/Wikipedia/DALL-E3）+ OpenAPI 3.0动态生成工具 |
| `retrievers/` | `SemanticRetriever`, `BM25FullTextRetriever` | 混合检索：向量检索(Weaviate) + 关键字检索(jieba分词) + Cross-Encoder重排序 |
| `vector_store/` | Weaviate集成 | `similarity_search_with_relevance_scores`，按dataset/document/segment过滤 |
| `file_extractor/` | 多格式解析器 | PDF/Word/Excel/Markdown文件解析 |

### 数据模型 (`internal/model/`)

核心模型10个，UUID主键，JSONB字段存储复杂配置：
- **App** — 应用（关联AppConfig草稿/发布版本）
- **Workflow** — 工作流（draft_graph/published_graph为JSON）
- **Dataset/Document/Segment** — 知识库三级结构
- **Conversation/Message** — 会话和消息
- **Account** — 用户账户
- **ApiTool** — 自定义API工具（openapi_schema为JSONB）
- **ApiKey** — API访问密钥

关联关系通过Join表（如`AppDatasetJoin`）实现多对多。

## 前端架构

Vue 3 + TypeScript + Vite，四层清晰分层：

```
Views(页面组件) → Hooks(业务逻辑) → Services(HTTP调用) → Models(类型定义)
```

### 分层说明

- **`src/models/`**：TypeScript接口定义，`BaseResponse<T>`、`BasePaginatorRequest/Response<T>` 为通用类型
- **`src/services/`**：纯HTTP层，基于原生Fetch封装（`src/utils/request.ts`），支持SSE流式（`ssePost()`）和文件上传（`upload()`）
- **`src/hooks/`**：Composition API hooks（`use-xxx.ts`），封装状态管理+API调用+分页逻辑+错误处理，返回响应式ref和操作函数
- **`src/stores/`**：Pinia仅管理最小全局状态——`credential.ts`（JWT令牌）和 `account.ts`（用户信息），持久化到localStorage
- **`src/views/`**：按功能域组织页面，所有路由使用动态import懒加载

### SSE流式响应

`ssePost()` 处理AI对话流式输出，事件类型：`agent_thought`（思维链）、`agent_action`（工具调用）、`dataset_retrieval`（检索结果）、`agent_message`（最终回复）。

### 工作流设计器

`src/views/space/workflows/` 基于Vue Flow + dagre自动布局。8种自定义节点组件（`components/nodes/`），每个节点有对应的配置面板（`components/infos/`）。`src/utils/helper.ts` 提供图遍历算法（前驱节点查找、变量引用收集）。

### 路由认证

`router/index.ts` 的 `beforeEach` 守卫检查localStorage中JWT令牌过期时间，未登录重定向到 `/auth/login`。HTTP客户端401响应自动清除凭证并跳转登录。

### 关键依赖

- **UI**：Arco Design Vue 2.55.3
- **图编辑器**：@vue-flow/core 1.41.6
- **图表**：ECharts + vue-echarts
- **样式**：Tailwind CSS 3.4.4

## 环境配置

后端配置：`imooc-llmops-api/imooc-llmops-api-master/.env`（参考`.env.example`）

关键配置项：
- `SQLALCHEMY_DATABASE_URI`：PostgreSQL连接串
- `REDIS_HOST/PORT`：Redis（同时用作Celery broker）
- `WEAVIATE_HOST/PORT`：向量数据库（默认8080）
- `JWT_SECRET_KEY`：JWT签名密钥
- LLM提供商密钥：`OPENAI_API_KEY/OPENAI_API_BASE`、`qianfan_ak/qianfan_sk`、`MOONSHOT_API_KEY`、`DASHSCOPE_API_KEY`
- 工具API：`GAODE_API_KEY`（高德地图）、`SERPER_API_KEY`（Google搜索）
- 对象存储：`COS_SECRET_ID/KEY/REGION/BUCKET`（腾讯云COS）

前端配置：通过Vite环境变量 `VITE_API_PREFIX` 设置API前缀。

## 访问地址

- 前端：http://localhost:5173
- 后端API：http://localhost:5000（Docker中为8000）
- Weaviate：http://localhost:8080

## 环境要求

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+
- Docker 20.10+（用于Weaviate向量数据库）
