# Schema 与 Dict 序列化 — 问答复盘

> 背景：在修复应用广场和插件广场的前端硬编码问题时，发现两个模块使用了不同的序列化方式，由此展开的讨论。

---

## Q1: 为什么应用广场的 builtin_app_schema.py 和插件广场的 builtin_tool_service.py 不一样？

这是项目中**架构风格不一致**的历史遗留问题，两个模块在不同时期编写。

### 应用广场 — 使用 Schema 层序列化

```
Handler → Service(返回 Entity) → Handler 用 Schema 序列化 → 返回 JSON
```

```python
# builtin_app_handler.py
builtin_apps = self.builtin_app_service.get_builtin_apps()  # 返回 Entity 列表
resp = GetBuiltinAppsResp(many=True)
return success_json(resp.dump(builtin_apps))  # Schema 负责序列化
```

Service 返回原始的 `BuiltinAppEntity` 对象，由 Marshmallow Schema 控制哪些字段输出、如何转换。

### 插件广场 — Service 层直接构造 dict

```
Handler → Service(返回 dict) → Handler 直接返回 JSON
```

```python
# builtin_tool_handler.py
builtin_tools = self.builtin_tool_service.get_builtin_tools()  # 返回 dict 列表
return success_json(builtin_tools)  # 直接返回，没有 Schema
```

Service 内部用 `model_dump()` 组装好了 dict，Handler 拿到直接返回。

---

## Q2: 哪种写法更好？

**使用 Schema 层更好**，原因：

| 对比项 | Schema 层（应用广场） | Service 直接构造 dict（插件广场） |
|--------|----------------------|-------------------------------|
| 职责分离 | 清晰（Service 管业务，Schema 管序列化） | 混合（Service 同时管业务和序列化） |
| 字段安全 | 白名单（include），默认不暴露 | 黑名单（exclude），默认暴露 |
| 改响应格式 | 只改 Schema，Service 不动 | 要改 Service，业务和序列化混在一起 |
| 项目一致性 | 符合项目规范 | 例外 |

---

## Q3: Schema 与 Dict 是什么？

### Dict（字典）

Python 基础数据结构，一组键值对：

```python
builtin_tool = {
    "name": "google",
    "label": "Google",
    "description": "谷歌搜索",
    "created_at": 1722498386,
}
```

简单直接，但没有约束——想放什么就放什么，没有检查。

### Schema（模式/模板）

项目使用 **Marshmallow** 库的 Schema，一个**序列化模板**，预先定义 API 响应要返回哪些字段、什么类型：

```python
class GetBuiltinAppsResp(Schema):
    id = fields.String(dump_default="")
    name = fields.String(dump_default="")
    author = fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)
```

Schema 负责三件事：
1. **过滤** — 只输出定义了的字段，多余的自动丢弃
2. **类型转换** — 保证字段类型正确
3. **默认值** — 字段缺失时给默认值

### 类比

把一份员工档案对外公开：
- **Dict 写法**：你自己手动挑信息抄到纸上，可能不小心把身份证号也抄上去
- **Schema 写法**：有一张固定表格（姓名、职位、部门），档案交给表格，只提取这三项，其他信息不会泄露

---

## Q4: 它们为什么是 API 的响应格式？

### 完整请求链路（以"获取内置应用列表"为例）

```
前端浏览器发起请求: GET /builtin-apps
        ↓
    Flask 路由分发
        ↓
    Handler（处理器）
        ↓
    Service（服务层）
        ↓
    读取 YAML 文件，得到 BuiltinAppEntity 对象列表
        ↓
    ⭐ Entity 对象不能直接发给前端（字段太多，有些前端不需要）
        ↓
    Schema 或 Dict 做序列化（Python 对象 → JSON 格式）
        ↓
    success_json() 包装统一响应格式
        ↓
    HTTP 响应返回给前端
```

Schema 和 Dict 都是在做同一件事 — **把后端的 Python 对象转换成前端能理解的 JSON 数据**。只是方式不同。

---

## Q5: `resp.dump(entities)` 详解

### 代码

```python
resp = GetBuiltinAppsResp(many=True)
return success_json(resp.dump(entities))
```

### 逐步拆解

#### 1) `GetBuiltinAppsResp(many=True)` — 实例化 Schema

- `many=True` 表示要处理**列表**（多条数据），不是单个对象
- `many=False` 表示处理单个对象

#### 2) `entities` — 原始数据

Service 返回的 BuiltinAppEntity 列表，包含十几个字段：

```python
[
  BuiltinAppEntity(
    id="6b476bc2-...",
    name="面试助手",
    author="LLMOps-Platform",
    preset_prompt="...",      # 前端列表页不需要
    tools=[...],              # 前端列表页不需要
    retrieval_config={...},   # 前端列表页不需要
    # ... 十几个字段
  ),
  ...
]
```

#### 3) `resp.dump(entities)` — 序列化过程

```python
class GetBuiltinAppsResp(Schema):
    id = fields.String(dump_default="")
    name = fields.String(dump_default="")
    author = fields.String(dump_default="")
    model_config = fields.Dict(dump_default={})
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data, **kwargs):
        # dump 之前先执行这个钩子，做字段映射和过滤
        return {
            **data.model_dump(include={"id", "name", "author", "created_at", ...}),
            "model_config": {
                "provider": data.language_model_config.get("provider", ""),
                "model": data.language_model_config.get("model", ""),
            }
        }
```

执行流程：
```
Entity 对象
    ↓  @pre_dump 钩子先执行（字段过滤 + 映射）
    ↓  Schema 按字段定义做类型检查和默认值填充
    ↓
输出 Python dict 列表（只剩需要的字段）
```

#### 4) `success_json(...)` — 包装统一响应

```json
{
  "code": "success",
  "data": [
    {"id": "...", "name": "面试助手", "author": "LLMOps-Platform", ...},
    {"id": "...", "name": "员工培训顾问", "author": "LLMOps-Platform", ...}
  ],
  "message": ""
}
```

### 整体流程图

```
YAML 文件
  ↓ BuiltinAppManager 加载
BuiltinAppEntity 列表（十几个字段）
  ↓ @pre_dump 钩子（过滤 + 映射）
  ↓ Schema 字段定义（类型检查 + 默认值）
Python dict 列表（只剩需要的字段）
  ↓ success_json()（包装统一格式）
JSON 响应  →  返回给前端浏览器
```

---

## 相关文件

| 文件 | 作用 |
|------|------|
| `internal/schema/builtin_app_schema.py` | 应用广场的 Marshmallow Schema 定义 |
| `internal/handler/builtin_app_handler.py` | 应用广场 Handler，使用 Schema 序列化 |
| `internal/service/builtin_tool_service.py` | 插件广场 Service，直接构造 dict |
| `internal/handler/builtin_tool_handler.py` | 插件广场 Handler，直接返回 dict |
| `pkg/response/__init__.py` | `success_json()` 统一响应包装函数 |

---

## 关联知识：icon vs icons 字段名不匹配

在排查过程中还发现了 `icon`（单数）与 `icons`（复数）字段名不匹配导致的 bug：

- **App ORM 模型**（数据库列）：`icons`
- **前端/表单/Entity**：`icon`
- 使用 `**dict` 解包时字段名不匹配会导致运行时错误

已修复的位置：
- `builtin_app_service.py` — 创建 App 时 `icons=builtin_app.icon`
- `app_handler.py` — 更新 App 时 `icons=req.icon.data`

教训：**使用 `model_dump()` 解包传参时，必须确认字段名与目标模型完全一致**。
