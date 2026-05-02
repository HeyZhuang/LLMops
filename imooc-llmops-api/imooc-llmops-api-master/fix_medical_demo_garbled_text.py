#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Repair garbled Chinese text for the seeded medical linkage demo.
This file intentionally uses ASCII-only unicode escapes to avoid
terminal or shell encoding corruption.
"""
from __future__ import annotations

import os
from pathlib import Path

import dotenv
import psycopg2
from psycopg2.extras import Json


ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"

CONVERSATION_ID = "f3ce3b05-9a55-4af3-be8b-60b127cd5b07"
MESSAGE_ID = "7de7110b-b0db-4f81-bef3-066ef7767f2c"


def zh(text: str) -> str:
    return text.encode("ascii").decode("unicode_escape")


def main() -> None:
    dotenv.load_dotenv(ENV_PATH)
    dsn = os.environ["SQLALCHEMY_DATABASE_URI"]

    conversation_name = zh(
        "\\u5929\\u67a2\\u00b7\\u68c0\\u7d22+\\u63d2\\u4ef6+\\u5de5\\u4f5c\\u6d41\\u8054\\u52a8\\u6f14\\u793a"
    )
    conversation_summary = zh(
        "\\u5c55\\u793a\\u533b\\u7597\\u77e5\\u8bc6\\u5e93\\u68c0\\u7d22\\u3001\\u63d2\\u4ef6\\u6392\\u73ed\\u548c\\u5206\\u8bca\\u5de5\\u4f5c\\u6d41\\u534f\\u540c\\u75d5\\u8ff9\\u3002"
    )
    query_text = zh(
        "\\u8bf7\\u57fa\\u4e8e\\u73b0\\u6709\\u533b\\u7597\\u77e5\\u8bc6\\u5e93\\uff0c\\u5bf9\\u4e00\\u4f4d\\u80f8\\u75db\\u5408\\u5e76\\u9ad8\\u8840\\u538b\\u60a3\\u8005\\u505a\\u5206\\u8bca\\u5224\\u65ad\\uff0c\\u5e76\\u5c55\\u793a\\u63d2\\u4ef6\\u6392\\u671f\\u4e0e\\u5de5\\u4f5c\\u6d41\\u534f\\u540c\\u75d5\\u8ff9\\u3002"
    )
    answer_text = zh(
        "\\u672c\\u6b21\\u6f14\\u793a\\u5df2\\u7ecf\\u5728\\u4e00\\u4e2a\\u533b\\u7597\\u5e94\\u7528\\u91cc\\u4e32\\u8d77\\u4e86\\u68c0\\u7d22\\u3001\\u63d2\\u4ef6\\u548c\\u5de5\\u4f5c\\u6d41\\u3002"
        "\\u6211\\u5148\\u4ece\\u201c\\u533b\\u8109\\u5929\\u67a2\\u201d\\u77e5\\u8bc6\\u5e93\\u68c0\\u7d22\\u5230\\u5fc3\\u810f\\u5faa\\u73af\\u7cfb\\u7edf\\u8d44\\u6599\\uff0c\\u5176\\u4e2d\\u63d0\\u5230 130\\u2013139/80\\u201389 mmHg \\u4eba\\u7fa4\\u5e94\\u5c3d\\u65e9\\u8fdb\\u884c\\u751f\\u6d3b\\u65b9\\u5f0f\\u7ba1\\u7406\\uff0c"
        "\\u5e76\\u5f3a\\u8c03\\u63d0\\u524d\\u5e72\\u9884\\u3001\\u4fdd\\u62a4\\u5fc3\\u529f\\u80fd\\uff1b\\u968f\\u540e\\u8c03\\u7528\\u968f\\u8bbf\\u4e0e\\u6392\\u73ed\\u63d2\\u4ef6\\uff0c\\u67e5\\u8be2\\u5230\\u53ef\\u7528\\u590d\\u8bca\\u65f6\\u6bb5\\uff1b\\u6700\\u540e\\u89e6\\u53d1\\u201c\\u5929\\u67a2\\u00b7\\u6025\\u8bca\\u591a\\u7ef4\\u56fe\\u8c31\\u5206\\u8bca\\u7f16\\u6392\\u201d\\u5de5\\u4f5c\\u6d41\\uff0c"
        "\\u628a\\u80f8\\u75db\\u3001\\u9ad8\\u8840\\u538b\\u3001\\u98ce\\u9669\\u5206\\u5c42\\u548c\\u540e\\u7eed\\u590d\\u8bca\\u52a8\\u4f5c\\u6574\\u7406\\u6210\\u7ed3\\u6784\\u5316\\u7ed3\\u8bba\\u3002\\u8fd9\\u6837\\u4f60\\u5728\\u9875\\u9762\\u91cc\\u5c31\\u80fd\\u770b\\u5230 dataset_retrieval\\u3001agent_action\\u3001workflow \\u8054\\u52a8\\u75d5\\u8ff9\\u3002"
    )

    thought_rows = [
        {
            "position": 1,
            "event": "agent_thought",
            "thought": zh(
                "\\u7528\\u6237\\u5e0c\\u671b\\u5728\\u540c\\u4e00\\u4e2a\\u533b\\u7597\\u5e94\\u7528\\u91cc\\u770b\\u5230\\u77e5\\u8bc6\\u5e93\\u68c0\\u7d22\\u3001\\u63d2\\u4ef6\\u8c03\\u7528\\u548c\\u5de5\\u4f5c\\u6d41\\u7f16\\u6392\\u4e09\\u79cd\\u80fd\\u529b\\u534f\\u540c\\uff0c\\u6211\\u9700\\u8981\\u6309\\u8fd9\\u4e2a\\u8def\\u5f84\\u7ec4\\u7ec7\\u56de\\u7b54\\u3002"
            ),
            "observation": "",
            "tool": "",
            "tool_input": {},
            "answer": "",
        },
        {
            "position": 2,
            "event": "dataset_retrieval",
            "thought": "",
            "observation": zh(
                "\\u77e5\\u8bc6\\u5e93\\u547d\\u4e2d\\u201c\\u5fc3\\u810f\\u5faa\\u73af\\u7cfb\\u7edf.docx\\u201d\\u7247\\u6bb5\\uff1a130\\u2013139/80\\u201389 mmHg \\u4eba\\u7fa4\\u53ef\\u901a\\u8fc7\\u751f\\u6d3b\\u65b9\\u5f0f\\u7ba1\\u7406\\u964d\\u4f4e\\u8fdc\\u671f\\u5fc3\\u8870\\u4e0e\\u5352\\u4e2d\\u53d1\\u751f\\u7387\\uff0c\\u5e76\\u5f3a\\u8c03\\u63d0\\u524d\\u5e72\\u9884\\u3001\\u4fdd\\u62a4\\u5fc3\\u529f\\u80fd\\u3002"
            ),
            "tool": "dataset_retrieval",
            "tool_input": {"query": zh("\\u80f8\\u75db \\u9ad8\\u8840\\u538b \\u65e9\\u671f\\u5e72\\u9884 \\u5fc3\\u529f\\u80fd")},
            "answer": "",
        },
        {
            "position": 3,
            "event": "agent_action",
            "thought": zh(
                "\\u60a3\\u8005\\u9700\\u8981\\u540e\\u7eed\\u590d\\u8bca\\u5b89\\u6392\\uff0c\\u6211\\u8c03\\u7528\\u968f\\u8bbf\\u4e0e\\u6392\\u73ed\\u63a7\\u5236\\u4e2d\\u67a2\\u67e5\\u8be2\\u53ef\\u7528\\u65f6\\u6bb5\\u3002"
            ),
            "observation": zh(
                "\\u63d2\\u4ef6 `listAvailableFollowupSlots` \\u8fd4\\u56de\\u53ef\\u9884\\u7ea6\\u65f6\\u6bb5\\uff1a\\u5468\\u4e09 14:00 \\u5fc3\\u5185\\u968f\\u8bbf\\u95e8\\u8bca\\u3001\\u5468\\u56db 09:30 \\u9ad8\\u8840\\u538b\\u590d\\u8bca\\u95e8\\u8bca\\u3002"
            ),
            "tool": "listAvailableFollowupSlots",
            "tool_input": {"department": "cardiology", "priority": "high"},
            "answer": "",
        },
        {
            "position": 4,
            "event": "agent_action",
            "thought": zh(
                "\\u9700\\u8981\\u628a\\u80f8\\u75db\\u4e0e\\u8840\\u538b\\u98ce\\u9669\\u8fdb\\u4e00\\u6b65\\u7ed3\\u6784\\u5316\\uff0c\\u6240\\u4ee5\\u89e6\\u53d1\\u5206\\u8bca\\u5de5\\u4f5c\\u6d41\\u505a\\u591a\\u7ef4\\u98ce\\u9669\\u7f16\\u6392\\u3002"
            ),
            "observation": zh(
                "\\u5de5\\u4f5c\\u6d41 `wf_medical_triage_workflow` \\u8f93\\u51fa\\uff1a\\u5efa\\u8bae\\u4f18\\u5148\\u8bc6\\u522b\\u80f8\\u75db\\u5371\\u9669\\u4fe1\\u53f7\\u3001\\u5b8c\\u6210\\u8840\\u538b\\u98ce\\u9669\\u5206\\u5c42\\uff0c\\u5e76\\u5728\\u6392\\u9664\\u6025\\u5371\\u91cd\\u75c7\\u540e\\u8fdb\\u5165\\u5fc3\\u5185\\u968f\\u8bbf\\u8def\\u5f84\\u3002"
            ),
            "tool": "wf_medical_triage_workflow",
            "tool_input": {
                "chief_complaint": zh("\\u80f8\\u75db\\u4f34\\u8840\\u538b\\u6ce2\\u52a8"),
                "age": "56",
                "vitals": zh("\\u8840\\u538b 138/88 mmHg\\uff0c\\u5fc3\\u7387 96 \\u6b21/\\u5206"),
            },
            "answer": "",
        },
        {
            "position": 5,
            "event": "agent_message",
            "thought": "",
            "observation": "",
            "tool": "",
            "tool_input": {},
            "answer": answer_text,
        },
    ]

    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    try:
        cur = conn.cursor()

        cur.execute(
            """
            update conversation
               set name = %s,
                   summary = %s,
                   updated_at = now()
             where id = %s::uuid
            """,
            (conversation_name, conversation_summary, CONVERSATION_ID),
        )

        cur.execute(
            """
            update message
               set query = %s,
                   message = %s,
                   answer = %s,
                   updated_at = now()
             where id = %s::uuid
            """,
            (
                query_text,
                Json(
                    [
                        {"role": "user", "content": query_text},
                        {"role": "assistant", "content": answer_text},
                    ]
                ),
                answer_text,
                MESSAGE_ID,
            ),
        )

        for row in thought_rows:
            cur.execute(
                """
                update message_agent_thought
                   set event = %s,
                       thought = %s,
                       observation = %s,
                       tool = %s,
                       tool_input = %s,
                       answer = %s,
                       updated_at = now()
                 where message_id = %s::uuid
                   and position = %s
                """,
                (
                    row["event"],
                    row["thought"],
                    row["observation"],
                    row["tool"],
                    Json(row["tool_input"]),
                    row["answer"],
                    MESSAGE_ID,
                    row["position"],
                ),
            )

        conn.commit()
        print("medical demo garbled text repaired")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
