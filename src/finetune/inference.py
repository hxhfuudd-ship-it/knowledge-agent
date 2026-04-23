"""微调模型推理：加载微调后的模型进行意图分类"""
import json
from pathlib import Path
from typing import Optional

FINETUNE_DIR = Path(__file__).parent.parent.parent / "data" / "finetune"


class FineTunedClassifier:
    """加载微调后的意图分类模型"""

    def __init__(self, model_dir: str = None):
        self.model_dir = model_dir or str(FINETUNE_DIR / "model")
        self.model = None
        self.tokenizer = None
        self.label_map = {}
        self.id_to_label = {}

    def load(self) -> bool:
        """加载模型"""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            from peft import PeftModel

            label_path = Path(self.model_dir) / "label_map.json"
            if label_path.exists():
                with open(label_path) as f:
                    self.label_map = json.load(f)
                self.id_to_label = {v: k for k, v in self.label_map.items()}

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir, trust_remote_code=True)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir, trust_remote_code=True)
            return True
        except Exception as e:
            print(f"模型加载失败: {e}")
            return False

    def predict(self, text: str) -> Optional[str]:
        """预测意图类别"""
        if not self.model:
            if not self.load():
                return None

        try:
            import torch
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
            with torch.no_grad():
                outputs = self.model(**inputs)
            predicted_id = outputs.logits.argmax(-1).item()
            return self.id_to_label.get(predicted_id, f"unknown_{predicted_id}")
        except Exception as e:
            return None

    def predict_with_confidence(self, text: str) -> dict:
        """预测并返回置信度"""
        if not self.model:
            if not self.load():
                return {"label": None, "confidence": 0}

        try:
            import torch
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
            with torch.no_grad():
                outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]
            predicted_id = probs.argmax().item()
            confidence = probs[predicted_id].item()

            return {
                "label": self.id_to_label.get(predicted_id, f"unknown_{predicted_id}"),
                "confidence": round(confidence, 4),
                "all_scores": {
                    self.id_to_label.get(i, f"class_{i}"): round(p.item(), 4)
                    for i, p in enumerate(probs)
                },
            }
        except Exception as e:
            return {"label": None, "confidence": 0, "error": str(e)}
