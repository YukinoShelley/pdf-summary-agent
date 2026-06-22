# Experiment 2: "Bring Your Own Agent" — 实验报告

> **课程：** The Modern Software Developer (Week 13-15)
>
> **姓名/学号：** 张军 / 2024212532
>
> **日期：** 2026/06/22

---

## 1. 项目概述

本项目实现了一个 **PDF 总结助手 (PDF Summary Assistant)** —— 一个单用途 AI Agent，能够自动读取、分析和总结 PDF 文档。用户只需输入文件路径和总结需求，Agent 就会自主调用工具链完成内容提取、关键信息检索和报告生成。

**核心功能：** 用户输入 "Summarize the file report.pdf" 后，Agent 自动：
1. 查询 PDF 元数据（页数、大小）
2. 逐页读取或批量读取文档内容
3. 搜索关键术语定位重要章节
4. 合成并输出结构化总结

---

## 2. 系统架构

### 2.1 架构图

```
+------------------+     Function Calling      +------------------+
|                  |  (类比 MCP 协议)           |                  |
|  LLM (DeepSeek) | <------------------------> |  Tool Layer      |
|                  |     tools/list             |                  |
|  决定调用什么工具 |     tool_call JSON-RPC    | +-- read_pdf     |
|  合成最终总结    |                            | +-- search_pdf   |
+------------------+                            | +-- get_pdf_info |
       |                                        | +-- list_pdfs    |
       |  System Prompt (角色定义)               +------------------+
       v                                                |
+------------------+                                    |
|   PDF 文件       | <--- pypdf library ----------------+
+------------------+
```

### 2.2 Tool Use / Skills（实验核心要求）

Agent 配备了 **4 个独立的外部工具**（要求 >= 2 个）：

| 工具名 | 功能 | 为什么不只是 LLM 知识？ |
|--------|------|------------------------|
| **read_pdf** | 提取 PDF 指定页面的文本内容 | LLM 无法直接读取本地文件，需工具桥接 |
| **search_pdf** | 在 PDF 中搜索关键词并返回上下文 | 依赖实际文件内容，非模型训练数据 |
| **get_pdf_info** | 获取页数、大小、作者等元数据 | 读取文件系统真实信息 |
| **list_pdf_files** | 扫描目录列出所有 PDF | 依赖文件系统遍历 |

所有工具都通过 **pypdf** 库与本地文件系统交互，LLM 无法单凭自身知识完成这些操作。

### 2.3 Context Integration（类比 MCP 协议）

使用 **DeepSeek Chat API（兼容 OpenAI 格式）的 Function Calling** 实现工具调用协议，其工作流程与 MCP (Model Context Protocol) 高度一致：

| MCP 概念 | 本项目的对应实现 |
|----------|-----------------|
| MCP Server | `tools.py` 中的 `TOOL_SCHEMAS` + `TOOL_DISPATCH` |
| tools/list | `TOOL_SCHEMAS` 定义的 JSON Schema 列表 |
| tool_call | LLM 返回的 `tool_calls` 指令（JSON-RPC 风格） |
| 执行与回传 | `agent.py` 中 dispatch → 执行 → 结果注入上下文 |

示例工具 Schema 定义（类比 MCP 的 tool 描述）：

```python
{
    "type": "function",
    "function": {
        "name": "read_pdf",
        "description": "Read and extract text content from a PDF file.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "page_start": {"type": "integer"}
            },
            "required": ["file_path"]
        }
    }
}
```

### 2.4 Agent 主循环

```
[User] "Summarize chapter3.pdf"
   |
   v
[LLM] 分析请求 -> 决定先调用 get_pdf_info
   |
   v
[Tool] get_pdf_info("chapter3.pdf") -> "20 pages, 500KB"
   |
   v
[LLM] 文件较长，决定分块读取 (pages 1-10, pages 11-20)
   |
   v
[Tool] read_pdf("chapter3.pdf", 1, 10) -> 文本内容
[Tool] read_pdf("chapter3.pdf", 11, 20) -> 文本内容
   |
   v
[LLM] 综合所有内容，生成结构化总结
   |
   v
[User] 收到总结报告
```

---

## 3. 运行截图

> *请在运行 `python main.py` 后，截取以下 3-4 张截图插入此处：*

### 截图 1: Agent 启动与 PDF 信息查询

```
在终端中运行：
  python main.py "Tell me about the file sample_ai.pdf"

截图应展示：
- Agent 调用 get_pdf_info 获取文档元数据
- 输出文档页数、大小等信息
```

**[在此插入截图 1]**

### 截图 2: 读取 PDF 内容

```
Agent 调用 read_pdf 工具读取文档内容
显示正在读取的页码范围
```

**[在此插入截图 2]**

### 截图 3: 生成的结构化总结

```
Agent 合成最终总结输出
展示标题、关键点、结构化格式
```

**[在此插入截图 3]**

### 截图 4: 搜索功能演示

```
运行：python main.py "Search for 'Deep Learning' in sample_ai.pdf"
Agent 调用 search_pdf 工具
展示搜索结果与上下文（关键词所在页码+周围文本）
```

**[在此插入截图 4]**

---

## 4. 技术反思 (Reflection)

### 4.1 技术难点：从 OpenAI API 迁移到 DeepSeek 的兼容性适配

在开发过程中，遇到的核心技术难点是 **LLM 后端从 OpenAI 切换到 DeepSeek 时的 API 兼容性问题**。

**问题描述：**
项目最初基于 OpenAI 的 GPT-4o-mini 开发，DeepSeek 虽然宣称"兼容 OpenAI API 格式"，但在实际使用中发现以下差异：

1. **模型命名差异：** DeepSeek 的对话模型名称为 `deepseek-chat`（对应 DeepSeek-V3），而非 `gpt-*` 系列。最初用 `gpt-4o-mini` 去请求 DeepSeek 的 API 端点会直接返回 404 错误。

2. **Base URL 格式：** DeepSeek 的 API 端点是 `https://api.deepseek.com/v1`，而 OpenAI 是 `https://api.openai.com/v1`。最初硬编码了 OpenAI 的地址，导致所有请求都发错地方。

3. **Function Calling 行为差异：** DeepSeek 的 `deepseek-chat` 模型对 function calling 的支持与 GPT-4 系列存在细微差别——当同时发送多条 tool 调用结果回传时，DeepSeek 模型有时会忽略部分上下文，导致总结不完整。

**解决过程：**
1. 将配置从硬编码改为环境变量驱动：引入 `API_BASE_URL` 和 `LLM_MODEL` 变量
2. 设置默认值指向 DeepSeek：`https://api.deepseek.com/v1` + `deepseek-chat`
3. 将环境变量前缀从 `OPENAI_*` 改为通用名称（兼容 `API_KEY` 和 `OPENAI_API_KEY` 两种写法），方便未来切换到其他提供商
4. 实测发现 DeepSeek 处理多轮 tool call 时效果良好，无需额外调整

### 4.2 经验总结

这次经历让我深刻体会到 **"API 兼容"不意味着 "100% 相同"**。许多号称兼容 OpenAI 格式的 API 服务在边缘行为和模型能力上仍有差异。关键收获：

- **配置与代码分离是架构设计的基本原则**——将 API 地址、模型名等参数抽离为环境变量，切换后端只需改 `.env`，不用改代码
- **验证 > 信任**——AI 生成的代码中 API 端点往往是基于训练数据的"猜测"，必须对照当前服务商的文档逐一确认
- **渐进式迁移策略**——先在一个工具上验证兼容性，再全量切换，而不是一次性全部迁移

这个小插曲印证了课程的核心观点：**AI 工具虽强，但开发者仍需理解底层技术原理，才能诊断和解决集成过程中的问题。**

---

## 5. 代码仓库

- **项目路径:** `C:\Users\jun\Desktop\pdf-summary-agent\`
- **关键文件:**
  - `main.py` — 入口文件
  - `pdf_summary_agent/tools.py` — 工具定义与实现
  - `pdf_summary_agent/agent.py` — Agent 工作循环
  - `pdf_summary_agent/config.py` — 配置管理
  - `requirements.txt` — 依赖清单
- **依赖:** `openai`, `python-dotenv`, `pypdf`

---

*报告结束*
