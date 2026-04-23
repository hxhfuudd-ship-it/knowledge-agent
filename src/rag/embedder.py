"""Embedding 生成器：支持本地 sentence-transformers 模型和 Voyage API"""
import logging
from typing import List, Optional
from .. import config

logger = logging.getLogger(__name__)

# 推荐的本地模型（按质量排序）
LOCAL_MODELS = {
    "chinese": "shibing624/text2vec-base-chinese",       # 中文专用，效果好
    "multilingual": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # 多语言
    "english": "sentence-transformers/all-MiniLM-L6-v2",  # 英文，速度快
}

DEFAULT_LOCAL_MODEL = "english"

_embedder_cache = {}


def get_embedder(model: Optional[str] = None) -> "Embedder":
    """获取 Embedder 单例（同一 model 参数共享实例，避免重复加载模型）"""
    key = model or config.get("rag.embedding_model", DEFAULT_LOCAL_MODEL)
    if key not in _embedder_cache:
        _embedder_cache[key] = Embedder(model)
    return _embedder_cache[key]


class Embedder:
    """文本 Embedding 生成 - 优先使用本地模型，回退到 API 或哈希向量"""

    def __init__(self, model: Optional[str] = None):
        self._model_name = model or config.get("rag.embedding_model", DEFAULT_LOCAL_MODEL)
        self._local_model = None
        self._backend = None  # "local", "voyage", "hash"

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        self._ensure_initialized()

        if self._backend == "local":
            return self._embed_local(texts)
        elif self._backend == "voyage":
            return self._embed_voyage(texts)
        return self._embed_hash(texts)

    def embed_query(self, query: str) -> List[float]:
        return self.embed_texts([query])[0]

    @property
    def backend(self) -> str:
        self._ensure_initialized()
        return self._backend

    @property
    def model_name(self) -> str:
        self._ensure_initialized()
        return self._model_name

    def _ensure_initialized(self):
        if self._backend is not None:
            return

        # 1. 尝试本地 sentence-transformers
        if self._try_init_local():
            return

        # 2. 尝试 Voyage API
        if self._try_init_voyage():
            return

        # 3. 回退到哈希向量
        self._backend = "hash"
        self._model_name = "hash-fallback"
        logger.warning("Embedding 使用哈希回退模式，检索效果有限。建议安装 sentence-transformers。")

    def _try_init_local(self) -> bool:
        try:
            from sentence_transformers import SentenceTransformer

            if self._model_name and self._model_name not in LOCAL_MODELS:
                model_id = self._model_name
            else:
                key = self._model_name or DEFAULT_LOCAL_MODEL
                model_id = LOCAL_MODELS.get(key, LOCAL_MODELS[DEFAULT_LOCAL_MODEL])

            logger.info("加载本地 Embedding 模型: %s", model_id)
            self._local_model = SentenceTransformer(model_id)
            self._model_name = model_id
            self._backend = "local"
            logger.info("本地 Embedding 模型加载成功 (维度: %d)", self._local_model.get_sentence_embedding_dimension())
            return True
        except ImportError:
            return False
        except Exception as e:
            logger.warning("本地模型加载失败: %s", e)
            return False

    def _try_init_voyage(self) -> bool:
        try:
            import voyageai
            self._voyage_client = voyageai.Client()
            self._model_name = self._model_name or "voyage-3"
            self._backend = "voyage"
            logger.info("使用 Voyage API Embedding: %s", self._model_name)
            return True
        except (ImportError, Exception):
            return False

    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        embeddings = self._local_model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def _embed_voyage(self, texts: List[str]) -> List[List[float]]:
        result = self._voyage_client.embed(texts, model=self._model_name)
        return result.embeddings

    @staticmethod
    def _embed_hash(texts: List[str]) -> List[List[float]]:
        """哈希伪向量（最后的回退方案，无语义能力）"""
        import hashlib
        dim = 384
        embeddings = []
        for text in texts:
            h = hashlib.sha256(text.encode()).hexdigest()
            vec = [(int(h[i % len(h)], 16) - 8) / 8.0 for i in range(dim)]
            norm = sum(v * v for v in vec) ** 0.5
            if norm > 0:
                vec = [v / norm for v in vec]
            embeddings.append(vec)
        return embeddings
