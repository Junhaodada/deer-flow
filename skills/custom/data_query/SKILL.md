---
name: data_query
description: 查询快消宽表数据，根据条件筛选POI或商圈数据。触发条件：用户需要查询数据库中的售点信息、商圈数据，或需要获取特定条件的POI列表。
---

# 数据查询技能

根据用户需求，从 `fmcg_wide_table.db` SQLite 数据库中查询候选 POI 或商圈数据。

## 支持的查询类型

### 1. 基础POI查询
- 按城市/区域查询售点
- 按渠道类型筛选 (CVS/MT/GT/餐饮等)
- 按连锁品牌筛选
- 按行业筛选 (水饮/啤酒/零食/奶粉/日化/眼镜/调料/白酒)

### 2. 消费场景筛选
- 是否在社区内
- 是否在商场内
- 是否在医院/学校附近
- 是否在写字楼/园区

### 3. 质量筛选
- 售点置信度筛选
- 质量筛选 (高质量/低质量)
- 新增/下线筛选

### 4. 垂直字段查询
- O2O数据 (饿了么/美团/京东到家)
- LINX线下零售数据
- 大众点评餐饮数据
- 酒店数据

## 输入参数

你必须从用户处收集以下信息（如果用户未提供，需要主动询问）：

| 参数 | 说明 | 必填 |
|------|------|------|
| 城市 | 查询的城市 | 是 |
| 区域 | 具体区域/商圈 | 否 |
| 渠道类型 | CVS/MT/GT/餐饮等 | 否 |
| 行业 | 水饮/啤酒/零食等 | 否 |
| 连锁品牌 | 具体品牌名 | 否 |
| 消费场景 | 社区/商场/医院等 | 否 |

## 输出格式

查询完成后，返回结构化数据：

```
【查询结果】

总计: {数量} 条

代表性字段:
- 售点名称: xxx
- 地址: xxx
- 渠道类型: xxx
- 连锁品牌: xxx
- 坐标: (lng, lat)
- 置信度: xxx
- 行业: xxx
- 消费场景: xxx
```

## Tool 调用逻辑

本技能使用内置的 DeerFlow Tool 来查询数据库。Tool 已在 `config.yaml` 中配置。

### 可用 Tools

| Tool 名称 | 说明 | 参数 |
|---------|------|------|
| `query_poi` | 按条件查询售点数据 | city, district, channel, chain, industry, scene, limit |
| `query_trend` | 查询月度趋势数据 | limit |
| `query_channel_stats` | 查询渠道统计数据 | limit |
| `query_chain_stats` | 查询连锁店统计数据 | limit |
| `query_poi_quality` | 查询售点质量分析数据 | limit |
| `query_geo_distribution` | 查询地理分布数据 | limit |
| `execute_sql` | 执行任意SQL查询 | sql, limit |

### 调用示例

```python
# 查询特定城市的售点
query_poi(city="上海市", channel="CVS", limit=50)

# 查询连锁店数据
query_poi(chain="全家", limit=30)

# 按行业和场景查询
query_poi(industry="水饮", scene="社区", limit=100)

# 查询渠道统计
query_channel_stats(limit=50)

# 查询趋势数据
query_trend(limit=12)

# 直接执行SQL
execute_sql(sql="SELECT city, COUNT(*) as cnt FROM tx_poi_information_total GROUP BY city", limit=20)
```

### 参数说明

- **city**: 城市名称，如 "上海市"、"北京市"
- **district**: 区域/区县名称
- **channel**: 渠道类型 (CVS/MT/GT/餐饮)
- **chain**: 连锁品牌名称（支持模糊匹配）
- **industry**: 行业类型
  - 水饮、啤酒、零食、奶粉、日化、眼镜、调料、白酒
- **scene**: 消费场景
  - 社区、商场、医院、写字楼、园区、学校、交通
- **limit**: 返回结果数量限制，默认100

### 返回数据格式

Tool 返回 JSON 格式的数据，需要解析后提取关键字段展示给用户。

### 注意事项

- 如果用户提供的条件无法匹配数据，需要告知用户并建议调整条件
- 优先返回有价值的字段（如置信度、连锁品牌、O2O数据）
- 查询结果条数过多时，可抽样或分页返回
- 使用 Tool 时，确保参数类型正确，特别是 limit 必须是整数
