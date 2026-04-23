"""Skill 基类：高级能力 = Tool 组合 + 专用 Prompt + 执行流程"""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class Skill(ABC):
    """Skill 基类 - 比 Tool 更高级的能力单元

    Tool 是原子操作（查SQL、读文件），Skill 是组合能力（数据分析、报告生成）
    """

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """该 Skill 的专用系统提示词"""
        ...

    @property
    def required_tools(self) -> List[str]:
        """该 Skill 需要的工具列表"""
        return []

    @property
    def output_format(self) -> Optional[str]:
        """输出格式模板"""
        return None

    @abstractmethod
    def build_prompt(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """根据用户输入构建完整的 Prompt"""
        ...

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "required_tools": self.required_tools,
        }


class SkillRegistry:
    """Skill 注册中心 - 支持关键词匹配和语义匹配两种路由策略"""

    def __init__(self, match_strategy: str = "keyword"):
        """
        match_strategy:
          - "keyword": 关键词匹配（快，无依赖）
          - "embedding": Embedding 语义匹配（准，需要 sentence-transformers）
          - "hybrid": 关键词优先，无命中时回退到语义匹配
        """
        self._skills: Dict[str, Skill] = {}
        self._strategy = match_strategy
        self._embedder = None
        self._skill_embeddings: Dict[str, List[float]] = {}
        self._similarity_threshold = 0.35

    def register(self, skill: Skill):
        self._skills[skill.name] = skill
        self._skill_embeddings.pop(skill.name, None)

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_skills(self) -> List[Skill]:
        return list(self._skills.values())

    def match(self, user_input: str) -> Optional[Skill]:
        """根据策略匹配最合适的 Skill"""
        if self._strategy == "keyword":
            return self._match_keyword(user_input)
        elif self._strategy == "embedding":
            return self._match_embedding(user_input)
        elif self._strategy == "hybrid":
            result = self._match_keyword(user_input)
            if result:
                return result
            return self._match_embedding(user_input)
        return self._match_keyword(user_input)

    def match_with_scores(self, user_input: str) -> List[Dict]:
        """返回所有 Skill 的匹配分数（用于调试和对比）"""
        scores = []

        kw_match = self._match_keyword(user_input)
        emb_scores = self._compute_embedding_scores(user_input)

        for skill in self._skills.values():
            scores.append({
                "skill": skill.name,
                "keyword_match": skill.name == kw_match.name if kw_match else False,
                "embedding_score": emb_scores.get(skill.name, 0.0),
            })

        scores.sort(key=lambda x: x["embedding_score"], reverse=True)
        return scores

    def _match_keyword(self, user_input: str) -> Optional[Skill]:
        for skill in self._skills.values():
            keywords = getattr(skill, "keywords", [])
            for kw in keywords:
                if kw in user_input:
                    return skill
        return None

    def _match_embedding(self, user_input: str) -> Optional[Skill]:
        scores = self._compute_embedding_scores(user_input)
        if not scores:
            return None

        best_name = max(scores, key=scores.get)
        if scores[best_name] >= self._similarity_threshold:
            logger.info(
                "语义匹配 Skill: %s (score=%.3f)", best_name, scores[best_name]
            )
            return self._skills[best_name]
        return None

    def _compute_embedding_scores(self, user_input: str) -> Dict[str, float]:
        if not self._skills:
            return {}

        embedder = self._get_embedder()
        if not embedder:
            return {}

        self._ensure_skill_embeddings(embedder)

        query_vec = embedder.embed_query(user_input)
        scores = {}
        for name, skill_vec in self._skill_embeddings.items():
            scores[name] = self._cosine_similarity(query_vec, skill_vec)
        return scores

    def _ensure_skill_embeddings(self, embedder):
        missing = [s for s in self._skills if s not in self._skill_embeddings]
        if not missing:
            return

        texts = []
        for name in missing:
            skill = self._skills[name]
            kws = " ".join(getattr(skill, "keywords", []))
            texts.append("%s %s %s" % (skill.name, skill.description, kws))

        vecs = embedder.embed_texts(texts)
        for name, vec in zip(missing, vecs):
            self._skill_embeddings[name] = vec

    def _get_embedder(self):
        if self._embedder is not None:
            return self._embedder
        try:
            from ..rag.embedder import get_embedder
            self._embedder = get_embedder()
            return self._embedder
        except Exception as e:
            logger.warning("Embedding 不可用，语义匹配降级: %s", e)
            return None

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
