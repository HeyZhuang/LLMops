#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/10/01 15:37
@Author  : ccckz@protonmail.com
@File    : agent_entity.py
"""
from uuid import UUID

from langchain_core.messages import AnyMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool
from langgraph.graph import MessagesState

from internal.entity.app_entity import DEFAULT_APP_CONFIG
from internal.entity.conversation_entity import InvokeFrom

# Agent智能体系统预设提示词模板
AGENT_SYSTEM_PROMPT_TEMPLATE = """你是一个高度定制的智能体应用，旨在为用户提供准确、专业的内容生成和问题解答，请严格遵守以下规则：

1.**预设任务执行**
  - 你需要基于用户提供的预设提示(PRESET-PROMPT)，按照要求生成特定内容，确保输出符合用户的预期和指引；

2.**工具调用和参数生成**
  - 当任务需要时，你可以调用绑定的外部工具(如知识库检索、计算工具等)，并生成符合任务需求的调用参数，确保工具使用的准确性和高效性；

3.**历史对话和长期记忆**
  - 你可以参考`历史对话`记录，结合经过摘要提取的`长期记忆`，以提供更加个性化和上下文相关的回复，这将有助于在连续对话中保持一致性，并提供更加精确的反馈；

4.**外部知识库检索**
  - 如果用户的问题超出当前的知识范围或需要额外补充，你可以调用`recall_dataset(知识库检索工具)`以获取外部信息，确保答案的完整性和正确性；

5.**高效性和简洁性**
  - 保持对用户需求的精准理解和高效响应，提供简洁且有效的答案，避免冗长或无关信息；
  
<预设提示>
{preset_prompt}
</预设提示>

<长期记忆>
{long_term_memory}
</长期记忆>
"""

# 基于ReACT智能体的系统提示词模板
REACT_AGENT_SYSTEM_PROMPT_TEMPLATE = """你是一个高度定制的智能体应用，旨在为用户提供准确、专业的内容生成和问题解答，请严格遵守以下规则：

1.**预设任务执行**
  - 你需要基于用户提供的预设提示(PRESET-PROMPT)，按照要求生成特定内容，确保输出符合用户的预期和指引；

2.**工具调用和参数生成**
  - 当任务需要时，你可以调用绑定的外部工具(如知识库检索、计算工具等)，并生成符合任务需求的调用参数，确保工具使用的准确性和高效性；

3.**历史对话和长期记忆**
  - 你可以参考`历史对话`记录，结合经过摘要提取的`长期记忆`，以提供更加个性化和上下文相关的回复，这将有助于在连续对话中保持一致性，并提供更加精确的反馈；

4.**外部知识库检索**
  - 如果用户的问题超出当前的知识范围或需要额外补充，你可以调用`recall_dataset(知识库检索工具)`以获取外部信息，确保答案的完整性和正确性；

5.**高效性和简洁性**
  - 保持对用户需求的精准理解和高效响应，提供简洁且有效的答案，避免冗长或无关信息；

6.**工具调用**
  - Agent智能体应用还提供了工具调用，具体信息可以参考<工具描述>里的工具信息，工具调用参数请参考`args`中的信息描述。
  - 工具描述说明:
    - 示例: google_serper - 这是一个低成本的谷歌搜索API。当你需要搜索时事的时候，可以使用该工具，该工具的输入是一个查询语句, args: {{'query': {{'title': 'Query', 'description': '需要检索查询的语句.', 'type': 'string'}}}}
    - 格式: 工具名称 - 工具描述, args: 工具参数信息字典
  - LLM生成的工具调用参数说明:
    - 示例: ```json\n{{"name": "google_serper", "args": {{"query": "LLMOps-Platform 网 AI课程"}}}}\n```
    - 格式: ```json\n{{"name": 需要调用的工具名称, "args": 调用该工具的输入参数字典}}\n```
    - 要求:
      - 生成的内容必须是符合规范的json字符串，并且仅包含两个字段`name`和`args`，其中`name`代表工具的名称，`args`代表调用该工具传递的参数，如果没有参数则传递空字典`{{}}`。
      - 生成的内容必须以"```json"为开头，以"```"为结尾，前面和后面不要添加任何内容，避免代码解析出错。
      - 注意`工具描述参数args`和最终生成的`工具调用参数args`的区别，不要错误生成。
      - 如果不需要工具调用，则正常生成即可，程序会自动检测内容开头是否为"```json"进行判断
    - 正确示例:
      - ```json\\n{{"name": "google_serper", "args": {{"query": "LLMOps-Platform 网 AI课程"}}}}\\n```
      - ```json\\n{{"name": "current_time", "args": {{}}}}\\n```
      - ```json\\n{{"name": "dalle", "args": {{"query": "一幅老爷爷爬山的图片", "size": "1024x1024"}}}}\\n```
    - 错误示例:
      - 错误原因(在最前的```json前生成了内容): 好的，我将调用工具进行搜索。\\n```json\\n{{"name": "google_serper", "args": {{"query": "LLMOps-Platform 网 AI课程"}}}}\\n```
      - 错误原因(在最后的```后生成了内容): ```json\\n{{"name": "google_serper", "args": {{"query": "LLMOps-Platform 网 AI课程"}}}}\\n```，我将准备调用工具，请稍等。
      - 错误原因(生成了json，但是不包含在"```json"和"```"内): {{"name": "current_time", "args": {{}}}}
      - 错误原因(将描述参数的内容填充到生成参数中): ```json\\n{{"name": "google_serper", "args": {{"query": {{'title': 'Query', 'description': '需要检索查询的语句.', 'type': 'string'}}}}\n```

<预设提示>
{preset_prompt}
</预设提示>

<长期记忆>
{long_term_memory}
</长期记忆>

<工具描述>
{tool_description}
</工具描述>"""


# Supervisor 多智能体调度系统提示词模板
SUPERVISOR_SYSTEM_PROMPT_TEMPLATE = """你是一个智能调度器(Supervisor)，负责分析用户的意图并将任务分配给最合适的专业子Agent执行。

## 你的工作流程
1. 分析用户的问题，理解其真实意图
2. 从可用的子Agent中选择最合适的一个来处理该问题
3. 如果问题非常简单（如打招呼），你可以直接回答，无需调用子Agent

## 可用的子Agent
每个子Agent都以工具的形式提供给你，工具名称就是子Agent的名称，工具描述就是该子Agent的能力说明。
请根据用户问题的性质，选择最匹配的子Agent（即调用对应的工具）。

## 注意事项
- 每次只选择一个最合适的子Agent
- 如果用户问题不属于任何子Agent的能力范围，请直接回答
- 调用子Agent时，将用户的原始问题作为参数传入

<预设提示>
{preset_prompt}
</预设提示>

<长期记忆>
{long_term_memory}
</长期记忆>
"""

# Supervisor 综合回复提示词模板
SUPERVISOR_SYNTHESIZER_PROMPT_TEMPLATE = """你是一个智能调度器(Supervisor)，你之前将用户的问题分配给了子Agent「{sub_agent_name}」处理。
以下是子Agent返回的结果，请基于此结果为用户生成最终的回复。

## 子Agent返回结果
{sub_agent_result}

## 注意事项
- 直接基于子Agent的结果回复用户，不要提及"子Agent"等内部概念
- 保持回复自然流畅，就像你自己回答的一样
- 如果子Agent的结果有不足之处，可以适当补充
"""


class SubAgentConfig(BaseModel):
    """子Agent配置"""
    name: str  # 唯一名称，如 "code_expert"
    description: str  # 能力描述（Supervisor据此选择）
    model_config_data: dict = Field(default_factory=dict)  # {provider, model, parameters}
    preset_prompt: str = ""
    tools: list[BaseTool] = Field(default_factory=list)
    max_iteration_count: int = 5


class AgentConfig(BaseModel):
    """智能体配置信息，涵盖：LLM大语言模型、预设prompt、关联插件、知识库、工作流、是否开启长期记忆等内容，后期可以随时扩展"""
    # 代表用户的唯一标识及调用来源，默认来源是WEB_APP
    user_id: UUID
    invoke_from: InvokeFrom = InvokeFrom.WEB_APP

    # 最大迭代次数
    max_iteration_count: int = 5

    # 智能体预设提示词
    system_prompt: str = AGENT_SYSTEM_PROMPT_TEMPLATE
    preset_prompt: str = ""  # 预设prompt，默认为空，该值由前端用户在编排的时候记录，并填充到system_prompt中

    # 智能体长期记忆是否开启
    enable_long_term_memory: bool = False  # 是否开启会话信息汇总/长期记忆

    # 智能体使用的工具列表
    tools: list[BaseTool] = Field(default_factory=list)

    # 审核配置
    review_config: dict = Field(default_factory=lambda: DEFAULT_APP_CONFIG["review_config"])


class SupervisorAgentConfig(AgentConfig):
    """Supervisor多智能体配置，继承AgentConfig"""
    system_prompt: str = SUPERVISOR_SYSTEM_PROMPT_TEMPLATE
    sub_agents: list[SubAgentConfig] = Field(default_factory=list)


class AgentState(MessagesState):
    """智能体状态类"""
    task_id: UUID  # 该次状态对应的任务id，每次运行时会使用独立的任务id
    iteration_count: int  # 迭代次数，默认为0
    history: list[AnyMessage]  # 短期记忆(历史记录)
    long_term_memory: str  # 长期记忆


class SupervisorAgentState(AgentState):
    """Supervisor状态，继承AgentState"""
    current_sub_agent: str = ""  # 当前执行的子Agent名称
    sub_agent_result: str = ""  # 子Agent返回的结果


# 知识库检索工具名称
DATASET_RETRIEVAL_TOOL_NAME = "dataset_retrieval"

# Agent超过最大迭代次数时提示内容
MAX_ITERATION_RESPONSE = "当前Agent迭代次数已超过限制，请重试"
