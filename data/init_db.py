"""生成 SQLite 模拟数据：部门、员工、产品、客户、订单、订单明细"""
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "sample.db"


def init_db():
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE departments (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        manager TEXT,
        budget REAL
    );

    CREATE TABLE employees (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        department_id INTEGER REFERENCES departments(id),
        position TEXT,
        salary REAL,
        hire_date TEXT
    );

    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        price REAL,
        stock INTEGER
    );

    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        city TEXT,
        level TEXT  -- 普通/VIP/SVIP
    );

    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER REFERENCES customers(id),
        order_date TEXT,
        total_amount REAL,
        status TEXT  -- 已完成/已取消/处理中
    );

    CREATE TABLE order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER REFERENCES orders(id),
        product_id INTEGER REFERENCES products(id),
        quantity INTEGER,
        unit_price REAL
    );
    """)

    # 部门
    departments = [
        (1, "技术部", "张伟", 500000),
        (2, "销售部", "李娜", 300000),
        (3, "市场部", "王芳", 200000),
        (4, "人事部", "赵敏", 150000),
        (5, "财务部", "陈强", 180000),
    ]
    c.executemany("INSERT INTO departments VALUES (?,?,?,?)", departments)

    # 员工
    names = ["刘洋", "孙磊", "周杰", "吴敏", "郑浩", "冯雪", "蒋涛", "沈静",
             "韩梅", "杨帆", "朱丽", "胡明", "林峰", "何欢", "罗琳", "谢宇",
             "唐鑫", "许晴", "邓超", "曹颖", "彭磊", "曾慧", "萧然", "田甜",
             "董洁", "袁野", "邹鹏", "潘安", "苏瑶", "卢卡"]
    positions = ["初级工程师", "中级工程师", "高级工程师", "经理", "总监",
                 "销售代表", "销售经理", "市场专员", "HR专员", "财务分析师"]
    employees = []
    for i, name in enumerate(names, 1):
        dept_id = random.randint(1, 5)
        pos = random.choice(positions)
        salary = random.randint(8000, 35000)
        days_ago = random.randint(30, 1800)
        hire_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        employees.append((i, name, dept_id, pos, salary, hire_date))
    c.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?)", employees)

    # 产品
    product_data = [
        ("笔记本电脑Pro", "电子产品", 7999), ("无线鼠标", "电子产品", 129),
        ("机械键盘", "电子产品", 459), ("4K显示器", "电子产品", 2999),
        ("降噪耳机", "电子产品", 1299), ("移动硬盘1TB", "电子产品", 399),
        ("Python编程指南", "图书", 89), ("数据分析实战", "图书", 69),
        ("AI入门教程", "图书", 99), ("项目管理手册", "图书", 59),
        ("办公椅", "办公用品", 899), ("站立式办公桌", "办公用品", 1599),
        ("白板", "办公用品", 199), ("投影仪", "办公用品", 3499),
        ("咖啡机", "生活用品", 599), ("空气净化器", "生活用品", 1299),
        ("台灯", "生活用品", 199), ("保温杯", "生活用品", 89),
        ("双肩背包", "生活用品", 259), ("充电宝", "电子产品", 149),
    ]
    products = []
    for i, (name, cat, price) in enumerate(product_data, 1):
        stock = random.randint(10, 500)
        products.append((i, name, cat, price, stock))
    c.executemany("INSERT INTO products VALUES (?,?,?,?,?)", products)

    # 客户
    cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京"]
    levels = ["普通", "普通", "普通", "VIP", "VIP", "SVIP"]
    customer_names = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十",
                      "郑十一", "冯十二", "陈十三", "褚十四", "卫十五", "蒋十六",
                      "沈十七", "韩十八", "杨十九", "朱二十"]
    customers = []
    for i, name in enumerate(customer_names, 1):
        city = random.choice(cities)
        level = random.choice(levels)
        email = f"user{i}@example.com"
        customers.append((i, name, email, city, level))
    c.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", customers)

    # 订单和订单明细
    statuses = ["已完成", "已完成", "已完成", "已完成", "已取消", "处理中"]
    order_id = 0
    item_id = 0
    for month_offset in range(12):
        num_orders = random.randint(15, 40)
        for _ in range(num_orders):
            order_id += 1
            cust_id = random.randint(1, len(customer_names))
            days_in_month = random.randint(0, 28)
            order_date = (datetime.now() - timedelta(days=30 * month_offset + days_in_month)).strftime("%Y-%m-%d")
            status = random.choice(statuses)

            num_items = random.randint(1, 4)
            total = 0
            items = []
            for _ in range(num_items):
                item_id += 1
                prod_id = random.randint(1, len(product_data))
                qty = random.randint(1, 5)
                price = product_data[prod_id - 1][2]
                total += price * qty
                items.append((item_id, order_id, prod_id, qty, price))

            c.execute("INSERT INTO orders VALUES (?,?,?,?,?)",
                      (order_id, cust_id, order_date, total, status))
            c.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", items)

    conn.commit()

    # 打印统计
    for table in ["departments", "employees", "products", "customers", "orders", "order_items"]:
        count = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} 条记录")

    conn.close()
    print(f"\n数据库已生成: {DB_PATH}")


if __name__ == "__main__":
    init_db()
