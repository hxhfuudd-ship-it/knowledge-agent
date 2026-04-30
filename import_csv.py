"""手动导入 CSV 到 SQLite 数据库（支持单文件和文件夹批量导入）"""
import sys
import argparse
import sqlite3
from pathlib import Path

from src.path_utils import is_sql_identifier, normalize_project_name, table_name_from_filename

PROJECT_ROOT = Path(__file__).parent


def _get_db_path(project=None):
    import yaml
    config_path = PROJECT_ROOT / "config" / "settings.yaml"
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if project:
        return PROJECT_ROOT / "data" / "databases" / ("%s.db" % normalize_project_name(project))
    return PROJECT_ROOT / cfg.get("database", {}).get("path", "data/databases/default.db")


def import_csv(csv_path: str, table_name: str, if_exists: str = "replace", project: str = None):
    import pandas as pd

    csv_file = Path(csv_path)
    if not csv_file.exists():
        print("文件不存在: %s" % csv_path)
        return False
    if not is_sql_identifier(table_name):
        print("非法表名: %s（只允许字母、数字和下划线，且不能以数字开头）" % table_name)
        return False

    db_path = _get_db_path(project)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(str(csv_file))
    print("读取 %s: %d 行, %d 列" % (csv_file.name, len(df), len(df.columns)))

    with sqlite3.connect(str(db_path)) as conn:
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)

    print("  → 表名: %s, 项目: %s, 模式: %s" % (table_name, db_path.stem, if_exists))
    return True


def import_folder(folder_path: str, if_exists: str = "replace", project: str = None):
    folder = Path(folder_path)
    if not folder.is_dir():
        print("文件夹不存在: %s" % folder_path)
        sys.exit(1)

    csv_files = sorted(folder.glob("*.csv"))
    if not csv_files:
        print("文件夹中没有 CSV 文件")
        sys.exit(1)

    print("找到 %d 个 CSV 文件\n" % len(csv_files))
    success = 0
    for f in csv_files:
        table_name = table_name_from_filename(f.name)
        if import_csv(str(f), table_name, if_exists, project):
            success += 1
        print()

    print("完成：%d/%d 个文件导入成功" % (success, len(csv_files)))


if __name__ == "__main__":
    try:
        import pandas  # noqa: F401
    except ImportError:
        print("需要安装 pandas: pip install pandas")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="导入 CSV 到 SQLite（支持单文件或文件夹）")
    parser.add_argument("path", nargs="?", help="CSV 文件路径或包含 CSV 的文件夹路径")
    parser.add_argument("--table", help="目标表名（仅单文件时有效，文件夹模式自动用文件名）")
    parser.add_argument("--mode", choices=["replace", "append"], default="replace",
                        help="表已存在时的处理方式（默认 replace）")
    parser.add_argument("--project", help="目标项目名（对应 data/databases/<name>.db，默认 default）")
    parser.add_argument("--list", action="store_true", help="列出所有项目")
    args = parser.parse_args()

    if args.list:
        db_dir = PROJECT_ROOT / "data" / "databases"
        dbs = sorted(db_dir.glob("*.db")) if db_dir.exists() else []
        if not dbs:
            print("暂无项目")
        else:
            print("项目列表：")
            for db in dbs:
                size = db.stat().st_size / 1024
                print("  - %s (%.1f KB)" % (db.stem, size))
        sys.exit(0)

    if not args.path:
        parser.print_help()
        sys.exit(1)

    p = Path(args.path)
    if p.is_dir():
        import_folder(args.path, args.mode, args.project)
    elif p.is_file():
        table_name = args.table or table_name_from_filename(p.name)
        import_csv(args.path, table_name, args.mode, args.project)
    else:
        print("路径不存在: %s" % args.path)
        sys.exit(1)
