# Agent 智能体编排工作原理详解

> 基于 LangGraph 状态图的 Agent 执行引擎，涵盖状态图构建、四节点工作流、双线程流式架构、Token 计算与事件队列全链路。

---

## 目录

1. [整体架构](#1-整体架构)
2. [类继承关系](#2-类继承关系)
3. [状态图构建](#3-状态图构建)
4. [AgentState 状态定义](#4-agentstate-状态定义)
5. [四个节点详解](#5-四个节点详解)
6. [双线程 + 队列的流式架构](#6-双线程--队列的流式架构)
7. [AgentQueueManager 事件队列管理器](#7-agentqueuemanager-事件队列管理器)
8. [完整对话执行流程示例](#8-完整对话执行流程示例)
9. [Token 计算与费用链路](#9-token-计算与费用链路)
10. [FunctionCall vs ReACT 双模式对比](#10-functioncall-vs-react-双模式对比)
11. [关键设计要点](#11-关键设计要点)
12. [关键文件索引](#12-关键文件索引)

---

## 1. 整体架构

Agent 基于 **LangGraph 状态图**构建，本质是一个有 4 个节点 + 2 个条件边的有向图，运行在子线程中，通过 Python `Queue` 队列向主线程推送事件流。

```
用户提问
  ↓
BaseAgent.stream()
  ├── 子线程：执行 LangGraph 编译状态图（preset → memory → llm ⇄ tools → END）
  └── 主线程：AgentQueueManager.listen() 监听队列，yield 事件给调用方
       ↓
  SSE 流式推送给前端
       ↓
  后台线程持久化到 Message / MessageAgentThought 表
       ↓
  AnalysisService 聚合查询生成统计数据
```

---

## 2. 类继承关系

```
BaseAgent (Serializable, Runnable)           ← 抽象基类，定义 stream/invoke 方法
│
│   核心属性：
│   ├── llm: BaseLanguageModel               ← LLM 实例
│   ├── agent_config: AgentConfig            ← 配置（工具、提示词、最大迭代次数等）
│   ├── _agent: CompiledStateGraph           ← LangGraph 编译后的状态图
│   └── _agent_queue_manager: AgentQueueManager  ← 事件队列管理器
│
├── FunctionCallAgent                        ← 原生工具调用（LLM 支持 tool_call 特性时用）
│     实现 _build_agent() 构建4节点状态图
│     实现 4个节点方法 + 2个条件边方法
│
└── ReACTAgent(FunctionCallAgent)            ← Prompt 驱动工具调用（任何 LLM 都能用）
      重写 _long_term_memory_recall_node()   ← 往 SystemMessage 注入工具描述
      重写 _llm_node()                      ← 通过解析输出前7字符判断是否为工具调用
```

**文件位置**：
- `internal/core/agent/agents/base_agent.py`
- `internal/core/agent/agents/function_call_agent.py`
- `internal/core/agent/agents/react_agent.py`

---

## 3. 状态图构建

`function_call_agent.py:36-57` — `_build_agent()` 方法：

```python
graph = StateGraph(AgentState)

# 添加4个节点
graph.add_node("preset_operation", self._preset_operation_node)
graph.add_node("long_term_memory_recall", self._long_term_memory_recall_node)
graph.add_node("llm", self._llm_node)
graph.add_node("tools", self._tools_node)

# 设置入口 + 边
graph.set_entry_point("preset_operation")
graph.add_conditional_edges("preset_operation", self._preset_operation_condition)
graph.add_edge("long_term_memory_recall", "llm")        # 固定边
graph.add_conditional_edges("llm", self._tools_condition)
graph.add_edge("tools", "llm")                          # 固定边（工具执行后回到LLM）

agent = graph.compile()
```

**图结构：**

```
                 ┌──────────────────────┐
        入口 ──→ │  preset_operation     │  预设操作（输入审核）
                 └──────────┬───────────┘
                            │
               _preset_operation_condition（条件边）
                     │              │
              触发敏感词          正常通过
                     │              │
                     ▼              ▼
                   END    ┌─────────────────────────┐
                          │ long_term_memory_recall   │  长期记忆召回 + 消息组装
                          └────────────┬──────────────┘
                                       │
                              固定边（直接连接）
                                       │
                              ┌────────▼────────┐
                     ┌───────→│      llm         │  调用 LLM（流式推理）
                     │        └────────┬─────────┘
                     │                 │
                     │       _tools_condition（条件边）
                     │          │              │
                     │    有 tool_calls    无 tool_calls
                     │          │              │
                     │          ▼              ▼
                     │   ┌──────────┐       END（最终回答）
                     └───│  tools    │  执行工具，结果回传给 LLM
                         └──────────┘
```

**核心环路**：`llm → tools → llm → tools → ... → END`

LLM 每次推理后，条件边检查输出中是否有 `tool_calls`：
- 有 → 执行工具 → 工具结果作为 ToolMessage 回传 → 再次调用 LLM
- 无 → 说明 LLM 已给出最终回答 → 结束

---

## 4. AgentState 状态定义

`agent_entity.py:122-127`：

```python
class AgentState(MessagesState):     # 继承 LangGraph 的 MessagesState，自带 messages 字段
    task_id: UUID                    # 任务ID，用于队列事件关联
    iteration_count: int             # 当前迭代次数（防止无限循环，默认最大5次）
    history: list[AnyMessage]        # 短期记忆（历史对话，[HumanMessage, AIMessage, ...]）
    long_term_memory: str            # 长期记忆（会话摘要文本）
```

`messages` 是 LangGraph 内置的消息列表，各节点通过返回 `{"messages": [...]}` 来追加消息，图自动管理消息的累积和传递。

---

## 5. 四个节点详解

### 节点一：`preset_operation` — 输入审核

**文件**：`function_call_agent.py:59-87`

**职责**：检查用户输入是否包含敏感词，如果命中则直接返回预设回复，跳过后续所有节点。

```
用户输入 query
  ↓
review_config.enable && inputs_config.enable ?
  ├── 是 → 遍历 keywords 列表
  │    ├── query 包含敏感词 →  发布 AGENT_MESSAGE(preset_response) + AGENT_END
  │    │                       返回 AIMessage(preset_response)
  │    └── 不包含 → 返回空消息列表 {"messages": []}
  └── 否 → 返回空消息列表 {"messages": []}
```

**条件边** `_preset_operation_condition`（第340-349行）：
- 最后一条消息是 `AIMessage` → 说明触发了审核 → `END`
- 否则 → `"long_term_memory_recall"`

### 节点二：`long_term_memory_recall` — 消息组装

**文件**：`function_call_agent.py:89-130`

**职责**：这是最关键的"准备"步骤——组装发给 LLM 的完整消息列表。

```
执行流程：

1. 检查是否开启长期记忆
   └── 是 → 发布 LONG_TERM_MEMORY_RECALL 事件（含长期记忆内容）

2. 构建 SystemMessage：
   将 preset_prompt（预设提示词）和 long_term_memory（长期记忆）
   填充到 AGENT_SYSTEM_PROMPT_TEMPLATE 模板中

3. 拼接短期记忆 history
   └── 校验消息必须成对（[Human, AI, Human, AI, ...]）

4. 拼接当前用户的提问 HumanMessage

5. 用 RemoveMessage 删除原始用户消息，替换为组装好的完整消息序列
```

组装后的 `messages` 结构：

```
[
  SystemMessage("你是一个高度定制的智能体应用...
                 <预设提示>{preset_prompt}</预设提示>
                 <长期记忆>{long_term_memory}</长期记忆>"),
  HumanMessage("历史问题1"),       ← 短期记忆
  AIMessage("历史回答1"),
  HumanMessage("历史问题2"),
  AIMessage("历史回答2"),
  HumanMessage("当前用户提问"),     ← 本次输入
]
```

### 节点三：`llm` — LLM 推理

**文件**：`function_call_agent.py:132-276`

**职责**：调用 LLM 流式推理，判断输出是"工具调用"还是"直接回答"，并计算 Token 消耗。

**完整步骤：**

```
1. 迭代次数检查
   iteration_count > max_iteration_count(默认5)?
   └── 是 → 发布 AGENT_MESSAGE("迭代次数已超过限制") + AGENT_END → 返回

2. 工具绑定
   LLM 支持 TOOL_CALL 特性 && 工具列表非空?
   └── 是 → llm = llm.bind_tools(self.agent_config.tools)

3. 流式调用 llm.stream(state["messages"])
   逐 chunk 处理：
   ┌──────────────────────────────────────────────────────────┐
   │ 第一个 chunk 判断 generation_type：                        │
   │   ├── chunk.tool_calls 非空 → type = "thought"（要调工具） │
   │   └── chunk.content 非空   → type = "message"（直接回答） │
   │                                                          │
   │ 后续 chunk：                                              │
   │   ├── type == "message"                                  │
   │   │    → 每个 chunk 实时发布 AGENT_MESSAGE 事件            │
   │   │      （流式推送给前端，同时做输出审核：敏感词替换为 "**"）│
   │   └── type == "thought"                                  │
   │        → 只聚合不发送，等流式结束后统一发布                  │
   │                                                          │
   │ 所有 chunk 聚合到 gathered 变量                            │
   └──────────────────────────────────────────────────────────┘

4. 流式结束后，计算 Token 和费用（详见第9节）

5. 发布最终事件（附带 Token 数据）：
   ├── type == "thought"
   │    → 发布 AGENT_THOUGHT（thought = tool_calls JSON，携带 Token+Price）
   └── type == "message"
        → 发布 AGENT_MESSAGE（携带 Token+Price 汇总）
        → 发布 AGENT_END（终止信号）

6. 返回 {"messages": [gathered], "iteration_count": state["iteration_count"] + 1}
```

**条件边** `_tools_condition`（第326-337行）：
- `ai_message.tool_calls` 非空 → `"tools"`
- 否则 → `END`

### 节点四：`tools` — 工具执行

**文件**：`function_call_agent.py:278-324`

**职责**：根据 LLM 的 tool_calls 指令执行对应工具，将结果作为 ToolMessage 回传。

```
1. 构建工具字典：{tool.name: tool_instance}

2. 从最后一条 AI 消息中提取 tool_calls 列表

3. 循环执行每个工具调用：
   for tool_call in tool_calls:
     ├── 查找工具：tools_by_name[tool_call["name"]]
     ├── 执行工具：tool.invoke(tool_call["args"])
     │    └── 异常时返回 "工具执行出错: {error}"
     ├── 构建 ToolMessage（包含工具返回结果）
     └── 发布事件：
         ├── 工具名 == "dataset_retrieval" → DATASET_RETRIEVAL 事件
         └── 其他工具 → AGENT_ACTION 事件
         （事件包含：工具名、输入参数、执行结果、耗时）

4. 返回 {"messages": [ToolMessage, ToolMessage, ...]}
```

执行完后通过固定边 `tools → llm` 回到 LLM 节点。LLM 会看到 ToolMessage 中的工具执行结果，基于此决定：继续调工具，还是生成最终回答。

---

## 6. 双线程 + 队列的流式架构

`base_agent.py:106-130` — `stream()` 方法：

```python
def stream(self, input: AgentState, config=None) -> Iterator[AgentThought]:
    # 1. 初始化任务数据
    input["task_id"] = uuid.uuid4()
    input["history"] = input.get("history", [])
    input["iteration_count"] = 0

    # 2. 创建子线程执行 LangGraph 状态图
    thread = Thread(target=self._agent.invoke, args=(input,))
    thread.start()

    # 3. 主线程监听队列，yield 事件
    yield from self._agent_queue_manager.listen(input["task_id"])
```

**为什么用子线程+队列，而不是直接 yield？**

LangGraph 的 `invoke()` 是**阻塞的**——从入口节点一直执行到 END 才返回。但我们需要在执行过程中**实时推送中间事件**（思维链、工具调用、每个 token）给前端。

解决方案：
- **子线程**：运行 LangGraph 状态图，各节点通过 `publish()` 把事件塞进队列
- **主线程**：`listen()` 从队列 yield 事件，转为 SSE 流推送给前端

```
主线程                              子线程
  │                                  │
  │  stream() 被调用                  │
  │    ├── 生成 task_id              │
  │    ├── Thread.start() ───────────────→ 启动子线程
  │    └── yield from listen()        │     执行 LangGraph 状态图
  │         │                         │         │
  │    等待队列数据                      │    节点执行过程中 publish() 往队列塞事件
  │         │                         │         │
  │    ← AgentThought(LONG_TERM...)  ←──── publish(LONG_TERM_MEMORY_RECALL)
  │    ← AgentThought(AGENT_MESSAGE) ←──── publish(AGENT_MESSAGE) × N个chunk
  │    ← AgentThought(AGENT_THOUGHT) ←──── publish(AGENT_THOUGHT) 工具调用决策
  │    ← AgentThought(AGENT_ACTION)  ←──── publish(AGENT_ACTION) 工具执行结果
  │    ← AgentThought(AGENT_MESSAGE) ←──── publish(AGENT_MESSAGE) 最终回答
  │    ← AgentThought(AGENT_END)     ←──── publish(AGENT_END) → stop_listen()
  │    ← None (队列结束)               │
  │                                    │
  ▼  yield 给 SSE 响应                  ▼  线程退出
```

---

## 7. AgentQueueManager 事件队列管理器

**文件**：`internal/core/agent/agents/agent_queue_manager.py`

### 7.1 核心数据结构

```python
class AgentQueueManager:
    user_id: UUID                    # 当前用户ID
    invoke_from: InvokeFrom          # 调用来源（DEBUGGER/WEB_APP/SERVICE_API）
    redis_client: Redis              # Redis 客户端（用于停止标记和任务归属）
    _queues: dict[str, Queue]        # task_id → Queue 的映射，按任务隔离队列
```

### 7.2 `listen()` — 监听循环

```python
def listen(self, task_id) -> Generator:
    listen_timeout = 600             # 总超时600秒
    start_time = time.time()
    last_ping_time = 0

    while True:
        item = self.queue(task_id).get(timeout=1)   # 阻塞等待1秒
        if item is None:                             # None 是终止信号
            break
        yield item                                   # yield 给主线程

        # 每10秒发一次 PING 保活（防止前端 SSE 连接超时断开）
        if elapsed_time // 10 > last_ping_time:
            self.publish(task_id, AgentThought(event=QueueEvent.PING))

        # 600秒超时保护
        if elapsed_time >= listen_timeout:
            self.publish(task_id, AgentThought(event=QueueEvent.TIMEOUT))

        # 检测 Redis 中的停止标记（用户点击"停止生成"）
        if self._is_stopped(task_id):
            self.publish(task_id, AgentThought(event=QueueEvent.STOP))
```

### 7.3 `publish()` — 发布事件

```python
def publish(self, task_id, agent_thought):
    self.queue(task_id).put(agent_thought)

    # 终止类事件自动停止监听
    if agent_thought.event in [STOP, ERROR, TIMEOUT, AGENT_END]:
        self.stop_listen(task_id)    # 往队列放入 None，触发 listen() 的 break
```

### 7.4 停止机制

前端用户点击"停止生成"时的完整链路：

```
前端按钮 → API 请求 → AgentQueueManager.set_stop_flag(task_id)
  → Redis: SETEX "generate_task_stopped:{task_id}" 600 1
  → listen() 循环中 _is_stopped() 检测到 → 发布 STOP 事件 → 队列终止
```

### 7.5 事件类型总览

```python
class QueueEvent(str, Enum):
    LONG_TERM_MEMORY_RECALL = "long_term_memory_recall"  # 长期记忆召回
    AGENT_THOUGHT           = "agent_thought"             # LLM 推理（决定调工具）
    AGENT_MESSAGE           = "agent_message"             # LLM 生成最终回答（逐chunk流式）
    AGENT_ACTION            = "agent_action"              # 执行工具
    DATASET_RETRIEVAL       = "dataset_retrieval"         # 执行知识库检索工具
    AGENT_END               = "agent_end"                 # 结束
    STOP                    = "stop"                      # 用户主动停止
    ERROR                   = "error"                     # 错误
    TIMEOUT                 = "timeout"                   # 超时
    PING                    = "ping"                      # 心跳保活
```

---

## 8. 完整对话执行流程示例

以用户提问 **"北京今天天气怎么样？"** 为例（Agent 绑定了高德天气工具）：

```
                            AgentState
                            messages: [HumanMessage("北京今天天气怎么样？")]
                            iteration_count: 0
                            history: [之前的对话...]
                            long_term_memory: "用户偏好简短回答"
                                │
  ┌─────────────────────────────▼──────────────────────────────────┐
  │ ① preset_operation                                             │
  │    检查"北京今天天气怎么样"是否包含敏感词 → 不包含                    │
  │    返回空消息列表                                                 │
  │    条件边：不是AIMessage → 走 long_term_memory_recall            │
  │                                                                │
  │    发布事件：无                                                   │
  └─────────────────────────────┬──────────────────────────────────┘
                                ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ ② long_term_memory_recall                                      │
  │    1. 发布 LONG_TERM_MEMORY_RECALL 事件（"用户偏好简短回答"）      │
  │    2. 组装 SystemMessage（模板 + preset_prompt + 长期记忆）        │
  │    3. 拼接 history（短期对话记录）                                 │
  │    4. 拼接 HumanMessage("北京今天天气怎么样？")                    │
  │    5. RemoveMessage 删除原始消息 → 替换为完整消息序列               │
  │                                                                │
  │    messages 变为:                                                │
  │    [SystemMessage("你是一个智能体...预设提示:...长期记忆:..."),      │
  │     HumanMessage("之前问题"), AIMessage("之前回答"),                │
  │     HumanMessage("北京今天天气怎么样？")]                          │
  │                                                                │
  │    发布事件：LONG_TERM_MEMORY_RECALL                             │
  └─────────────────────────────┬───────────────────────────────────┘
                                ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ ③ llm（第1次调用，iteration_count: 0→1）                         │
  │    1. llm.bind_tools([gaode_weather, ...])                      │
  │    2. llm.stream(messages)                                      │
  │    3. 第一个 chunk 有 tool_calls → type = "thought"              │
  │    4. gathered.tool_calls = [{"name":"gaode_weather",            │
  │                               "args":{"city":"北京"}}]           │
  │    5. 计算 Token: input=356, output=42                          │
  │    6. 计算费用: price = (356×0.0011 + 42×0.0044) × 0.001        │
  │    7. 条件边：有 tool_calls → 走 tools                           │
  │                                                                │
  │    发布事件：AGENT_THOUGHT（含 tool_calls JSON + Token + Price）  │
  └─────────────────────────────┬───────────────────────────────────┘
                                ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ ④ tools                                                        │
  │    1. 查找工具: tools_by_name["gaode_weather"]                   │
  │    2. 执行: gaode_weather.invoke({"city": "北京"})               │
  │    3. 结果: "晴，25°C，北风3级"                                  │
  │    4. 构建 ToolMessage(content="晴，25°C，北风3级")               │
  │    5. 工具名 != "dataset_retrieval" → AGENT_ACTION 事件          │
  │                                                                │
  │    发布事件：AGENT_ACTION（工具名 + 输入参数 + 执行结果 + 耗时）    │
  └─────────────────────────────┬───────────────────────────────────┘
                                │  固定边: tools → llm
                                ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ ⑤ llm（第2次调用，iteration_count: 1→2）                         │
  │    messages 现在多了 ToolMessage("晴，25°C，北风3级")              │
  │    1. llm.stream(messages) → 直接生成文本，无 tool_calls          │
  │    2. type = "message"                                          │
  │    3. 逐 chunk 发布 AGENT_MESSAGE（流式推送给前端）：               │
  │       "北京" → "今天" → "天气晴朗" → "，气温25°C" → ...           │
  │    4. 流式结束后计算 Token: input=412, output=38                  │
  │    5. 发布 AGENT_MESSAGE（含 Token+Price 汇总）                   │
  │    6. 发布 AGENT_END                                            │
  │    7. 条件边：无 tool_calls → END                                │
  │                                                                │
  │    发布事件：AGENT_MESSAGE ×N(逐chunk)                           │
  │             AGENT_MESSAGE(Token汇总)                            │
  │             AGENT_END                                           │
  └─────────────────────────────┬───────────────────────────────────┘
                                ▼
                              END
```

### 本次对话的事件时序

| 顺序 | 事件类型 | 来源节点 | 携带数据 | Token数据 |
|------|---------|---------|---------|-----------|
| 1 | `LONG_TERM_MEMORY_RECALL` | long_term_memory_recall | observation: "用户偏好简短回答" | 无 |
| 2 | `AGENT_THOUGHT` | llm (第1次) | thought: tool_calls JSON | input=356, output=42, price=0.0006 |
| 3 | `AGENT_ACTION` | tools | tool: "gaode_weather", observation: "晴,25°C" | 无（工具执行不消耗Token） |
| 4 | `AGENT_MESSAGE` ×N | llm (第2次) | thought: 每个chunk文本（流式） | 无（中间chunk不带Token） |
| 5 | `AGENT_MESSAGE` (最终) | llm (第2次) | Token+Price 汇总数据 | input=412, output=38, price=0.0006 |
| 6 | `AGENT_END` | llm (第2次) | 空（终止信号） | 无 |

**关键**：只有 `llm` 节点的事件（第2、5步）携带 Token 和费用数据。`tools` 节点只是执行外部工具，不调用 LLM，不产生 Token 消耗。

---

## 9. Token 计算与费用链路

### 9.1 定价来源

每个 LLM 模型的 YAML 配置文件中定义定价，例如 `providers/openai/gpt-4o-mini.yaml`：

```yaml
metadata:
  pricing:
    input: 0.0011       # 输入 token 单价
    output: 0.0044      # 输出 token 单价
    unit: 0.001         # 计费单位乘数
    currency: RMB       # 币种
```

通过 `BaseLanguageModel.get_pricing()` 获取：

```python
# model_entity.py:84-92
def get_pricing(self) -> tuple[float, float, float]:
    input_price = self.metadata.get("pricing", {}).get("input", 0.0)
    output_price = self.metadata.get("pricing", {}).get("output", 0.0)
    unit = self.metadata.get("pricing", {}).get("unit", 0.0)
    return input_price, output_price, unit
```

### 9.2 Token 计算时机

在 `_llm_node` 中，每次 LLM 流式调用结束后立即计算：

```python
# function_call_agent.py:215-224

# 计数
input_token_count = self.llm.get_num_tokens_from_messages(state["messages"])  # 输入Token
output_token_count = self.llm.get_num_tokens_from_messages([gathered])        # 输出Token

# 获取定价
input_price, output_price, unit = self.llm.get_pricing()

# 计算费用
total_token_count = input_token_count + output_token_count
total_price = (input_token_count * input_price + output_token_count * output_price) * unit
```

**费用公式**：

```
总费用 = (输入token数 × 输入单价 + 输出token数 × 输出单价) × 计费单位

示例（gpt-4o-mini, 输入1000 token, 输出500 token）：
= (1000 × 0.0011 + 500 × 0.0044) × 0.001
= (1.1 + 2.2) × 0.001
= 0.0033 RMB
```

### 9.3 数据附加到事件

Token 数据通过 `AgentThought` 实体携带：

```python
# queue_entity.py:30-59
class AgentThought(BaseModel):
    # 输入侧
    message_token_count: int = 0       # 输入 token 数
    message_unit_price: float = 0      # 输入单价(CNY)
    message_price_unit: float = 0      # 计费单位

    # 输出侧
    answer_token_count: int = 0        # 输出 token 数
    answer_unit_price: float = 0       # 输出单价(CNY)
    answer_price_unit: float = 0       # 计费单位

    # 汇总
    total_token_count: int = 0         # 总 token = 输入 + 输出
    total_price: float = 0             # 总费用(CNY)
    latency: float = 0                 # 步骤耗时(秒)
```

### 9.4 持久化到数据库

`conversation_service.py:131-243` 的 `save_agent_thoughts()` 在后台线程中：

```python
for agent_thought in agent_thoughts:
    # 每个推理步骤 → 写入 MessageAgentThought 表（明细）
    if agent_thought.event in [LONG_TERM_MEMORY_RECALL, AGENT_THOUGHT,
                                AGENT_MESSAGE, AGENT_ACTION, DATASET_RETRIEVAL]:
        position += 1
        latency += agent_thought.latency         # 累加总耗时

        self.create(MessageAgentThought,
            message_token_count=..., answer_token_count=...,
            total_token_count=..., total_price=..., latency=...,
        )

    # 收到 AGENT_MESSAGE 事件 → 更新 Message 表（汇总）
    if agent_thought.event == QueueEvent.AGENT_MESSAGE:
        self.update(message,
            total_token_count=..., total_price=...,
            latency=latency,    # 注意：这里是所有步骤的累加耗时
        )
```

**双表设计**：
- `Message` 表：消息级汇总（一次完整对话的总 Token、总费用、总耗时）
- `MessageAgentThought` 表：步骤级明细（每个推理步骤的 Token、费用、耗时）

### 9.5 统计服务聚合

`AnalysisService` 从 `Message` 表聚合查询：

```python
# analysis_service.py:119-123
token_output_rate = sum(msg.total_token_count) / sum(msg.latency)   # Token/秒
cost_consumption  = sum(msg.total_price)                             # 总费用(RMB)
```

---

## 10. FunctionCall vs ReACT 双模式对比

| 特性 | FunctionCallAgent | ReACTAgent |
|------|-------------------|------------|
| 适用模型 | 支持 `TOOL_CALL` 特性的模型（GPT-4o等） | **任何**文本生成模型 |
| 工具绑定方式 | `llm.bind_tools(tools)` 原生绑定 | Prompt 注入工具描述到 SystemMessage |
| 工具调用检测 | 检查 `chunk.tool_calls` 是否非空 | 解析输出前7字符是否为 `` ```json `` |
| 工具参数解析 | LLM 原生返回结构化 tool_calls | 从 `` ```json {...} ``` `` 中 JSON 解析 |
| 系统提示词 | `AGENT_SYSTEM_PROMPT_TEMPLATE` | `REACT_AGENT_SYSTEM_PROMPT_TEMPLATE`（额外包含 `<工具描述>` 段） |
| 重写的方法 | 无（基类） | `_long_term_memory_recall_node` + `_llm_node` |

**ReACTAgent 的关键差异**：

1. `_long_term_memory_recall_node`：如果 LLM 不支持 tool_call，就把工具描述通过 `render_text_description_and_args()` 渲染后注入到系统提示词中，让 LLM 通过生成 JSON 文本来"模拟"工具调用。

2. `_llm_node`：流式输出时通过检测**前7个字符**是否为 `` ```json `` 来判断是工具调用还是文本回答——这是一个巧妙的 trick，让不支持原生工具调用的模型也能使用 Agent 能力。

---

## 11. 关键设计要点

### 11.1 迭代次数保护

```python
# function_call_agent.py:134-154
if state["iteration_count"] > self.agent_config.max_iteration_count:  # 默认5
    # 强制返回"迭代次数已超过限制"并 END
```

防止 LLM 陷入"调工具→看结果→再调工具→..."的死循环。每经过一次 `llm` 节点，`iteration_count + 1`。

### 11.2 流式消息的叠加机制

`base_agent.py:56-104` 的 `invoke()` 方法中，`AGENT_MESSAGE` 事件采用**叠加**策略（因为是逐 chunk 流式发送的）：

```python
if agent_thought.event == QueueEvent.AGENT_MESSAGE:
    if event_id not in agent_thoughts:
        agent_thoughts[event_id] = agent_thought          # 首次：初始化
    else:
        agent_thoughts[event_id] = agent_thoughts[event_id].model_copy(update={
            "thought": existing.thought + agent_thought.thought,  # 文本叠加
            "answer": existing.answer + agent_thought.answer,
            "latency": agent_thought.latency,                     # 耗时取最新
        })
```

其他事件类型（AGENT_THOUGHT、AGENT_ACTION等）采用**覆盖**策略。

### 11.3 输入输出审核

- **输入审核**：`preset_operation` 节点在 LLM 调用**之前**检查敏感词 → 命中则直接返回预设回复
- **输出审核**：`llm` 节点在流式输出**过程中**逐 chunk 检查 → 命中的敏感词替换为 `"**"`

```python
# function_call_agent.py:192-196 输出审核
if review_config["enable"] and review_config["outputs_config"]["enable"]:
    for keyword in review_config["keywords"]:
        content = re.sub(re.escape(keyword), "**", content, flags=re.IGNORECASE)
```

### 11.4 Redis 在 Agent 中的三个用途

| 用途 | Key 格式 | TTL | 说明 |
|------|---------|-----|------|
| 任务归属 | `generate_task_belong:{task_id}` | 1800s | 记录任务属于哪个用户，防止越权停止 |
| 停止标记 | `generate_task_stopped:{task_id}` | 600s | 用户点击"停止生成"时设置 |
| 统计缓存 | `{YYYY_MM_DD}:{app_id}` | 86400s | 分析数据缓存，每天更新一次 |

---

## 12. 关键文件索引

| 文件 | 行号 | 内容 |
|------|------|------|
| `internal/core/agent/agents/base_agent.py` | 25-136 | BaseAgent 基类：stream/invoke、子线程启动 |
| `internal/core/agent/agents/function_call_agent.py` | 36-57 | 状态图构建（_build_agent） |
| 同上 | 59-87 | preset_operation 节点（输入审核） |
| 同上 | 89-130 | long_term_memory_recall 节点（消息组装） |
| 同上 | 132-276 | llm 节点（LLM推理 + Token计算） |
| 同上 | 278-324 | tools 节点（工具执行） |
| 同上 | 326-349 | 两个条件边方法 |
| `internal/core/agent/agents/react_agent.py` | 全文 | ReACT 模式（重写2个节点） |
| `internal/core/agent/agents/agent_queue_manager.py` | 全文 | 事件队列管理器 |
| `internal/core/agent/entities/agent_entity.py` | 19-96 | 系统提示词模板 |
| 同上 | 99-134 | AgentConfig、AgentState 定义 |
| `internal/core/agent/entities/queue_entity.py` | 16-27 | QueueEvent 事件类型枚举 |
| 同上 | 30-59 | AgentThought 实体（含Token字段） |
| 同上 | 62-83 | AgentResult 最终结果实体 |
| `internal/core/language_model/entities/model_entity.py` | 84-92 | get_pricing() 定价获取 |
| `internal/service/conversation_service.py` | 131-243 | save_agent_thoughts() 持久化 |
