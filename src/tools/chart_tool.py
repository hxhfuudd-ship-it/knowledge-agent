"""数据可视化工具：生成图表并保存为图片"""
import json
import logging
from pathlib import Path
from .base import Tool

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "charts"


class ChartTool(Tool):
    name = "create_chart"
    description = (
        "根据数据生成图表（柱状图、折线图、饼图等），保存为 PNG 文件。\n"
        "传入 chart_type、title、data（JSON 格式的 labels 和 values）。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "chart_type": {
                "type": "string",
                "description": "图表类型：bar（柱状图）、line（折线图）、pie（饼图）",
                "enum": ["bar", "line", "pie"],
            },
            "title": {
                "type": "string",
                "description": "图表标题",
            },
            "data": {
                "type": "object",
                "description": "图表数据，包含 labels（标签列表）和 values（数值列表）",
                "properties": {
                    "labels": {"type": "array", "items": {"type": "string"}},
                    "values": {"type": "array", "items": {"type": "number"}},
                },
                "required": ["labels", "values"],
            },
        },
        "required": ["chart_type", "title", "data"],
    }

    def execute(self, chart_type: str, title: str, data: dict) -> str:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            return "错误：需要安装 matplotlib（pip install matplotlib）"

        labels = data.get("labels", [])
        values = data.get("values", [])
        if not labels or not values or len(labels) != len(values):
            return "错误：labels 和 values 长度必须一致且不为空"

        plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

        fig, ax = plt.subplots(figsize=(8, 5))

        if chart_type == "bar":
            ax.bar(labels, values, color="#4A90D9")
        elif chart_type == "line":
            ax.plot(labels, values, marker="o", color="#4A90D9", linewidth=2)
        elif chart_type == "pie":
            ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
            ax.axis("equal")
        else:
            return "错误：不支持的图表类型 %s" % chart_type

        ax.set_title(title, fontsize=14)
        if chart_type != "pie":
            ax.tick_params(axis="x", rotation=30)
        fig.tight_layout()

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:40]
        filepath = OUTPUT_DIR / ("%s.png" % safe_title)
        fig.savefig(filepath, dpi=120)
        plt.close(fig)

        logger.info("图表已保存: %s", filepath)
        return "图表已生成: %s" % filepath
