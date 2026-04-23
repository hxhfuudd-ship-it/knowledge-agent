"""知识库文档：数据字典 - 描述数据库表结构和业务含义"""

# 数据字典
DATABASE_SCHEMA = """
## 数据库表结构说明

### departments（部门表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 部门ID，主键 |
| name | TEXT | 部门名称（技术部/销售部/市场部/人事部/财务部） |
| manager | TEXT | 部门经理姓名 |
| budget | REAL | 年度预算（元） |

### employees（员工表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 员工ID，主键 |
| name | TEXT | 员工姓名 |
| department_id | INTEGER | 所属部门ID，外键关联 departments.id |
| position | TEXT | 职位（初级工程师/中级工程师/高级工程师/经理/总监等） |
| salary | REAL | 月薪（元） |
| hire_date | TEXT | 入职日期，格式 YYYY-MM-DD |

### products（产品表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 产品ID，主键 |
| name | TEXT | 产品名称 |
| category | TEXT | 产品分类（电子产品/图书/办公用品/生活用品） |
| price | REAL | 单价（元） |
| stock | INTEGER | 当前库存数量 |

### customers（客户表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 客户ID，主键 |
| name | TEXT | 客户姓名 |
| email | TEXT | 邮箱地址 |
| city | TEXT | 所在城市 |
| level | TEXT | 客户等级（普通/VIP/SVIP），VIP为年消费>5000，SVIP为年消费>20000 |

### orders（订单表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 订单ID，主键 |
| customer_id | INTEGER | 客户ID，外键关联 customers.id |
| order_date | TEXT | 下单日期，格式 YYYY-MM-DD |
| total_amount | REAL | 订单总金额（元） |
| status | TEXT | 订单状态（已完成/已取消/处理中） |

### order_items（订单明细表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 明细ID，主键 |
| order_id | INTEGER | 订单ID，外键关联 orders.id |
| product_id | INTEGER | 产品ID，外键关联 products.id |
| quantity | INTEGER | 购买数量 |
| unit_price | REAL | 成交单价（元） |

## 常用业务指标

- **GMV（成交总额）**：所有已完成订单的 total_amount 之和
- **客单价**：GMV / 已完成订单数
- **退单率**：已取消订单数 / 总订单数
- **复购率**：有2笔及以上已完成订单的客户数 / 总客户数
- **库存周转**：一段时间内售出数量 / 平均库存

## 常用 SQL 示例

-- 查询各部门平均薪资
SELECT d.name, AVG(e.salary) as avg_salary
FROM employees e JOIN departments d ON e.department_id = d.id
GROUP BY d.name ORDER BY avg_salary DESC;

-- 查询月度销售趋势
SELECT strftime('%Y-%m', order_date) as month, SUM(total_amount) as revenue
FROM orders WHERE status = '已完成'
GROUP BY month ORDER BY month;

-- 查询热销产品 TOP10
SELECT p.name, SUM(oi.quantity) as total_sold, SUM(oi.quantity * oi.unit_price) as revenue
FROM order_items oi JOIN products p ON oi.product_id = p.id
JOIN orders o ON oi.order_id = o.id WHERE o.status = '已完成'
GROUP BY p.id ORDER BY total_sold DESC LIMIT 10;

-- 查询各城市客户消费排名
SELECT c.city, COUNT(DISTINCT c.id) as customers, SUM(o.total_amount) as total_spend
FROM customers c JOIN orders o ON c.id = o.customer_id WHERE o.status = '已完成'
GROUP BY c.city ORDER BY total_spend DESC;
"""
