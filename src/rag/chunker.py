"""文本切片器：将长文档切分为适合 Embedding 的小块"""
import re
from typing import List
from .loader import Document


class TextChunker:
    """文本切片 - 支持多种切片策略"""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, documents: List[Document], strategy: str = "recursive") -> List[Document]:
        strategies = {
            "fixed": self._fixed_chunk,
            "recursive": self._recursive_chunk,
            "semantic": self._semantic_chunk,
        }
        fn = strategies.get(strategy, self._recursive_chunk)
        chunks = []
        for doc in documents:
            chunks.extend(fn(doc))
        return chunks

    def _fixed_chunk(self, doc: Document) -> List[Document]:
        """固定大小切片，带重叠"""
        text = doc.content
        chunks = []
        start = 0
        idx = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            if chunk_text.strip():
                meta = {**doc.metadata, "chunk_index": idx, "chunk_strategy": "fixed"}
                chunks.append(Document(content=chunk_text, metadata=meta))
                idx += 1
            start = end - self.chunk_overlap
        return chunks

    def _recursive_chunk(self, doc: Document) -> List[Document]:
        """递归切片：按分隔符层级切分（段落 → 句子 → 固定大小）"""
        separators = ["\n\n", "\n", "。", ".", "！", "!", "？", "?", "；", ";", " "]
        return self._split_recursive(doc.content, separators, doc.metadata)

    def _split_recursive(self, text: str, separators: List[str], metadata: dict) -> List[Document]:
        if len(text) <= self.chunk_size:
            if text.strip():
                return [Document(content=text.strip(), metadata={**metadata, "chunk_strategy": "recursive"})]
            return []

        sep = separators[0] if separators else ""
        remaining_seps = separators[1:] if len(separators) > 1 else []

        if sep:
            parts = text.split(sep)
        else:
            return self._fixed_chunk(Document(content=text, metadata=metadata))

        chunks = []
        current = ""
        idx = 0
        for part in parts:
            candidate = current + sep + part if current else part
            if len(candidate) > self.chunk_size and current:
                if len(current) > self.chunk_size and remaining_seps:
                    chunks.extend(self._split_recursive(current, remaining_seps, {**metadata, "chunk_index": idx}))
                elif current.strip():
                    chunks.append(Document(
                        content=current.strip(),
                        metadata={**metadata, "chunk_index": idx, "chunk_strategy": "recursive"},
                    ))
                idx += 1
                current = part
            else:
                current = candidate

        if current.strip():
            if len(current) > self.chunk_size and remaining_seps:
                chunks.extend(self._split_recursive(current, remaining_seps, {**metadata, "chunk_index": idx}))
            else:
                chunks.append(Document(
                    content=current.strip(),
                    metadata={**metadata, "chunk_index": idx, "chunk_strategy": "recursive"},
                ))

        return chunks

    def _semantic_chunk(self, doc: Document) -> List[Document]:
        """语义切片：按 Markdown 标题或段落分割"""
        sections = re.split(r"(^#{1,3}\s+.+$)", doc.content, flags=re.MULTILINE)

        chunks = []
        current_heading = ""
        current_text = ""
        idx = 0

        for section in sections:
            if re.match(r"^#{1,3}\s+", section):
                if current_text.strip():
                    text = (current_heading + "\n" + current_text).strip()
                    for sub_chunk in self._ensure_size(text, idx, doc.metadata):
                        chunks.append(sub_chunk)
                        idx += 1
                current_heading = section.strip()
                current_text = ""
            else:
                current_text += section

        if current_text.strip():
            text = (current_heading + "\n" + current_text).strip()
            for sub_chunk in self._ensure_size(text, idx, doc.metadata):
                chunks.append(sub_chunk)

        return chunks if chunks else self._recursive_chunk(doc)

    def _ensure_size(self, text: str, idx: int, metadata: dict) -> List[Document]:
        if len(text) <= self.chunk_size:
            return [Document(
                content=text,
                metadata={**metadata, "chunk_index": idx, "chunk_strategy": "semantic"},
            )]
        return self._fixed_chunk(Document(content=text, metadata=metadata))
