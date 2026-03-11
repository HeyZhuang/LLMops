# 使用 uv 配置 Python 3.11 环境（保姆级教程）

> 适用于 Windows 11，本项目后端 `imooc-llmops-api`

---

## 第一步：用 uv 安装 Python 3.11

打开终端（PowerShell / CMD / Git Bash 均可），执行：

```bash
uv python install 3.11
```

等待下载完成后，验证：

```bash
uv python list --only-installed
```

确认列表中出现 `cpython-3.11.x` 即可。

---

## 第二步：删除旧的虚拟环境

进入后端目录，删除旧环境：

```bash
cd imooc-llmops-api/imooc-llmops-api-master

# 如果存在旧的 .venv，删掉它
rm -rf .venv
```

> 如果你的 .venv 在其他位置，请对应删除。

---

## 第三步：用 uv 创建 Python 3.11 虚拟环境

```bash
uv venv --python 3.11
```

执行后会在当前目录生成 `.venv` 文件夹，并输出类似：

```
Using CPython 3.11.x
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
```

---

## 第四步：激活虚拟环境

根据你的终端选择一种方式：

```bash
# PowerShell
.venv\Scripts\Activate.ps1

# CMD
.venv\Scripts\activate.bat

# Git Bash
source .venv/Scripts/activate
```

激活后终端提示符前面会出现 `(.venv)`，确认版本：

```bash
python --version
# 输出：Python 3.11.x ✅
```

---

## 第五步：用 uv 安装项目依赖

```bash
uv pip install -r requirements.txt
```

> `uv pip install` 比原生 pip 快 10-100 倍，耐心等待即可。
>
> 如果某些包安装失败（如 `torch`），可以尝试加镜像源：
>
> ```bash
> uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```

---

## 第六步：验证环境

```bash
# 确认 Python 版本
python --version

# 确认关键包已安装
python -c "import flask; print('Flask', flask.__version__)"
python -c "import langchain; print('LangChain', langchain.__version__)"
```

输出类似：

```
Python 3.11.x
Flask 3.0.2
LangChain 0.2.16
```

---

## 第七步：正常启动项目

```bash
# 1. 配置环境变量（首次需要）
cp .env.example .env
# 编辑 .env 填写数据库、Redis、API Key 等配置

# 2. 启动 Weaviate（另开终端）
cd docker/docker
docker-compose -f docker-compose-weaviate-only.yaml up -d

# 3. 初始化数据库（首次需要）
python init_db.py
python create_user.py

# 4. 启动后端
python -m app.http.app

# 5. 启动 Celery（另开终端，激活虚拟环境后）
celery -A app.celery worker --loglevel=info --pool=solo

# 6. 启动前端（另开终端）
cd imooc-llmops-ui/imooc-llmops-ui-master
npm install
npm run dev
```

---

## 常用 uv 命令速查

| 命令 | 说明 |
|------|------|
| `uv python install 3.11` | 安装 Python 3.11 |
| `uv python list --only-installed` | 查看已安装的 Python 版本 |
| `uv venv --python 3.11` | 用 3.11 创建虚拟环境 |
| `uv pip install -r requirements.txt` | 安装依赖（极速） |
| `uv pip install <package>` | 安装单个包 |
| `uv pip list` | 查看已安装的包 |
| `uv pip freeze` | 导出依赖列表 |
| `uv python uninstall 3.13` | 卸载不需要的版本 |

---

## 常见问题

### Q: `uv python install` 下载很慢？

设置镜像（Git Bash / PowerShell）：

```bash
# 临时使用清华镜像安装依赖
uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: torch 安装失败？

PyTorch 体积较大，可单独安装：

```bash
uv pip install torch==2.4.1 torchvision==0.19.1 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: psycopg2 编译报错？

改用预编译版本：

```bash
uv pip install psycopg2-binary==2.9.9
```

然后再安装剩余依赖：`uv pip install -r requirements.txt`

### Q: 想彻底清理旧版本 Python？

```bash
uv python uninstall 3.13    # 卸载 3.13（如果通过 uv 安装的）
```

系统级安装的 Python 需要通过 Windows「设置 → 应用」卸载。



  为什么必须有 Celery？

  文档上传后的处理流程是这样的：

  前端上传文档 → Flask API 接收 → 调用 build_documents.delay() 丢给 Celery 异步队列
                                                      ↓
                                          Celery Worker 异步执行：
                                          parsing（解析）→ splitting（分段）→ indexing（向量化）→ completed

  关键在 document_service.py:100 这行：build_documents.delay(...) — 文档构建是通过 Celery 异步任务执行的。Flask
  只负责接收请求并把任务扔到 Redis 队列，真正干活（解析、分段、向量化、改状态为 completed）的是 Celery Worker。

  没有 Celery Worker 运行 → 队列里的任务没人消费 → 文档永远卡在 waiting 状态。

  解决你的 celery 命令报错

  你需要先进入后端目录并激活虚拟环境：

  cd D:\perfect-project\LLMops\imooc-llmops-api\imooc-llmops-api-master
  .venv\Scripts\Activate.ps1
   celery -A app.http.app.celery worker --loglevel=info --pool=solo

