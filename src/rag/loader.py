"""文档加载器：支持 PDF、Markdown、TXT、HTML 文件解析"""
import re
import logging
from pathlib import Path
from typing import List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """文档对象"""
    content: str
    metadata: dict

    def __repr__(self):
        src = self.metadata.get("source", "unknown")
        return "Document(source=%s, len=%d)" % (src, len(self.content))


class DocumentLoader:
    """统一文档加载入口"""

    SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".html", ".py"}

    def load(self, path: str) -> List[Document]:
        p = Path(path)
        if p.is_dir():
            return self._load_directory(p)
        return self._load_file(p)

    def _load_directory(self, dir_path: Path) -> List[Document]:
        docs = []
        for f in sorted(dir_path.iterdir()):
            if f.is_file() and f.suffix in self.SUPPORTED_SUFFIXES:
                try:
                    docs.extend(self._load_file(f))
                except Exception as e:
                    logger.warning("加载文件失败 %s: %s", f.name, e)
        return docs

    def _load_file(self, file_path: Path) -> List[Document]:
        suffix = file_path.suffix.lower()
        metadata = {"source": str(file_path), "filename": file_path.name}

        if suffix == ".pdf":
            return self._load_pdf(file_path, metadata)
        elif suffix in (".md", ".txt", ".py"):
            return self._load_text(file_path, metadata)
        elif suffix == ".html":
            return self._load_html(file_path, metadata)
        return []

    def _load_text(self, path: Path, metadata: dict) -> List[Document]:
        text = path.read_text(encoding="utf-8")
        return [Document(content=text, metadata=metadata)]

    def _load_pdf(self, path: Path, metadata: dict) -> List[Document]:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(path))
            docs = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    page_meta = {**metadata, "page": i + 1}
                    docs.append(Document(content=text, metadata=page_meta))
            return docs
        except ImportError:
            logger.warning("PyPDF2 未安装，无法读取 PDF")
            return []

    def _load_html(self, path: Path, metadata: dict) -> List[Document]:
        html = path.read_text(encoding="utf-8")
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        return [Document(content=text, metadata=metadata)]
