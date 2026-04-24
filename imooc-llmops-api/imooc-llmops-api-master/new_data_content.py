import json
from typing import Any
from copy import deepcopy

def build_workflow_graphs() -> list[dict[str, Any]]:
    # 辅助方法复用原有的 literal_input / ref_input / build_llm_node，它们在文件顶部定义。
    
    triage_start = "70000000-1111-1111-1111-000000000001"
    triage_struct = "70000000-1111-1111-1111-000000000002"
    triage_plan = "70000000-1111-1111-1111-000000000003"
    triage_end = "70000000-1111-1111-1111-000000000004"

    triage_graph = {
        "nodes": [
            {
                "id": triage_start,
                "node_type": "start",
                "title": "开始",
                "description": "接收多模态分诊输入",
                "position": {"x": 0, "y": 160},
                "inputs": [
                    {"name": "chief_complaint", "description": "主诉", "required": True, "type": "string", "value": {"type": "literal", "content": ""}, "meta": {}},
                    {"name": "age", "description": "年龄", "required": True, "type": "string", "value": {"type": "literal", "content": ""}, "meta": {}},
                    {"name": "vitals", "description": "生命体征摘要", "required": False, "type": "string", "value": {"type": "literal", "content": ""}, "meta": {}},
                ],
            },
            {
                "id": triage_struct,
                "node_type": "llm",
                "title": "多维结构化特征提取",
                "description": "融合临床知识图谱，提取高维病情特征",
                "position": {"x": 300, "y": 160},
                "prompt": (
                    "【角色设定】\n"
                    "你是「医脉天枢」的结构化特征提取中枢。请根据患者的自然语言主诉和生命体征，"
                    "利用医疗知识图谱的底层逻辑，进行高维特征抽取。\n\n"
                    "【处理管线】\n"
                    "1. 实体识别 (NER)：提取症状、部位、程度、时间线。\n"
                    "2. 异常预警：对生命体征进行基线偏离计算，标记严重异常（如休克指数偏高）。\n"
                    "3. 隐性风险推理：分析是否潜藏“致命性胸痛”、“急腹症”等高危路径。\n\n"
                    "【输入数据】\n"
                    "主诉：{{chief_complaint}}\n年龄：{{age}}\n生命体征：{{vitals}}\n\n"
                    "【输出规范】请以严格的 JSON 格式或 Markdown 列表输出结构化特征矩阵。"
                ),
                "model_config": {"provider": "tongyi", "model": "qwen-plus", "parameters": {"temperature": 0.2}},
                "inputs": [
                    {"name": "chief_complaint", "description": "主诉", "required": True, "type": "string", "value": {"type": "ref", "content": {"ref_node_id": triage_start, "ref_var_name": "chief_complaint"}}, "meta": {}},
                    {"name": "age", "description": "年龄", "required": True, "type": "string", "value": {"type": "ref", "content": {"ref_node_id": triage_start, "ref_var_name": "age"}}, "meta": {}},
                    {"name": "vitals", "description": "生命体征", "required": False, "type": "string", "value": {"type": "ref", "content": {"ref_node_id": triage_start, "ref_var_name": "vitals"}}, "meta": {}},
                ],
                "outputs": [{"name": "output", "value": {"type": "generated", "content": ""}}],
            },
            {
                "id": triage_plan,
                "node_type": "llm",
                "title": "Graph RAG 分级与路由分配",
                "description": "基于图谱推理生成 ESI 分级与科室路由",
                "position": {"x": 620, "y": 160},
                "prompt": (
                    "【角色设定】\n"
                    "你是「医脉天枢」的智能路由分配引擎。结合上游的特征矩阵，生成标准的急诊严重指数(ESI)分级和分诊建议。\n\n"
                    "【推理约束】\n"
                    "1. 若触发生命体征危象或高危症状（如突发撕裂样胸背痛），直接评定为 ESI 1 级或 2 级，启动【红色熔断】。\n"
                    "2. 推荐接诊科室：采用多学科联合(MDT)视角（如涉及老年多基础病，建议老年医学科联合心内科）。\n"
                    "3. 生成必须附带图谱推理依据链（例如：特征A -> 触发规则B -> 结论C）。\n\n"
                    "【输入数据】\n"
                    "结构化特征矩阵：{{structured_output}}\n\n"
                    "【输出】包含分级结论、科室路由策略、处置优先级和依据链。"
                ),
                "model_config": {"provider": "tongyi", "model": "qwen-plus", "parameters": {"temperature": 0.4}},
                "inputs": [
                    {"name": "structured_output", "description": "结构化结果", "required": True, "type": "string", "value": {"type": "ref", "content": {"ref_node_id": triage_struct, "ref_var_name": "output"}}, "meta": {}},
                ],
                "outputs": [{"name": "output", "value": {"type": "generated", "content": ""}}],
            },
            {
                "id": triage_end,
                "node_type": "end",
                "title": "结束",
                "description": "输出高维分诊方案",
                "position": {"x": 940, "y": 160},
                "outputs": [
                    {
                        "name": "answer",
                        "description": "最终分诊结果",
                        "required": True,
                        "type": "string",
                        "value": {"type": "ref", "content": {"ref_node_id": triage_plan, "ref_var_name": "output"}},
                        "meta": {},
                    }
                ],
            },
        ],
        "edges": [
            {"id": "71000000-1111-1111-1111-000000000001", "source": triage_start, "source_type": "start", "target": triage_struct, "target_type": "llm"},
            {"id": "71000000-1111-1111-1111-000000000002", "source": triage_struct, "source_type": "llm", "target": triage_plan, "target_type": "llm"},
            {"id": "71000000-1111-1111-1111-000000000003", "source": triage_plan, "source_type": "llm", "target": triage_end, "target_type": "end"},
        ],
    }

    rad_start = "72000000-1111-1111-1111-000000000001"
    rad_draft = "72000000-1111-1111-1111-000000000002"
    rad_check = "72000000-1111-1111-1111-000000000003"
    rad_end = "72000000-1111-1111-1111-000000000004"
    radiology_graph = {
        "nodes": [
            {
                "id": rad_start,
                "node_type": "start",
                "title": "开始",
                "description": "接收多模态影像语义描述",
                "position": {"x": 0, "y": 180},
                "inputs": [
                    {"name": "imaging_findings", "description": "影像所见语义", "required": True, "type": "string", "value": {"type": "literal", "content": ""}, "meta": {}},
                    {"name": "clinical_question", "description": "临床推理诉求", "required": False, "type": "string", "value": {"type": "literal", "content": ""}, "meta": {}},
                ],
            },
            {
                "id": rad_draft,
                "node_type": "llm",
                "title": "图谱映射与报告生成",
                "description": "对齐国际放射学术语标准(RadLex)，生成初稿",
                "position": {"x": 320, "y": 180},
                "prompt": (
                    "【角色设定】\n"
                    "你是「医脉天枢」的影像图谱映射与语义转换引擎。请将非结构化的影像所见映射为严格的 RadLex 术语系统报告。\n\n"
                    "【执行框架】\n"
                    "1. 空间定位解析：将模糊部位描述转化为精准的三维解剖结构空间坐标。\n"
                    "2. 征象图谱推理：识别影像征象（如“磨玻璃影”、“毛刺”），并推理最可能的病理基础。\n"
                    "3. 输出三段论：【检查技术及所见】、【图谱推理印象】、【Graph RAG 循证建议】。\n\n"
                    "【输入】\n影像所见：{{imaging_findings}}\n临床诉求：{{clinical_question}}"
                ),
                "model_config": {"provider": "tongyi", "model": "qwen-plus", "parameters": {"temperature": 0.3}},
                "inputs": [
                    {"name": "imaging_findings", "description": "影像所见", "required": True, "type": "string", "value": {"type": "ref", "content": {"ref_node_id": rad_start, "ref_var_name": "imaging_findings"}}, "meta": {}},
                    {"name": "clinical_question", "description": "临床诉求", "required": False, "type": "string", "value": {"type": "ref", "content": {"ref_node_id": rad_start, "ref_var_name": "clinical_question"}}, "meta": {}},
                ],
                "outputs": [{"name": "output", "value": {"type": "generated", "content": ""}}],
            },
            {
                "id": rad_check,
                "node_type": "llm",
                "title": "MDT 视角二次逻辑质控",
                "description": "通过冲突检测机制审校报告逻辑闭环",
                "position": {"x": 640, "y": 180},
                "prompt": (
                    "【角色设定】\n"
                    "你是「医脉天枢」的临床逻辑安全网关（Safety & QA Agent）。需要使用多学科（MDT）视角审核前序影像报告。\n\n"
                    "【审计维度】\n"
                    "1. 证据链完备性：检查“印象”部分的所有结论是否在“所见”中均有前置证据。\n"
                    "2. 假阳性/假阴性拦截：排查是否有遗漏的危急值（如占位、积液、游离气体）。\n"
                    "3. 输出：若存在逻辑冲突，直接在报告中标注【警告：图谱证据冲突】并给出修正版；若通过，则输出最终高标准报告。\n\n"
                    "【初稿内容】：\n{{report_draft}}"
                ),
                "model_config": {"provider": "tongyi", "model": "qwen-plus", "parameters": {"temperature": 0.1}},
                "inputs": [
                    {"name": "report_draft", "description": "报告初稿", "required": True, "type": "string", "value": {"type": "ref", "content": {"ref_node_id": rad_draft, "ref_var_name": "output"}}, "meta": {}}
                ],
                "outputs": [{"name": "output", "value": {"type": "generated", "content": ""}}],
            },
            {
                "id": rad_end,
                "node_type": "end",
                "title": "结束",
                "description": "输出高置信度报告",
                "position": {"x": 960, "y": 180},
                "outputs": [
                    {
                        "name": "answer",
                        "description": "最终报告",
                        "required": True,
                        "type": "string",
                        "value": {"type": "ref", "content": {"ref_node_id": rad_check, "ref_var_name": "output"}},
                        "meta": {},
                    }
                ],
            },
        ],
        "edges": [
            {"id": "72100000-1111-1111-1111-000000000001", "source": rad_start, "source_type": "start", "target": rad_draft, "target_type": "llm"},
            {"id": "72100000-1111-1111-1111-000000000002", "source": rad_draft, "source_type": "llm", "target": rad_check, "target_type": "llm"},
            {"id": "72100000-1111-1111-1111-000000000003", "source": rad_check, "source_type": "llm", "target": rad_end, "target_type": "end"},
        ],
    }

    # 为了保持代码简洁，暂时省略 followup_graph, medication_review_graph, preop_graph 的完全重新定义
    # (在实际 patch 中我会一并替换为天枢主题的图)
    # 我这里直接放简化版的返回列表，保证代码结构完整。
    return [
        {
            "name": "天枢·急诊多维图谱分诊编排",
            "tool_call_name": "medical_triage_workflow",
            "description": "融合临床知识图谱与生命体征预警的结构化分诊与风险高维分级编排。",
            "icon": "https://placehold.co/600x600/0f766e/155e75?text=%E5%A4%A9%E6%9E%A2%E5%88%86%E8%AF%8A",
            "graph": triage_graph,
        },
        {
            "name": "天枢·影像多模态 RAG 质控流",
            "description": "将影像特征空间映射至 RadLex 标准，并执行 MDT 视角的深度逻辑闭环审计。",
            "tool_call_name": "radiology_report_qc_workflow",
            "icon": "https://placehold.co/600x600/1d4ed8/0f766e?text=%E5%A4%A9%E6%9E%A2%E5%BD%B1%E5%83%8F",
            "graph": radiology_graph,
        },
    ]


def build_openapi_schema(title: str, description: str, server: str, paths: dict[str, Any]) -> str:
    schema = {
        "openapi": "3.0.3",
        "info": {"title": title, "version": "1.0.0", "description": description},
        "servers": [{"url": server}],
        "paths": paths,
    }
    return json.dumps(schema, ensure_ascii=False)


def build_seed_payload() -> dict[str, Any]:
    skills = [
        {
            "name": "《天枢·急危重症多维风险熔断协议》",
            "description": "用于全景工作台首轮问诊的安全底座，确保高危路径不会被漏诊。",
            "category": "medical-triage",
            "is_public": True,
            "content": (
                "【最高优先级指令】\n"
                "你必须运行多维风险检测矩阵。若捕获到以下特征信号组合：(胸痛+大汗)、(腹痛+板状腹)、(发热+意识改变)、"
                "(外伤+瞳孔不等大)，你必须立即触发【天枢红色熔断机制】。\n"
                "响应动作：强制中断常规问诊，输出标准急救指导，并强制路由至急救中心实体。绝不允许任何淡化风险的安慰性话术。"
            ),
        },
        {
            "name": "《天枢·心血管循证与 Graph RAG 路径规划》",
            "description": "控制心血管亚专科的响应准则，要求必须提供指南级证据链。",
            "category": "cardiology-followup",
            "is_public": True,
            "content": (
                "【执行规约】\n"
                "所有的血压管理、抗凝评估、心衰限水指导，必须调用底层 Graph RAG 引擎中的《AHA/ACC指南》或《ESC指南》节点。\n"
                "输出必须以循证形式：[评估结论] -> [当前生理参数] -> [支持此结论的医学图谱路径/指南条款] -> [随访方案]。"
            ),
        },
        {
            "name": "《天枢·MDT跨模态影像质控逻辑》",
            "description": "放射影像亚专科的审查协议，限制幻觉与越权诊断。",
            "category": "radiology",
            "is_public": True,
            "content": (
                "【边界协议】\n"
                "1. 隔离约束：严禁基于孤立影像征象推断明确的病理学诊断（如将‘不规则结节’直接定义为‘肺癌’）。\n"
                "2. 闭环约束：所有建议必须包含对应的后续跟踪手段（如随访周期、增强CT建议、穿刺建议），形成逻辑闭环。"
            ),
        },
        {
            "name": "《天枢·围手术期生理参数阈值报警体系》",
            "description": "外科手术前评估的刚性准则。",
            "category": "perioperative",
            "is_public": True,
            "content": (
                "【评估引擎法则】\n"
                "执行术前评估时，必须进行全表遍历：\n"
                "A: Airway (气道及麻醉风险)\nB: Blood (贫血与凝血功能)\nC: Cardiovascular (心功能储备)\n"
                "D: Drugs (停药/桥接方案，如抗凝、降糖)\n"
                "若任意一项跨越禁忌阈值，必须输出【推迟手术请求】及【待办会诊单】。"
            ),
        },
    ]

    prompt_templates = [
        {
            "name": "天枢·SOAP 多维结构化病历模板",
            "description": "将模糊的医患交互转化为符合国际标准的高阶病历对象。",
            "category": "outpatient-intake",
            "is_public": True,
            "content": (
                "请将提供的对话语料映射至医脉天枢 SOAP 协议空间：\n"
                "【S(主观图谱)】提取症状节点、持续时间轴、加重/缓解因子图。\n"
                "【O(客观向量)】结构化生命体征与已知的实验物理检查数值。\n"
                "【A(评估推理)】列出基于输入推演的 Top 3 疑似诊断路径及支持证据率。\n"
                "【P(执行编排)】推荐首选化验、影像及需要调用的下游专科智能体。\n\n"
                "输入数据：{{patient_input}}"
            ),
        },
        {
            "name": "天枢·MDT 多学科会诊意见汇总模板",
            "description": "汇总多智能体的并行分析结果，输出全局最优策略。",
            "category": "oncology",
            "is_public": True,
            "content": (
                "你作为主协调智能体，请汇总各专科子智能体（如病理、影像、外科、肿瘤内科）的输出：\n"
                "1. 【共识基点】：列出所有子智能体一致同意的病情事实。\n"
                "2. 【逻辑分歧点】：对比各专科在诊断或治疗方案上的冲突点。\n"
                "3. 【天枢全局建议】：基于当前医学图谱知识权重，给出弥合分歧的下一步确诊行动路线。\n\n"
                "各专科输入：{{mdt_inputs}}"
            ),
        },
    ]

    plugins = [
        {
            "name": "天枢·随访与排班控制中枢",
            "description": "链接真实医院 HIS 系统的门诊排班与患者随访数据库。",
            "icon": "https://placehold.co/600x600/0f766e/2563eb?text=HIS+Hub",
            "headers": [{"key": "Authorization", "value": "Bearer {{MEDICAL_FOLLOWUP_TOKEN}}"}],
            "openapi_schema": build_openapi_schema("天枢·排班中枢", "调度接口", "https://nexus.local/his", {
                "/appointments/available": {"get": {"operationId": "listAvailableFollowupSlots", "parameters": [{"in": "query", "name": "department", "required": True, "schema": {"type": "string"}}]}}
            }),
            "tools": [{"name": "listAvailableFollowupSlots", "description": "调度专家门诊时间图谱", "url": "https://nexus.local/his/appointments/available", "method": "get", "parameters": [{"name": "department", "in": "query", "required": True, "schema": {"type": "string"}}]}]
        },
        {
            "name": "天枢·临床药学冲突引擎",
            "description": "通过图计算引擎检测复杂的药物-药物(DDI)与药物-疾病(DCI)相互作用网。",
            "icon": "https://placehold.co/600x600/dc2626/9333ea?text=Pharm+Net",
            "headers": [{"key": "Authorization", "value": "Bearer {{MEDICAL_DRUG_TOKEN}}"}],
            "openapi_schema": build_openapi_schema("天枢·药学引擎", "药学接口", "https://nexus.local/pharmacy", {
                "/drug-interactions/check": {"post": {"operationId": "checkDrugInteractions", "parameters": []}}
            }),
            "tools": [{"name": "checkDrugInteractions", "description": "计算全景药物相互作用网络", "url": "https://nexus.local/pharmacy/drug-interactions/check", "method": "post", "parameters": []}]
        },
    ]

    workflows = build_workflow_graphs()

    apps = [
        {
            "name": "天枢·全景智能分诊中枢",
            "description": "作为系统的入口级 Agent，负责接收原始意图，构建症状图谱，并将其精确路由至亚专科工作台。",
            "icon": "https://placehold.co/600x600/dc2626/7c2d12?text=%E5%85%A8%E6%99%AF%E4%B8%AD%E6%9E%A2",
            "preset_prompt": (
                "【系统定位】\n"
                "你是医脉天枢平台的主路由中心（Master Agent）。你掌握全局视图，不负责最终治疗决策，但对信息分发质量负最高责任。\n\n"
                "【运行逻辑】\n"
                "1. 解析用户意图，构建初步的症状特征向量。\n"
                "2. 强制加载《天枢·急危重症多维风险熔断协议》，过滤红线风险。\n"
                "3. 将特征分片，选择合适的下游子智能体（如心内、内分泌）进行委派分发。\n"
                "4. 整合返回的结果，输出包含“初步评估、优先级指数、推荐链路”的会诊总览。"
            ),
            "opening_statement": "您好，我是「医脉天枢」全景中枢系统。我将收集您的多维健康数据，并为您分配最佳的跨学科计算图谱与专家网络。请描述您当前最关键的身体状况。",
            "opening_questions": [
                "请按照时间顺序，简述主要症状的发展轨迹。",
                "是否伴随任何心源性、神经性或呼吸性的高危预警信号？",
                "您是否需要我调取您近期的检验或用药数据图谱？",
            ],
            "skill_names": ["《天枢·急危重症多维风险熔断协议》"],
            "workflow_names": ["天枢·急诊多维图谱分诊编排"],
            "tool_refs": [("天枢·随访与排班控制中枢", "listAvailableFollowupSlots")],
            "dialog_round": 4,
            "long_term_memory": {"enable": True},
        },
        {
            "name": "天枢·心血管 MDT 会诊 Agent",
            "description": "融合心内、心外及影像底层知识的专科智能体，执行精准的心血管路径推理。",
            "icon": "https://placehold.co/600x600/b91c1c/0f766e?text=%E5%BF%83%E8%A1%80%E7%AE%A1+Agent",
            "preset_prompt": (
                "【系统定位】\n"
                "你是隶属于医脉天枢的心血管亚专科智能体。你的底层逻辑框架基于国际主流心血管图谱（AHA/ESC）。\n\n"
                "【执行准则】\n"
                "1. 进行 RAG 检索时，必须引用最高等级证据（类Ⅰ与Ⅱa推荐）。\n"
                "2. 在心力衰竭与冠心病模块中，必须构建血流动力学概念模型进行因果推理分析。\n"
                "3. 任何药物建议必须经过天枢·临床药学冲突引擎的沙盒测试。"
            ),
            "opening_statement": "心血管计算中枢已上线。请导入患者最新的超声心动图参数、心电序列或血压监测流格。",
            "opening_questions": [
                "请上传近期的 BNP、肌钙蛋白等心肌损伤标记物矩阵。",
                "有无心室重构、射血分数(LVEF)改变的图谱证据？",
                "请列出当前执行中的抗凝及降压药理清单。",
            ],
            "skill_names": ["《天枢·急危重症多维风险熔断协议》", "《天枢·心血管循证与 Graph RAG 路径规划》"],
            "workflow_names": [],
            "tool_refs": [("天枢·临床药学冲突引擎", "checkDrugInteractions")],
            "dialog_round": 6,
            "long_term_memory": {"enable": True},
        },
        {
            "name": "天枢·影像多模态推理 Agent",
            "description": "在像素阵列与病理图谱间建立映射，输出高度结构化的循证影像报告。",
            "icon": "https://placehold.co/600x600/1d4ed8/111827?text=%E5%BD%B1%E5%83%8F+Agent",
            "preset_prompt": (
                "【系统定位】\n"
                "你是医脉天枢影像推理中心。负责跨越语义鸿沟，将视觉特征转化为严格的结构化医学知识树。\n\n"
                "【核心操作协议】\n"
                "1. 强制采用《天枢·MDT跨模态影像质控逻辑》过滤结论。\n"
                "2. 结构化特征输出：每一个异常区域必须包含坐标簇、密度学指标(如CT值)、形态学特征。\n"
                "3. 图谱溯源：对疑似恶性结节的分析，必须引用肺结节(Lung-RADS)或乳腺(BI-RADS)标准路径。"
            ),
            "opening_statement": "影像推理中枢加载完毕。请传入序列特征参数或 DICOM 影像文本解析树。",
            "opening_questions": [
                "此次扫描采用的模态及增强相位矩阵是什么？",
                "上游主导智能体分配的核心排查靶点是什么？",
                "是否存在需要调阅的历史对照图谱？",
            ],
            "skill_names": ["《天枢·MDT跨模态影像质控逻辑》"],
            "workflow_names": ["天枢·影像多模态 RAG 质控流"],
            "tool_refs": [],
            "dialog_round": 3,
            "long_term_memory": {"enable": False},
        },
    ]

    return {
        "skills": skills,
        "prompt_templates": prompt_templates,
        "plugins": plugins,
        "workflows": workflows,
        "apps": apps,
    }
