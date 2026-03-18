# Multi-Agent Supervisor 多智能体协作系统 — 技术实现文档

## 一、功能概述

在现有 LLMOps 平台的单 Agent 模式（FunctionCallAgent / ReACTAgent）基础上，新增 **Supervisor 多智能体协作系统**：

- 一个 **主管 Agent（Supervisor）** 分析用户意图，动态选择最合适的 **专业子 Agent** 执行任务
- 子 Agent 执行完毕后，Supervisor 综合其结果生成最终回复
- 全程通过 SSE 实时展示调度与协作过程

这是当前 Agent 领域最热门的架构模式之一（LangGraph 官方推荐的 Supervisor 模式）。

---

## 二、核心架构设计

### 2.1 整体调度流程

```
用户提问
   │
   ▼
┌──────────────────┐
│  preset_operation │  ← 输入审核（敏感词过滤）
└────────┬─────────┘
         │ 通过审核
         ▼
┌──────────────────────┐
│  supervisor_router   │  ← Supervisor LLM 通过 bind_tools() 选择子Agent
└────────┬─────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
 有tool_call  无tool_call
    │         │
    ▼         ▼
┌──────────┐  直接回答 → END
│sub_agent  │
│  _node   │  ← 创建子Agent，执行并收集结果
└────┬─────┘
     │
     ▼
┌──────────────┐
│ synthesizer  │  ← Supervisor LLM 综合子Agent结果，生成最终回复
│   _node      │
└────┬─────────┘
     │
     ▼
    END
```

### 2.2 关键设计决策

| 决策点 | 方案 | 原因 |
|--------|------|------|
| 子Agent如何暴露给Supervisor | 每个子Agent包装为 `@tool`，通过 `bind_tools()` 绑定 | LLM 原生的 function calling 能力，自然选择最合适的子Agent |
| 子Agent内部实现 | 复用现有 FunctionCallAgent / ReACTAgent | 避免重复造轮子，子Agent拥有完整的工具调用能力 |
| 事件流转发 | 子Agent事件带 `sub_agent_name` 标记转发到Supervisor队列 | SSE 实时展示子Agent的完整思维过程 |
| 向后兼容 | `multi_agent_config` 默认 `{"enable": false}` | 不影响任何已有的单Agent应用 |

### 2.3 数据流向

```
前端配置 multi_agent_config（sub_agents列表）
        │
        ▼
后端 AppService.debug_chat() 判断 enable 字段
        │
   ┌────┴────┐
   │         │
enable=true  enable=false
   │         │
   ▼         ▼
SupervisorAgent  原有 FunctionCallAgent/ReACTAgent（完全不变）
   │
   ▼
SSE 事件流（含 agent_delegation / sub_agent_end 新事件）
        │
        ▼
前端 AgentThought 组件展示调度过程
```

---

## 三、文件变更清单

### 3.1 新建文件（2个）

| 文件路径 | 说明 | 行数 |
|----------|------|------|
| `internal/core/agent/agents/supervisor_agent.py` | SupervisorAgent 核心类 | ~430 |
| `src/views/space/apps/components/abilities/MultiAgentAbilityItem.vue` | 多Agent配置UI组件 | ~210 |

### 3.2 修改文件（13个）

| 文件路径 | 修改内容 |
|----------|----------|
| `internal/core/agent/entities/agent_entity.py` | +3个类：`SubAgentConfig`、`SupervisorAgentConfig`、`SupervisorAgentState`；+2个提示词模板 |
| `internal/core/agent/entities/queue_entity.py` | `QueueEvent` +2个枚举值；`AgentThought` +`sub_agent_name`字段 |
| `internal/core/agent/agents/__init__.py` | 导出 `SupervisorAgent` |
| `internal/entity/app_entity.py` | `DEFAULT_APP_CONFIG` +`multi_agent_config`默认配置 |
| `internal/model/app.py` | `AppConfig` & `AppConfigVersion` +`multi_agent_config` JSONB列 |
| `internal/migration/versions/b3f5a8c61d42_.py` | 数据库迁移脚本 |
| `internal/service/app_config_service.py` | `_process_and_transformer_app_config` 返回结果包含 `multi_agent_config` |
| `internal/service/app_service.py` | `debug_chat()` 分支判断；`_validate_draft_app_config` 新增校验；`publish_draft_app_config` 包含新字段；SSE 输出包含 `sub_agent_name` |
| `internal/schema/app_schema.py` | agent_thoughts 序列化新增 `sub_agent_name` 字段 |
| `src/models/app.ts` | +`SubAgentConfig`、`MultiAgentConfig`类型；响应/请求结构新增字段 |
| `src/config/index.ts` | `QueueEvent` +`agentDelegation`、`subAgentEnd` |
| `src/hooks/use-app.ts` | `loadDraftAppConfig` 数据映射新增 `multi_agent_config` |
| `src/views/space/apps/components/AgentAppAbility.vue` | 引入并渲染 `MultiAgentAbilityItem` |
| `src/components/AgentThought.vue` | 处理新事件类型，子Agent名称前缀标签，面板宽度增至360px |
| `src/views/space/apps/components/PreviewDebugChat.vue` | SSE事件处理新增 `sub_agent_name` 字段 |

---

## 四、后端实现细节

### 4.1 实体层新增

**`agent_entity.py` 新增类：**

```python
class SubAgentConfig(BaseModel):
    """子Agent配置"""
    name: str                    # 唯一名称，如 "code_expert"
    description: str             # 能力描述（Supervisor据此选择）
    model_config_data: dict      # {provider, model, parameters}
    preset_prompt: str = ""
    tools: list[BaseTool] = []
    max_iteration_count: int = 5

class SupervisorAgentConfig(AgentConfig):
    """继承AgentConfig，新增sub_agents"""
    system_prompt: str = SUPERVISOR_SYSTEM_PROMPT_TEMPLATE
    sub_agents: list[SubAgentConfig] = []

class SupervisorAgentState(AgentState):
    """继承AgentState，新增调度状态"""
    current_sub_agent: str = ""    # 当前执行的子Agent名称
    sub_agent_result: str = ""     # 子Agent返回的结果
```

**`queue_entity.py` 新增：**

```python
# QueueEvent 枚举新增
AGENT_DELEGATION = "agent_delegation"  # 子Agent调度事件
SUB_AGENT_END = "sub_agent_end"        # 子Agent结束事件

# AgentThought 新增字段
sub_agent_name: str = ""  # 子Agent名称（多智能体模式下使用）
```

### 4.2 SupervisorAgent 核心实现

**类继承关系：**
```
Serializable + Runnable
      │
  BaseAgent（抽象基类）
   ├── FunctionCallAgent
   ├── ReACTAgent
   └── SupervisorAgent  ← 新增
```

**四个核心节点：**

#### 节点1：`_preset_operation_node` — 输入审核
- 复用 FunctionCallAgent 的审核逻辑
- 检测敏感词，命中则直接返回预设响应并结束

#### 节点2：`_supervisor_router_node` — 智能调度
```python
# 1. 将每个子Agent包装为LangChain工具
sub_agent_tools = self._build_sub_agent_tools()

# 2. Supervisor LLM 绑定工具并调用
llm = self.llm.bind_tools(sub_agent_tools)
response = llm.stream(messages)

# 3. 如果LLM返回tool_calls → 选择了子Agent
#    如果LLM直接生成文本 → 简单问题，直接回答
```

**子Agent工具构建方式：**
```python
@staticmethod
def _create_sub_agent_tool(name: str, description: str) -> BaseTool:
    @tool(name, return_direct=False)
    def delegate_to_sub_agent(query: str) -> str:
        """委派任务给子Agent"""
        return query
    delegate_to_sub_agent.description = description
    return delegate_to_sub_agent
```

#### 节点3：`_sub_agent_node` — 子Agent执行
```python
# 1. 根据 state["current_sub_agent"] 找到对应配置
# 2. 加载子Agent专属LLM（可独立配置模型）
# 3. 创建 FunctionCallAgent 或 ReACTAgent 实例
# 4. 调用 sub_agent.stream() 获取流式结果
# 5. 转发所有事件到Supervisor的队列（带sub_agent_name标记）
# 6. 收集完整answer存入 state["sub_agent_result"]
```

**事件转发关键代码：**
```python
for agent_thought in sub_agent.stream({...}):
    if agent_thought.event != QueueEvent.PING and agent_thought.event != QueueEvent.AGENT_END:
        forwarded_thought = agent_thought.model_copy(update={
            "sub_agent_name": sub_agent_name,  # 标记来源
        })
        self.agent_queue_manager.publish(state["task_id"], forwarded_thought)
```

#### 节点4：`_synthesizer_node` — 综合回复
```python
# Supervisor LLM 接收子Agent结果，生成最终用户回复
synthesizer_prompt = SUPERVISOR_SYNTHESIZER_PROMPT_TEMPLATE.format(
    sub_agent_name=sub_agent_name,
    sub_agent_result=sub_agent_result,
)
# 流式输出最终回答
```

### 4.3 Service 层集成

**`app_service.py` — `debug_chat()` 分支判断：**

```python
multi_agent_config = draft_app_config.get("multi_agent_config", {})
if multi_agent_config.get("enable") and multi_agent_config.get("sub_agents"):
    # 构建 SubAgentConfig 列表（包括工具、知识库、工作流）
    # 创建 SupervisorAgent
    agent = SupervisorAgent(
        llm=llm,
        agent_config=SupervisorAgentConfig(..., sub_agents=sub_agent_configs),
        language_model_service=self.language_model_service,
    )
else:
    # 原有单Agent逻辑（完全不变）
    agent_class = FunctionCallAgent if ModelFeature.TOOL_CALL in llm.features else ReACTAgent
    agent = agent_class(llm=llm, agent_config=AgentConfig(...))
```

**SSE 输出新增 `sub_agent_name`：**
```python
data = {
    **agent_thought.model_dump(include={
        "event", "thought", "observation", "tool", "tool_input",
        "answer", "total_token_count", "total_price", "latency",
        "sub_agent_name",  # 新增
    }),
    ...
}
```

**`_validate_draft_app_config()` 新增校验：**
- `enable` 必须是布尔值
- `sub_agents` 必须是列表
- 启用时至少2个、最多5个子Agent
- 每个子Agent的 `name` 唯一性校验
- 模型配置宽松校验（无效则用默认值）

### 4.4 数据库变更

```sql
-- 迁移脚本 b3f5a8c61d42_.py
ALTER TABLE app_config ADD COLUMN multi_agent_config JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE app_config_version ADD COLUMN multi_agent_config JSONB NOT NULL DEFAULT '{}'::jsonb;
```

**`multi_agent_config` JSON 结构：**
```json
{
  "enable": true,
  "sub_agents": [
    {
      "name": "code_expert",
      "description": "擅长处理编程相关问题，包括代码编写、调试、算法设计",
      "model_config": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "parameters": { "temperature": 0.5 }
      },
      "preset_prompt": "你是一个资深的编程专家...",
      "tools": [],
      "workflows": [],
      "datasets": [],
      "max_iteration_count": 5
    },
    {
      "name": "writing_expert",
      "description": "擅长文案写作、内容创作、文章润色",
      "model_config": { "provider": "openai", "model": "gpt-4o-mini", "parameters": {} },
      "preset_prompt": "你是一个专业的写作助手...",
      "tools": [],
      "workflows": [],
      "datasets": [],
      "max_iteration_count": 5
    }
  ]
}
```

---

## 五、前端实现细节

### 5.1 类型定义

```typescript
// 子Agent配置类型
export type SubAgentConfig = {
  name: string
  description: string
  model_config: { provider: string; model: string; parameters: Record<string, any> }
  preset_prompt: string
  tools: GetDraftAppConfigResponse['data']['tools']
  workflows: { id: string; name: string; icon: string; description: string }[]
  datasets: { id: string; name: string; icon: string; description: string }[]
  max_iteration_count: number
}

// 多Agent配置类型
export type MultiAgentConfig = {
  enable: boolean
  sub_agents: SubAgentConfig[]
}
```

### 5.2 配置组件（MultiAgentAbilityItem.vue）

遵循现有 `ToolsAbilityItem.vue` 模式：

- **折叠面板**：标题"多智能体协作"，右侧开关切换启用/禁用
- **子Agent列表**：每个卡片显示名称首字母头像 + 名称 + 描述，hover 显示设置/删除按钮
- **添加按钮**：底部虚线按钮，限制最多5个
- **编辑模态窗**：包含名称、描述、模型配置、预设提示词、最大迭代次数滑块

### 5.3 SSE 事件类型新增

```typescript
export const QueueEvent = {
  // ...原有事件
  agentDelegation: 'agent_delegation',  // 新增：调度子Agent
  subAgentEnd: 'sub_agent_end',          // 新增：子Agent完成
}
```

### 5.4 AgentThought 组件更新

| 事件 | 图标 | 标签文本 |
|------|------|----------|
| `agent_delegation` | `<icon-swap>` | "调度子Agent: {sub_agent_name}" |
| `sub_agent_end` | `<icon-check-circle>` | "{sub_agent_name} 完成" |

对已有事件（agentThought、agentAction、datasetRetrieval、agentMessage），如果 `sub_agent_name` 不为空，header 显示 `[子Agent名称]` 前缀：

```
[code_expert] 智能体推理
[code_expert] 调用工具
[code_expert] 智能体消息
```

---

## 六、SSE 事件流示例

用户提问"请帮我写一段Python排序算法"时的完整事件流：

```
event: agent_delegation
data: {"event":"agent_delegation", "thought":"将任务分配给子Agent: code_expert", "sub_agent_name":"code_expert", ...}

event: agent_thought
data: {"event":"agent_thought", "thought":"[工具调用参数]", "sub_agent_name":"code_expert", ...}

event: agent_action
data: {"event":"agent_action", "tool":"google_serper", "sub_agent_name":"code_expert", ...}

event: agent_message
data: {"event":"agent_message", "thought":"这是子Agent生成的...", "sub_agent_name":"code_expert", ...}

event: sub_agent_end
data: {"event":"sub_agent_end", "thought":"子Agent code_expert 完成", "sub_agent_name":"code_expert", ...}

event: agent_message
data: {"event":"agent_message", "thought":"以下是排序算法的实现...", "sub_agent_name":"", ...}

event: agent_end
data: {"event":"agent_end", ...}
```

---

## 七、向后兼容保障

| 场景 | 行为 |
|------|------|
| 已有应用未配置 `multi_agent_config` | 数据库默认 `{}`，代码回退到 `DEFAULT_APP_CONFIG` 默认值 `{"enable": false}` |
| 已有应用 `enable=false` | `debug_chat()` 走原有单Agent分支，逻辑完全不变 |
| 前端加载旧配置无 `multi_agent_config` | hooks 中 `data.multi_agent_config \|\| { enable: false, sub_agents: [] }` 兜底 |
| 数据库旧记录无新列 | 迁移脚本 `server_default='{}'::jsonb` 确保旧数据兼容 |

---

## 八、验证方案

### 8.1 数据库迁移验证
```bash
cd imooc-llmops-api/imooc-llmops-api-master
# 执行迁移
flask db upgrade
# 验证新列
psql -c "SELECT column_name FROM information_schema.columns WHERE table_name='app_config' AND column_name='multi_agent_config';"
```

### 8.2 后端功能验证
1. 启动后端服务：`python -m app.http.app`
2. 通过 API 更新草稿配置，启用多Agent + 2个子Agent
3. 调用 `debug_chat` 接口，验证 SSE 流中包含 `agent_delegation` 和 `sub_agent_end` 事件

### 8.3 前端 E2E 验证
1. 启动前端：`npm run dev`
2. 进入应用详情页 → 应用能力 → 展开"多智能体协作"
3. 添加2个子Agent（如 code_expert、writing_expert）
4. 开启总开关
5. 在调试对话中发送问题，确认运行流程面板显示调度过程

### 8.4 向后兼容验证
- 未启用多Agent的应用仍然正常工作（debug_chat 走原有单Agent路径）
- 旧数据不受影响

---

## 九、后续扩展方向

1. **多轮调度**：支持 Supervisor 连续调用多个子Agent，汇总多个结果
2. **子Agent工具/知识库配置UI**：在模态窗中集成现有的工具选择和知识库选择组件
3. **调度策略可选**：除 Supervisor 模式外，支持 Round-Robin、Pipeline 等模式
4. **子Agent间通信**：支持子Agent之间传递上下文信息
5. **运行统计**：记录各子Agent的调用频次、耗时、Token消耗
6. **OpenAPI 支持**：在 `openapi` 蓝图中也支持多Agent模式
