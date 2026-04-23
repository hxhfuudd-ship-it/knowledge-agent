"""微调训练脚本：使用 LoRA 微调小模型做意图分类

使用前需安装：pip install transformers peft torch datasets

这个脚本展示了 LoRA 微调的完整流程，实际运行需要 GPU 或较长时间。
"""
import json
from pathlib import Path
from typing import List, Dict

FINETUNE_DIR = Path(__file__).parent.parent.parent / "data" / "finetune"


def prepare_dataset(samples: List[Dict]) -> dict:
    """将训练数据转换为 HuggingFace Dataset 格式"""
    texts = []
    labels = []
    label_map = {}

    for s in samples:
        if s.get("task") == "intent_classification":
            texts.append(s["input"])
            label = s["output"]
            if label not in label_map:
                label_map[label] = len(label_map)
            labels.append(label_map[label])

    return {
        "texts": texts,
        "labels": labels,
        "label_map": label_map,
        "num_labels": len(label_map),
    }


def train(data_path: str = None, output_dir: str = None, epochs: int = 3, lr: float = 2e-4):
    """LoRA 微调训练

    参数:
        data_path: JSONL 训练数据路径
        output_dir: 模型输出目录
        epochs: 训练轮数
        lr: 学习率
    """
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
        from peft import LoraConfig, get_peft_model, TaskType
        import torch
    except ImportError:
        print("请先安装依赖: pip install transformers peft torch datasets")
        print("\n以下是训练配置预览：")
        print(f"  数据路径: {data_path}")
        print(f"  输出目录: {output_dir}")
        print(f"  训练轮数: {epochs}")
        print(f"  学习率: {lr}")
        print(f"  方法: LoRA (rank=8, alpha=16)")
        print("\nLoRA 微调的核心思想：")
        print("  - 冻结预训练模型的大部分参数")
        print("  - 只训练低秩分解矩阵 (A, B)")
        print("  - 参数量减少 90%+，训练速度快")
        print("  - 效果接近全量微调")
        return

    if output_dir is None:
        output_dir = str(FINETUNE_DIR / "model")

    # 加载数据
    from .data_prep import DataPrep
    if data_path:
        samples = DataPrep.load_jsonl(data_path)
    else:
        samples = DataPrep.generate_synthetic()

    dataset = prepare_dataset(samples)
    print(f"训练数据: {len(dataset['texts'])} 条, {dataset['num_labels']} 个类别")
    print(f"类别映射: {dataset['label_map']}")

    # 加载模型和分词器
    model_name = "Qwen/Qwen2.5-0.5B"  # 小模型，适合学习
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=dataset["num_labels"],
        trust_remote_code=True,
    )

    # LoRA 配置
    lora_config = LoraConfig(
        task_type=TaskType.SEQ_CLS,
        r=8,              # 低秩维度
        lora_alpha=16,    # 缩放因子
        lora_dropout=0.1,
        target_modules=["q_proj", "v_proj"],  # 只在注意力层的 Q 和 V 上加 LoRA
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # 数据编码
    encodings = tokenizer(dataset["texts"], truncation=True, padding=True, max_length=128, return_tensors="pt")

    class SimpleDataset(torch.utils.data.Dataset):
        def __init__(self, encodings, labels):
            self.encodings = encodings
            self.labels = labels
        def __len__(self):
            return len(self.labels)
        def __getitem__(self, idx):
            item = {k: v[idx] for k, v in self.encodings.items()}
            item["labels"] = torch.tensor(self.labels[idx])
            return item

    train_dataset = SimpleDataset(encodings, dataset["labels"])

    # 训练配置
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=8,
        learning_rate=lr,
        logging_steps=10,
        save_strategy="epoch",
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
    )

    trainer.train()
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # 保存类别映射
    with open(Path(output_dir) / "label_map.json", "w") as f:
        json.dump(dataset["label_map"], f, ensure_ascii=False)

    print(f"\n模型已保存到: {output_dir}")


if __name__ == "__main__":
    train()
