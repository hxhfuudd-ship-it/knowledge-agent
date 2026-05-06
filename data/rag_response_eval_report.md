# RAG Response Evaluation Report

## Summary

| Metric | Value |
|---|---|
| Total | 3 |
| Passed | 3 |
| Failed | 0 |
| Citation Hit Rate | 100.0% |
| Avg Faithfulness | 86.9% |
| Avg Coverage | 100.0% |
| Grounded Pass Rate | 100.0% |

## Details

### [PASS] gmv_grounded_answer
- Query: GMV 是怎么计算的？
- Response: GMV = SUM(已完成订单的 total_amount)，只统计已完成订单。citation: business_rules.md#business_rules.md:2:0e633d06768b
- Retrieved Citations: business_rules.md#business_rules.md:2:0e633d06768b, data_dictionary.py#data_dictionary.py:8:d7455ee404cf, business_rules.md#business_rules.md:8:bf506dbbebe7
- Citation Hit: True
- Faithfulness: 75.0%
- Coverage: 100.0%

### [PASS] repurchase_grounded_answer
- Query: 复购率是怎么计算的？
- Response: 复购率 = 有2笔及以上已完成订单的客户数 / 有已完成订单的客户数。citation: business_rules.md#business_rules.md:5:112196688a1f
- Retrieved Citations: business_rules.md#business_rules.md:5:112196688a1f, data_dictionary.py#data_dictionary.py:8:d7455ee404cf, business_rules.md#business_rules.md:4:1e7d326695dc
- Citation Hit: True
- Faithfulness: 100.0%
- Coverage: 100.0%

### [PASS] orders_schema_grounded_answer
- Query: orders 订单表有哪些字段？
- Response: orders 表字段包括 id、customer_id、order_date、total_amount、status。citation: data_dictionary.py#data_dictionary.py:6:e01078a0d0e6
- Retrieved Citations: data_dictionary.py#data_dictionary.py:6:e01078a0d0e6, data_dictionary.py#data_dictionary.py:7:6526820000b0, data_dictionary.py#data_dictionary.py:8:d7455ee404cf
- Citation Hit: True
- Faithfulness: 85.7%
- Coverage: 100.0%
