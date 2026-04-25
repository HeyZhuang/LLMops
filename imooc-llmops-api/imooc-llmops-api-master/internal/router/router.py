#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/3/29 15:01
@Author  : ccckz@protonmail.com
@File    : router.py
"""
from dataclasses import dataclass

from flask import Flask, Blueprint
from injector import inject

from internal.handler import (
    AppHandler,
    BuiltinToolHandler,
    ApiToolHandler,
    UploadFileHandler,
    DatasetHandler,
    DocumentHandler,
    SegmentHandler,
    OAuthHandler,
    AccountHandler,
    AuthHandler,
    AIHandler,
    ApiKeyHandler,
    OpenAPIHandler,
    BuiltinAppHandler,
    BuiltinWorkflowHandler,
    WorkflowHandler,
    LanguageModelHandler,
    AssistantAgentHandler,
    AnalysisHandler,
    WebAppHandler,
    ConversationHandler,
    FeedbackHandler,
    AppExportHandler,
    PromptTemplateHandler,
    SkillHandler,
    ConsultCenterHandler,
    ImagingHandler,
)


@inject
@dataclass
class Router:
    """路由"""
    app_handler: AppHandler
    builtin_tool_handler: BuiltinToolHandler
    api_tool_handler: ApiToolHandler
    upload_file_handler: UploadFileHandler
    dataset_handler: DatasetHandler
    document_handler: DocumentHandler
    segment_handler: SegmentHandler
    oauth_handler: OAuthHandler
    account_handler: AccountHandler
    auth_handler: AuthHandler
    ai_handler: AIHandler
    api_key_handler: ApiKeyHandler
    openapi_handler: OpenAPIHandler
    builtin_app_handler: BuiltinAppHandler
    builtin_workflow_handler: BuiltinWorkflowHandler
    workflow_handler: WorkflowHandler
    language_model_handler: LanguageModelHandler
    assistant_agent_handler: AssistantAgentHandler
    analysis_handler: AnalysisHandler
    web_app_handler: WebAppHandler
    conversation_handler: ConversationHandler
    feedback_handler: FeedbackHandler
    app_export_handler: AppExportHandler
    prompt_template_handler: PromptTemplateHandler
    skill_handler: SkillHandler
    consult_center_handler: ConsultCenterHandler
    imaging_handler: ImagingHandler

    def register_router(self, app: Flask):
        """注册路由"""
        # 1.创建一个蓝图
        bp = Blueprint("llmops", __name__, url_prefix="")
        openapi_bp = Blueprint("openapi", __name__, url_prefix="")

        # 2.将url与对应的控制器方法做绑定
        bp.add_url_rule("/ping", view_func=self.app_handler.ping)
        bp.add_url_rule("/consult-center/overview", view_func=self.consult_center_handler.get_overview)
        bp.add_url_rule(
            "/imaging/overview",
            endpoint="imaging_get_overview",
            view_func=self.imaging_handler.get_overview,
        )
        bp.add_url_rule(
            "/imaging/workflow-templates",
            endpoint="imaging_get_workflow_templates",
            view_func=self.imaging_handler.get_workflow_templates,
        )
        bp.add_url_rule(
            "/imaging/mvp-tasks",
            endpoint="imaging_get_mvp_tasks",
            view_func=self.imaging_handler.get_mvp_tasks,
        )
        bp.add_url_rule(
            "/imaging/studies",
            endpoint="imaging_get_studies",
            view_func=self.imaging_handler.get_studies,
        )
        bp.add_url_rule(
            "/imaging/upload-dicom",
            methods=["POST"],
            endpoint="imaging_upload_dicom",
            view_func=self.imaging_handler.upload_dicom,
        )
        bp.add_url_rule(
            "/imaging/studies/<string:study_id>",
            endpoint="imaging_get_study_detail",
            view_func=self.imaging_handler.get_study_detail,
        )
        bp.add_url_rule(
            "/imaging/studies/<string:study_id>/series",
            endpoint="imaging_get_study_series",
            view_func=self.imaging_handler.get_study_series,
        )
        bp.add_url_rule(
            "/imaging/studies/<string:study_id>/series/<string:series_id>/instances",
            endpoint="imaging_get_series_instances",
            view_func=self.imaging_handler.get_series_instances,
        )
        bp.add_url_rule(
            "/imaging/studies/<string:study_id>/series/<string:series_id>/instances/<string:instance_id>/preview",
            endpoint="imaging_get_instance_preview",
            view_func=self.imaging_handler.get_instance_preview,
        )
        bp.add_url_rule(
            "/imaging/studies/<string:study_id>/analysis-tasks",
            methods=["POST"],
            endpoint="imaging_create_analysis_task",
            view_func=self.imaging_handler.create_analysis_task,
        )
        bp.add_url_rule(
            "/imaging/studies/<string:study_id>/analysis-result",
            endpoint="imaging_get_analysis_result",
            view_func=self.imaging_handler.get_analysis_result,
        )
        bp.add_url_rule(
            "/imaging/studies/<string:study_id>/structured-findings",
            endpoint="imaging_get_structured_findings",
            view_func=self.imaging_handler.get_structured_findings,
        )
        bp.add_url_rule(
            "/imaging/studies/<string:study_id>/audit-logs",
            endpoint="imaging_get_audit_logs",
            view_func=self.imaging_handler.get_audit_logs,
        )
        bp.add_url_rule(
            "/imaging/studies/<string:study_id>/review-logs",
            endpoint="imaging_get_review_logs",
            view_func=self.imaging_handler.get_review_logs,
        )
        bp.add_url_rule(
            "/imaging/studies/<string:study_id>/feedback-stats",
            endpoint="imaging_get_feedback_stats",
            view_func=self.imaging_handler.get_feedback_stats,
        )
        bp.add_url_rule(
            "/imaging/studies/<string:study_id>/report-draft",
            methods=["POST"],
            endpoint="imaging_save_report_draft",
            view_func=self.imaging_handler.save_report_draft,
        )
        bp.add_url_rule(
            "/imaging/studies/<string:study_id>/review",
            methods=["POST"],
            endpoint="imaging_submit_review",
            view_func=self.imaging_handler.submit_review,
        )
        bp.add_url_rule("/apps", view_func=self.app_handler.get_apps_with_page)
        bp.add_url_rule("/apps", methods=["POST"], view_func=self.app_handler.create_app)
        bp.add_url_rule("/apps/<uuid:app_id>", view_func=self.app_handler.get_app)
        bp.add_url_rule("/apps/<uuid:app_id>", methods=["POST"], view_func=self.app_handler.update_app)
        bp.add_url_rule("/apps/<uuid:app_id>/delete", methods=["POST"], view_func=self.app_handler.delete_app)
        bp.add_url_rule("/apps/<uuid:app_id>/copy", methods=["POST"], view_func=self.app_handler.copy_app)
        bp.add_url_rule("/apps/<uuid:app_id>/draft-app-config", view_func=self.app_handler.get_draft_app_config)
        bp.add_url_rule(
            "/apps/<uuid:app_id>/draft-app-config",
            methods=["POST"],
            view_func=self.app_handler.update_draft_app_config,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/publish",
            methods=["POST"],
            view_func=self.app_handler.publish,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/cancel-publish",
            methods=["POST"],
            view_func=self.app_handler.cancel_publish,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/publish-histories",
            view_func=self.app_handler.get_publish_histories_with_page,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/fallback-history",
            methods=["POST"],
            view_func=self.app_handler.fallback_history_to_draft,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/summary",
            view_func=self.app_handler.get_debug_conversation_summary,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/summary",
            methods=["POST"],
            view_func=self.app_handler.update_debug_conversation_summary,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/conversations/delete-debug-conversation",
            methods=["POST"],
            view_func=self.app_handler.delete_debug_conversation,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/conversations",
            methods=["POST"],
            view_func=self.app_handler.debug_chat,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/conversations/tasks/<uuid:task_id>/stop",
            methods=["POST"],
            view_func=self.app_handler.stop_debug_chat,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/conversations/messages",
            view_func=self.app_handler.get_debug_conversation_messages_with_page,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/published-config",
            view_func=self.app_handler.get_published_config,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/published-config/regenerate-web-app-token",
            methods=["POST"],
            view_func=self.app_handler.regenerate_web_app_token,
        )

        # 3.内置插件广场模块
        bp.add_url_rule("/builtin-tools", view_func=self.builtin_tool_handler.get_builtin_tools)
        bp.add_url_rule(
            "/builtin-tools/<string:provider_name>/tools/<string:tool_name>",
            view_func=self.builtin_tool_handler.get_provider_tool,
        )
        bp.add_url_rule(
            "/builtin-tools/<string:provider_name>/icon",
            view_func=self.builtin_tool_handler.get_provider_icon,
        )
        bp.add_url_rule(
            "/builtin-tools/categories",
            view_func=self.builtin_tool_handler.get_categories,
        )

        # 4.自定义API插件模块
        bp.add_url_rule(
            "/api-tools",
            view_func=self.api_tool_handler.get_api_tool_providers_with_page,
        )
        bp.add_url_rule(
            "/api-tools/validate-openapi-schema",
            methods=["POST"],
            view_func=self.api_tool_handler.validate_openapi_schema,
        )
        bp.add_url_rule(
            "/api-tools",
            methods=["POST"],
            view_func=self.api_tool_handler.create_api_tool_provider,
        )
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>",
            view_func=self.api_tool_handler.get_api_tool_provider,
        )
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>",
            methods=["POST"],
            view_func=self.api_tool_handler.update_api_tool_provider,
        )
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>/tools/<string:tool_name>",
            view_func=self.api_tool_handler.get_api_tool,
        )
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>/delete",
            methods=["POST"],
            view_func=self.api_tool_handler.delete_api_tool_provider,
        )

        # 4.上传文件模块
        bp.add_url_rule("/upload-files/file", methods=["POST"], view_func=self.upload_file_handler.upload_file)
        bp.add_url_rule("/upload-files/image", methods=["POST"], view_func=self.upload_file_handler.upload_image)

        # 5.知识库模块
        bp.add_url_rule("/datasets", view_func=self.dataset_handler.get_datasets_with_page)
        bp.add_url_rule("/datasets", methods=["POST"], view_func=self.dataset_handler.create_dataset)
        bp.add_url_rule("/datasets/<uuid:dataset_id>", view_func=self.dataset_handler.get_dataset)
        bp.add_url_rule("/datasets/<uuid:dataset_id>", methods=["POST"], view_func=self.dataset_handler.update_dataset)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/queries", view_func=self.dataset_handler.get_dataset_queries)
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/delete",
            methods=["POST"],
            view_func=self.dataset_handler.delete_dataset,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents",
            view_func=self.document_handler.get_documents_with_page,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents",
            methods=["POST"],
            view_func=self.document_handler.create_documents,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>",
            view_func=self.document_handler.get_document,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/name",
            methods=["POST"],
            view_func=self.document_handler.update_document_name,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/enabled",
            methods=["POST"],
            view_func=self.document_handler.update_document_enabled,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/delete",
            methods=["POST"],
            view_func=self.document_handler.delete_document,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/batch/<string:batch>",
            view_func=self.document_handler.get_documents_status,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments",
            view_func=self.segment_handler.get_segments_with_page,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments",
            methods=["POST"],
            view_func=self.segment_handler.create_segment,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>",
            view_func=self.segment_handler.get_segment,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>",
            methods=["POST"],
            view_func=self.segment_handler.update_segment,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>/enabled",
            methods=["POST"],
            view_func=self.segment_handler.update_segment_enabled,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>/delete",
            methods=["POST"],
            view_func=self.segment_handler.delete_segment,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/hit",
            methods=["POST"],
            view_func=self.dataset_handler.hit,
        )

        # 6.授权认证模块
        bp.add_url_rule(
            "/oauth/<string:provider_name>",
            view_func=self.oauth_handler.provider,
        )
        bp.add_url_rule(
            "/oauth/authorize/<string:provider_name>",
            methods=["POST"],
            view_func=self.oauth_handler.authorize,
        )
        bp.add_url_rule(
            "/auth/password-login",
            methods=["POST"],
            view_func=self.auth_handler.password_login,
        )
        bp.add_url_rule(
            "/auth/logout",
            methods=["POST"],
            view_func=self.auth_handler.logout,
        )

        # 7.账号设置模块
        bp.add_url_rule("/account", view_func=self.account_handler.get_current_user)
        bp.add_url_rule("/account/password", methods=["POST"], view_func=self.account_handler.update_password)
        bp.add_url_rule("/account/name", methods=["POST"], view_func=self.account_handler.update_name)
        bp.add_url_rule("/account/avatar", methods=["POST"], view_func=self.account_handler.update_avatar)

        # 8.AI辅助模块
        bp.add_url_rule("/ai/optimize-prompt", methods=["POST"], view_func=self.ai_handler.optimize_prompt)
        bp.add_url_rule(
            "/ai/suggested-questions",
            methods=["POST"],
            view_func=self.ai_handler.generate_suggested_questions,
        )

        # 9.API秘钥模块
        bp.add_url_rule("/openapi/api-keys", view_func=self.api_key_handler.get_api_keys_with_page)
        bp.add_url_rule(
            "/openapi/api-keys",
            methods=["POST"],
            view_func=self.api_key_handler.create_api_key,
        )
        bp.add_url_rule(
            "/openapi/api-keys/<uuid:api_key_id>",
            methods=["POST"],
            view_func=self.api_key_handler.update_api_key,
        )
        bp.add_url_rule(
            "/openapi/api-keys/<uuid:api_key_id>/is-active",
            methods=["POST"],
            view_func=self.api_key_handler.update_api_key_is_active,
        )
        bp.add_url_rule(
            "/openapi/api-keys/<uuid:api_key_id>/delete",
            methods=["POST"],
            view_func=self.api_key_handler.delete_api_key,
        )
        openapi_bp.add_url_rule(
            "/openapi/chat",
            methods=["POST"],
            view_func=self.openapi_handler.chat,
        )

        # 10.内置应用模块
        bp.add_url_rule("/builtin-apps/categories", view_func=self.builtin_app_handler.get_builtin_app_categories)
        bp.add_url_rule("/builtin-apps", view_func=self.builtin_app_handler.get_builtin_apps)
        bp.add_url_rule(
            "/builtin-apps/add-builtin-app-to-space",
            methods=["POST"],
            view_func=self.builtin_app_handler.add_builtin_app_to_space,
        )

        # 11.工作流模块
        bp.add_url_rule("/workflows", view_func=self.workflow_handler.get_workflows_with_page)

        # 11.5 内置工作流模板模块
        bp.add_url_rule("/builtin-workflows/categories", view_func=self.builtin_workflow_handler.get_builtin_workflow_categories)
        bp.add_url_rule("/builtin-workflows", view_func=self.builtin_workflow_handler.get_builtin_workflows)
        bp.add_url_rule(
            "/builtin-workflows/add-builtin-workflow-to-space",
            methods=["POST"],
            view_func=self.builtin_workflow_handler.add_builtin_workflow_to_space,
        )

        bp.add_url_rule("/workflows", methods=["POST"], view_func=self.workflow_handler.create_workflow)
        bp.add_url_rule("/workflows/<uuid:workflow_id>", view_func=self.workflow_handler.get_workflow)
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>",
            methods=["POST"],
            view_func=self.workflow_handler.update_workflow,
        )
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/delete",
            methods=["POST"],
            view_func=self.workflow_handler.delete_workflow,
        )
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/draft-graph",
            methods=["POST"],
            view_func=self.workflow_handler.update_draft_graph,
        )
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/draft-graph",
            view_func=self.workflow_handler.get_draft_graph,
        )
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/debug",
            methods=["POST"],
            view_func=self.workflow_handler.debug_workflow,
        )
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/publish",
            methods=["POST"],
            view_func=self.workflow_handler.publish_workflow,
        )
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/cancel-publish",
            methods=["POST"],
            view_func=self.workflow_handler.cancel_publish_workflow,
        )

        # 12.语言模型模块
        bp.add_url_rule("/language-models", view_func=self.language_model_handler.get_language_models)
        bp.add_url_rule(
            "/language-models/<string:provider_name>/icon",
            view_func=self.language_model_handler.get_language_model_icon,
        )
        bp.add_url_rule(
            "/language-models/<string:provider_name>/<string:model_name>",
            view_func=self.language_model_handler.get_language_model,
        )

        # 13.辅助Agent模块
        bp.add_url_rule(
            "/assistant-agent/chat",
            methods=["POST"],
            view_func=self.assistant_agent_handler.assistant_agent_chat,
        )
        bp.add_url_rule(
            "/assistant-agent/chat/<uuid:task_id>/stop",
            methods=["POST"],
            view_func=self.assistant_agent_handler.stop_assistant_agent_chat,
        )
        bp.add_url_rule(
            "/assistant-agent/messages",
            view_func=self.assistant_agent_handler.get_assistant_agent_messages_with_page,
        )
        bp.add_url_rule(
            "/assistant-agent/delete-conversation",
            methods=["POST"],
            view_func=self.assistant_agent_handler.delete_assistant_agent_conversation,
        )

        # 14.应用统计模块
        bp.add_url_rule(
            "/analysis/<uuid:app_id>",
            view_func=self.analysis_handler.get_app_analysis,
        )
        bp.add_url_rule(
            "/analysis/<uuid:app_id>/token-cost",
            view_func=self.analysis_handler.get_token_cost_analysis,
        )

        # 15.WebApp模块
        bp.add_url_rule("/web-apps/<string:token>", view_func=self.web_app_handler.get_web_app)
        bp.add_url_rule(
            "/web-apps/<string:token>/chat",
            methods=["POST"],
            view_func=self.web_app_handler.web_app_chat,
        )
        bp.add_url_rule(
            "/web-apps/<string:token>/chat/<uuid:task_id>/stop",
            methods=["POST"],
            view_func=self.web_app_handler.stop_web_app_chat,
        )
        bp.add_url_rule("/web-apps/<string:token>/conversations", view_func=self.web_app_handler.get_conversations)

        # 16.会话模块
        bp.add_url_rule(
            "/conversations/<uuid:conversation_id>/messages",
            view_func=self.conversation_handler.get_conversation_messages_with_page,
        )
        bp.add_url_rule(
            "/conversations/<uuid:conversation_id>/delete",
            methods=["POST"],
            view_func=self.conversation_handler.delete_conversation,
        )
        bp.add_url_rule(
            "/conversations/<uuid:conversation_id>/messages/<uuid:message_id>/delete",
            methods=["POST"],
            view_func=self.conversation_handler.delete_message,
        )
        bp.add_url_rule(
            "/conversations/<uuid:conversation_id>/name",
            view_func=self.conversation_handler.get_conversation_name,
        )
        bp.add_url_rule(
            "/conversations/<uuid:conversation_id>/name",
            methods=["POST"],
            view_func=self.conversation_handler.update_conversation_name,
        )
        bp.add_url_rule(
            "/conversations/<uuid:conversation_id>/is-pinned",
            methods=["POST"],
            view_func=self.conversation_handler.update_conversation_is_pinned,
        )

        # 18.消息反馈模块
        bp.add_url_rule(
            "/messages/<uuid:message_id>/feedback",
            methods=["POST"],
            view_func=self.feedback_handler.create_feedback,
        )
        bp.add_url_rule(
            "/messages/<uuid:message_id>/feedback",
            view_func=self.feedback_handler.get_feedback,
        )
        bp.add_url_rule(
            "/apps/<uuid:app_id>/feedback-stats",
            view_func=self.feedback_handler.get_feedback_stats,
        )

        # 19.应用导入导出模块
        bp.add_url_rule(
            "/apps/<uuid:app_id>/export",
            view_func=self.app_export_handler.export_app,
        )
        bp.add_url_rule(
            "/apps/import",
            methods=["POST"],
            view_func=self.app_export_handler.import_app,
        )

        # 20.Prompt模板库模块
        bp.add_url_rule(
            "/prompt-templates",
            view_func=self.prompt_template_handler.get_prompt_templates_with_page,
        )
        bp.add_url_rule(
            "/prompt-templates",
            methods=["POST"],
            view_func=self.prompt_template_handler.create_prompt_template,
        )
        bp.add_url_rule(
            "/prompt-templates/<uuid:template_id>",
            view_func=self.prompt_template_handler.get_prompt_template,
        )
        bp.add_url_rule(
            "/prompt-templates/<uuid:template_id>",
            methods=["POST"],
            view_func=self.prompt_template_handler.update_prompt_template,
        )
        bp.add_url_rule(
            "/prompt-templates/<uuid:template_id>/delete",
            methods=["POST"],
            view_func=self.prompt_template_handler.delete_prompt_template,
        )

        # 21.在应用上注册蓝图
        # 20.5.技能库模块
        bp.add_url_rule("/skills", view_func=self.skill_handler.get_skills_with_page)
        bp.add_url_rule("/skills", methods=["POST"], view_func=self.skill_handler.create_skill)
        bp.add_url_rule("/skills/<uuid:skill_id>", view_func=self.skill_handler.get_skill)
        bp.add_url_rule(
            "/skills/<uuid:skill_id>",
            methods=["POST"],
            view_func=self.skill_handler.update_skill,
        )
        bp.add_url_rule(
            "/skills/<uuid:skill_id>/delete",
            methods=["POST"],
            view_func=self.skill_handler.delete_skill,
        )
        app.register_blueprint(bp)
        app.register_blueprint(openapi_bp)
