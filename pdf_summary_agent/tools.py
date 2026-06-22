"""
Tool implementations for the PDF Summary Agent.

Provides external capabilities the LLM can invoke:
  - read_pdf:      Extract text from PDF pages
  - search_pdf:    Search for keywords in a PDF
  - get_pdf_info:  Get PDF metadata (pages, file size, etc.)
"""

import os
from pathlib import Path
from typing import Optional

from pypdf import PdfReader


def read_pdf(file_path: str, page_start: Optional[int] = None,
             page_end: Optional[int] = None) -> str:
    """Extract text from a PDF file."""
    path = Path(file_path)
    if not path.exists():
        return f"[Error] File not found: {file_path}"
    if path.suffix.lower() != ".pdf":
        return f"[Error] Not a PDF file: {file_path}"

    reader = PdfReader(str(path))
    total = len(reader.pages)
    start = page_start if page_start is not None else 1
    end = page_end if page_end is not None else total

    if start < 1 or end > total or start > end:
        return f"[Error] Invalid range [{start}-{end}]. Document has {total} pages."

    parts = []
    for i in range(start - 1, end):
        page = reader.pages[i]
        text = page.extract_text()
        if text:
            parts.append(f"--- Page {i+1} ---\n{text.strip()}")

    result = "\n\n".join(parts)
    return (f"Document: {path.name} (pages {start}-{end} of {total}, "
            f"~{len(result)} chars)\n\n{result}")


def search_pdf(file_path: str, keyword: str, max_chars: int = 300) -> str:
    """Search for a keyword within a PDF file."""
    path = Path(file_path)
    if not path.exists():
        return f"[Error] File not found: {file_path}"
    if path.suffix.lower() != ".pdf":
        return f"[Error] Not a PDF file: {file_path}"

    reader = PdfReader(str(path))
    total = len(reader.pages)
    found_pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if keyword.lower() in text.lower():
            idx = text.lower().find(keyword.lower())
            start = max(0, idx - 40)
            end = min(len(text), idx + max_chars)
            context = text[start:end].replace("\n", " ").strip()
            found_pages.append((i + 1, context))

    if not found_pages:
        return f"[Search] No matches for '{keyword}' in {path.name} ({total} pages)."

    lines = [f"[Search] Found '{keyword}' on {len(found_pages)} page(s):"]
    for pnum, ctx in found_pages:
        lines.append(f"\nPage {pnum}:\n  ...{ctx}...")
    return "\n".join(lines)


def get_pdf_info(file_path: str) -> str:
    """Get metadata and overview of a PDF file."""
    path = Path(file_path)
    if not path.exists():
        return f"[Error] File not found: {file_path}"
    if path.suffix.lower() != ".pdf":
        return f"[Error] Not a PDF file: {file_path}"

    reader = PdfReader(str(path))
    total = len(reader.pages)
    size_kb = os.path.getsize(path) / 1024
    meta = reader.metadata or {}

    first_page_text = ""
    if total > 0:
        raw = reader.pages[0].extract_text()
        first_page_text = raw.strip()[:300].replace("\n", " ") if raw else "(empty)"

    info = [
        f"PDF Info: {path.name}",
        f"  Pages:      {total}",
        f"  File size:  {size_kb:.1f} KB",
        f"  Title:      {meta.get('/Title', '(none)')}",
        f"  Author:     {meta.get('/Author', '(none)')}",
        f"  First page:  {first_page_text}...",
    ]
    return "\n".join(info)


def list_pdf_files(directory: str = ".") -> str:
    """List all PDF files in a directory."""
    path = Path(directory)
    if not path.is_dir():
        return f"[Error] Directory not found: {directory}"

    pdfs = sorted(path.glob("*.pdf"))
    if not pdfs:
        return f"[List] No PDF files found in {path.resolve()}"

    lines = [f"PDF files in {path.resolve()}:", ""]
    for p in pdfs:
        try:
            reader = PdfReader(str(p))
            pages = len(reader.pages)
            size = os.path.getsize(p) / 1024
            lines.append(f"  * {p.name}  ({pages} pages, {size:.1f} KB)")
        except Exception:
            lines.append(f"  * {p.name}  (could not read)")
    return "\n".join(lines)


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_pdf",
            "description": "读取 PDF 文件并提取其中的文本内容。用于获取文档全文以便总结。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "PDF 文件路径"},
                    "page_start": {"type": "integer", "description": "起始页码（从1开始）。默认：1"},
                    "page_end": {"type": "integer", "description": "结束页码（包含）。默认：最后一页"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_pdf",
            "description": "在 PDF 中搜索关键词，返回匹配位置和上下文内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "PDF 文件路径"},
                    "keyword": {"type": "string", "description": "要搜索的关键词（不区分大小写）"},
                    "max_chars": {"type": "integer", "description": "每个匹配项返回的上下文字符数。默认：300"}
                },
                "required": ["file_path", "keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pdf_info",
            "description": "获取 PDF 元数据：页数、文件大小、标题、作者等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "PDF 文件路径"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_pdf_files",
            "description": "列出目录中的所有 PDF 文件，附带页数和大小信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "要扫描的目录。默认：当前目录"}
                },
                "required": []
            }
        }
    }
]

TOOL_DISPATCH = {
    "read_pdf": lambda **kw: read_pdf(**kw),
    "search_pdf": lambda **kw: search_pdf(**kw),
    "get_pdf_info": lambda **kw: get_pdf_info(**kw),
    "list_pdf_files": lambda **kw: list_pdf_files(**kw),
}
