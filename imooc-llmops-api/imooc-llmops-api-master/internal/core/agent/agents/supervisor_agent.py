#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/03/17 10:00
@Author  : ccckz@protonmail.com
@File    : supervisor_agent.py
"""
import json
import logging
import re
import time
import uuid
from typing import Literal, Any, Optional

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    AIMessage,
    RemoveMessage,
    messages_to_dict,
)
from langchain_core.pydantic_v1 import PrivateAttr
from langchain_core.tools import BaseTool, tool
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from internal.core.agent.entities.agent_entity import (
    SupervisorAgentState,
    SupervisorAgentConfig,
    SubAgentConfig,
    AgentConfig,
    AgentState,
    SUPERVISOR_SYSTEM_PROMPT_TEMPLATE,
    SUPERVISOR_SYNTHESIZER_PROMPT_TEMPLATE,
    AGENT_SYSTEM_PROMPT_TEMPLATE,
    DATASET_RETRIEVAL_TOOL_NAME,
    MAX_ITERATION_RESPONSE,
)
from internal.core.agent.entities.queue_entity import AgentThought, QueueEvent
from internal.core.language_model.entities.model_entity import ModelFeature
from internal.exception import FailException
from .base_agent import BaseAgent
from .agent_queue_manager import AgentQueueManager
from .function_call_agent import FunctionCallAgent
from .react_agent import ReACTAgent


class SupervisorAgent(BaseAgent):
    """基于Supervisor模式的多智能体协作Agent"""
    agent_config: SupervisorAgentConfig
    _language_model_service: Any = PrivateAttr(None)

    def __init__(
            self,
            llm,
            agent_config: SupervisorAgentConfig,
            language_model_service=None,
            *args,
            **kwargs,
    ):
        """构造函数，初始化Supervisor智能体"""
        super().__init__(*args, llm=llm, agent_config=agent_config, **kwargs)
        self._language_model_service = language_model_service

    def _build_agent(self) -> CompiledStateGraph:
        """构建Supervisor LangGraph图结构"""
        # 1.创建图，使用SupervisorAgentState
        graph = StateGraph(SupervisorAgentState)

        # 2.添加节点
        graph.add_node("preset_operation", self._preset_operation_node)
        graph.add_node("supervisor_router", self._supervisor_router_node)
        graph.add_node("sub_agent_node", self._sub_agent_node)
        graph.add_node("synthesizer_node", self._synthesizer_node)

        # 3.添加边
        graph.set_entry_point("preset_operation")
        graph.add_conditional_edges("preset_operation", self._preset_operation_condition)
        graph.add_conditional_edges("supervisor_router", self._router_condition)
        graph.add_edge("sub_agent_node", "synthesizer_node")
        graph.add_edge("synthesizer_node", END)

        # 4.编译并返回
        return graph.compile()

    def _preset_operation_node(self, state: SupervisorAgentState) -> dict:
        """预设操作节点，处理审核逻辑"""
        # 1.获取审核配置与用户输入query
        review_config = self.agent_config.review_config
        query = state["messages"][-1].content

        # 2.检测是否开启审核配置
        if review_config["enable"] and review_config["inputs_config"]["enable"]:
            contains_keyword = any(keyword in query for keyword in review_config["keywords"])
            if contains_keyword:
                preset_response = review_config["inputs_config"]["preset_response"]
                self.agent_queue_manager.publish(state["task_id"], AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_MESSAGE,
                    thought=preset_response,
                    message=messages_to_dict(state["messages"]),
                    answer=preset_response,
                    latency=0,
                ))
                self.agent_queue_manager.publish(state["task_id"], AgentThought(
                    id=uuid.uuid4(),
                    task_id=state["task_id"],
                    event=QueueEvent.AGENT_END,
                ))
                return {"messages": [AIMessage(preset_response)]}

        return {"messages": []}

    def _supervisor_router_node(self, state: SupervisorAgentState) -> dict:
        """Supervisor路由节点：LLM通过bind_tools选择子Agent"""
        start_at = time.perf_counter()
        thought_id = uuid.uuid4()

        # 1.构建子Agent工具列表（每个子Agent暴露为一个LangChain工具）
        sub_agent_tools = self._build_sub_agent_tools()

        # 2.构建系统消息
        long_term_memory = ""
        if self.agent_config.enable_long_term_memory:
            long_term_memory = state.get("long_term_memory", "")

        system_message = SystemMessage(SUPERVISOR_SYSTEM_PROMPT_TEMPLATE.format(
            preset_prompt=self.agent_config.preset_prompt,
            long_term_memory=long_term_memory,
        ))

        # 3.构建消息列表
        messages = [system_message]
        history = state.get("history", [])
        if isinstance(history, list) and len(history) > 0:
            messages.extend(history)

        human_message = state["messages"][-1]
        messages.append(HumanMessage(human_message.content))

        # 4.绑定子Agent工具并调用LLM
        llm = self.llm
        if sub_agent_tools and ModelFeature.TOOL_CALL in llm.features:
            llm = llm.bind_tools(sub_agent_tools)

        try:
            gathered = None
            is_first_chunk = True
            generation_type = ""
            for chunk in llm.stream(messages):
                if is_first_chunk:
                    gathered = chunk
                    is_first_chunk = False
                else:
                    gathered += chunk

                if not generation_type:
                    if chunk.tool_calls:
                        generation_type = "thought"
                    elif chunk.content:
                        generation_type = "message"

                # 如果是直接回答模式，流式输出
                if generation_type == "message":
                    review_config = self.agent_config.review_config
                    content = chunk.content
                    if review_config["enable"] and review_config["outputs_config"]["enable"]:
                        for keyword in review_config["keywords"]:
                            content = re.sub(re.escape(keyword), "**", content, flags=re.IGNORECASE)

                    self.agent_queue_manager.publish(state["task_id"], AgentThought(
                        id=thought_id,
                        task_id=state["task_id"],
                        event=QueueEvent.AGENT_MESSAGE,
                        thought=content,
                        message=messages_to_dict(messages),
                        answer=content,
                        latency=(time.perf_counter() - start_at),
                    ))
        except Exception as e:
            logging.exception(f"Supervisor路由节点LLM错误: {str(e)}")
            self.agent_queue_manager.publish_error(state["task_id"], f"Supervisor LLM错误: {str(e)}")
            raise e

        # 5.根据LLM输出判断是调度子Agent还是直接回答
        if generation_type == "thought" and gathered and gathered.tool_calls:
            # 选择了子Agent
            selected_tool_call = gathered.tool_calls[0]
            sub_agent_name = selected_tool_call["name"]

            # 发布 AGENT_DELEGATION 事件
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=uuid.uuid4(),
                task_id=state["task_id"],
                event=QueueEvent.AGENT_DELEGATION,
                thought=f"将任务分配给子Agent: {sub_agent_name}",
                observation=json.dumps(selected_tool_call),
                tool=sub_agent_name,
                tool_input=selected_tool_call.get("args", {}),
                sub_agent_name=sub_agent_name,
                latency=(time.perf_counter() - start_at),
            ))

            return {
                "messages": [gathered],
                "current_sub_agent": sub_agent_name,
                "iteration_count": state["iteration_count"] + 1,
            }
        else:
            # 直接回答，发布结束事件
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=thought_id,
                task_id=state["task_id"],
                event=QueueEvent.AGENT_MESSAGE,
                thought="",
                message=messages_to_dict(messages),
                answer="",
                latency=(time.perf_counter() - start_at),
            ))
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=uuid.uuid4(),
                task_id=state["task_id"],
                event=QueueEvent.AGENT_END,
            ))
            return {
                "messages": [gathered] if gathered else [],
                "current_sub_agent": "",
                "iteration_count": state["iteration_count"] + 1,
            }

    def _sub_agent_node(self, state: SupervisorAgentState) -> dict:
        """子Agent执行节点：根据选择的子Agent创建并执行"""
        sub_agent_name = state["current_sub_agent"]
        start_at = time.perf_counter()

        # 1.找到对应的SubAgentConfig
        sub_agent_config = None
        for sa in self.agent_config.sub_agents:
            if sa.name == sub_agent_name:
                sub_agent_config = sa
                break

        if not sub_agent_config:
            error_msg = f"未找到子Agent: {sub_agent_name}"
            self.agent_queue_manager.publish_error(state["task_id"], error_msg)
            return {"sub_agent_result": error_msg}

        # 2.加载子Agent的LLM
        sub_llm = None
        if self._language_model_service and sub_agent_config.model_config_data:
            try:
                sub_llm = self._language_model_service.load_language_model(sub_agent_config.model_config_data)
            except Exception as e:
                logging.warning(f"加载子Agent [{sub_agent_name}] 模型失败: {e}, 使用Supervisor的LLM")

        if not sub_llm:
            sub_llm = self.llm

        # 3.创建子Agent实例
        agent_class = FunctionCallAgent if ModelFeature.TOOL_CALL in sub_llm.features else ReACTAgent
        child_agent_config = AgentConfig(
            user_id=self.agent_config.user_id,
            invoke_from=self.agent_config.invoke_from,
            preset_prompt=sub_agent_config.preset_prompt,
            tools=sub_agent_config.tools,
            max_iteration_count=sub_agent_config.max_iteration_count,
            review_config=self.agent_config.review_config,
        )
        sub_agent = agent_class(
            llm=sub_llm,
            agent_config=child_agent_config,
        )

        # 4.获取用户原始提问（从tool_calls的参数中或从state消息中提取）
        query = ""
        last_ai_msg = state["messages"][-1]
        if hasattr(last_ai_msg, "tool_calls") and last_ai_msg.tool_calls:
            tool_args = last_ai_msg.tool_calls[0].get("args", {})
            query = tool_args.get("query", "")
        if not query:
            # 从历史消息中找到最后一个HumanMessage
            for msg in reversed(state["messages"]):
                if isinstance(msg, HumanMessage):
                    query = msg.content
                    break

        # 5.执行子Agent并收集结果（使用stream来获取流式事件）
        sub_agent_answer = ""
        for agent_thought in sub_agent.stream({
            "messages": [HumanMessage(query)],
            "history": state.get("history", []),
            "long_term_memory": state.get("long_term_memory", ""),
        }):
            # 转发子Agent的事件到Supervisor的队列，带上sub_agent_name标记
            if agent_thought.event != QueueEvent.PING and agent_thought.event != QueueEvent.AGENT_END:
                forwarded_thought = agent_thought.model_copy(update={
                    "sub_agent_name": sub_agent_name,
                })
                self.agent_queue_manager.publish(state["task_id"], forwarded_thought)

            # 收集answer
            if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                sub_agent_answer += agent_thought.answer

        # 6.发布 SUB_AGENT_END 事件
        self.agent_queue_manager.publish(state["task_id"], AgentThought(
            id=uuid.uuid4(),
            task_id=state["task_id"],
            event=QueueEvent.SUB_AGENT_END,
            thought=f"子Agent {sub_agent_name} 完成",
            observation=sub_agent_answer[:500],
            sub_agent_name=sub_agent_name,
            latency=(time.perf_counter() - start_at),
        ))

        return {"sub_agent_result": sub_agent_answer}

    def _synthesizer_node(self, state: SupervisorAgentState) -> dict:
        """综合节点：Supervisor LLM根据子Agent结果生成最终回答"""
        start_at = time.perf_counter()
        thought_id = uuid.uuid4()

        sub_agent_name = state["current_sub_agent"]
        sub_agent_result = state["sub_agent_result"]

        # 1.构建综合提示消息
        synthesizer_prompt = SUPERVISOR_SYNTHESIZER_PROMPT_TEMPLATE.format(
            sub_agent_name=sub_agent_name,
            sub_agent_result=sub_agent_result,
        )

        # 2.获取用户原始提问
        query = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                query = msg.content
                break

        messages = [
            SystemMessage(synthesizer_prompt),
            HumanMessage(query),
        ]

        # 3.流式调用Supervisor LLM生成最终回答
        try:
            gathered = None
            is_first_chunk = True
            for chunk in self.llm.stream(messages):
                if is_first_chunk:
                    gathered = chunk
                    is_first_chunk = False
                else:
                    gathered += chunk

                if chunk.content:
                    # 输出审核
                    review_config = self.agent_config.review_config
                    content = chunk.content
                    if review_config["enable"] and review_config["outputs_config"]["enable"]:
                        for keyword in review_config["keywords"]:
                            content = re.sub(re.escape(keyword), "**", content, flags=re.IGNORECASE)

                    self.agent_queue_manager.publish(state["task_id"], AgentThought(
                        id=thought_id,
                        task_id=state["task_id"],
                        event=QueueEvent.AGENT_MESSAGE,
                        thought=content,
                        message=messages_to_dict(messages),
                        answer=content,
                        latency=(time.perf_counter() - start_at),
                    ))

            # 4.发送最终统计和结束事件
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=thought_id,
                task_id=state["task_id"],
                event=QueueEvent.AGENT_MESSAGE,
                thought="",
                message=messages_to_dict(messages),
                answer="",
                latency=(time.perf_counter() - start_at),
            ))
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=uuid.uuid4(),
                task_id=state["task_id"],
                event=QueueEvent.AGENT_END,
            ))

        except Exception as e:
            logging.exception(f"Supervisor综合节点LLM错误: {str(e)}")
            self.agent_queue_manager.publish_error(state["task_id"], f"综合回复生成错误: {str(e)}")
            raise e

        return {"messages": [gathered] if gathered else []}

    def _build_sub_agent_tools(self) -> list[BaseTool]:
        """将子Agent暴露为LangChain工具"""
        sub_agent_tools = []
        for sa_config in self.agent_config.sub_agents:
            sa_tool = self._create_sub_agent_tool(sa_config.name, sa_config.description)
            sub_agent_tools.append(sa_tool)
        return sub_agent_tools

    @staticmethod
    def _create_sub_agent_tool(name: str, description: str) -> BaseTool:
        """为单个子Agent创建LangChain工具"""
        @tool(name, return_direct=False)
        def delegate_to_sub_agent(query: str) -> str:
            """委派任务给子Agent"""
            return query

        delegate_to_sub_agent.description = description
        return delegate_to_sub_agent

    @classmethod
    def _preset_operation_condition(cls, state: SupervisorAgentState) -> Literal["supervisor_router", "__end__"]:
        """预设操作条件边"""
        message = state["messages"][-1]
        if message.type == "ai":
            return END
        return "supervisor_router"

    @classmethod
    def _router_condition(cls, state: SupervisorAgentState) -> Literal["sub_agent_node", "__end__"]:
        """路由条件：判断是执行子Agent还是直接结束"""
        if state.get("current_sub_agent"):
            return "sub_agent_node"
        return END
