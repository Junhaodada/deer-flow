import json
import sqlite3
from pathlib import Path
from typing import Literal

from langchain.tools import tool


def get_db_connection():
    """Get SQLite connection to FMCG database."""
    db_path = Path(__file__).parent.parent.parent / "data" / "fmcg_wide_table.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


@tool("query_poi", parse_docstring=True, return_direct=True)
def query_poi_tool(
    city: str | None = None,
    district: str | None = None,
    channel: str | None = None,
    chain: str | None = None,
    industry: str | None = None,
    scene: str | None = None,
    limit: int = 100,
) -> str:
    """Query POI (Point of Interest) data from FMCG database.

    Use this tool when the user wants to:
    - Query store/retail location data
    - Find specific retail outlets in a city or district
    - Filter POI data by channel, chain, industry, or scene
    - Get business location recommendations

    Args:
        city: City name (e.g., "上海市", "北京市"). Required for meaningful queries.
        district: District/area name within the city (e.g., "浦东新区", "海淀区").
        channel: Channel type. Options: CVS (convenience store), MT (modern trade), GT (general trade), 餐饮 (restaurant).
        chain: Chain store name for partial matching (e.g., "全家", "罗森", "沃尔玛").
        industry: Industry category. Options: 水饮 (beverage), 啤酒 (beer), 零食 (snacks), 奶粉 (milk powder), 日化 (daily chemicals), 眼镜 (glasses), 调料 (condiments), 白酒 (baijiu).
        scene: Consumption scene. Options: 社区 (residential), 商场 (shopping mall), 医院 (hospital), 写字楼 (office building), 园区 (industrial park), 学校 (school), 交通 (transport hub).
        limit: Maximum number of results to return. Default is 100.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if city:
        conditions.append("city = ?")
        params.append(city)
    if district:
        conditions.append("district = ?")
        params.append(district)
    if channel:
        conditions.append("channel = ?")
        params.append(channel)
    if chain:
        conditions.append("chain LIKE ?")
        params.append(f"%{chain}%")

    industry_field_map = {
        "水饮": "is_yj",
        "啤酒": "is_pj",
        "零食": "is_ls",
        "奶粉": "is_nf",
        "日化": "is_rh",
        "眼镜": "is_yj",
        "调料": "is_tl",
        "白酒": "is_bj",
    }
    if industry and industry in industry_field_map:
        conditions.append(f"{industry_field_map[industry]} = 1")

    scene_field_map = {
        "社区": "is_resident",
        "商场": "is_shoppingmall",
        "医院": "is_hospital",
        "写字楼": "is_office",
        "园区": "is_industrial_park",
        "学校": "is_university",
        "交通": "is_transport",
    }
    if scene and scene in scene_field_map:
        conditions.append(f"{scene_field_map[scene]} = 1")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    sql = f"""
        SELECT 
            id, title, address, lng, lat, province, city, district,
            chain, chain_group, channel, sub_channel,
            poi_quality, retail_general_reliability,
            first_category, second_category, trade
        FROM tx_poi_information_total
        WHERE {where_clause}
        LIMIT ?
    """
    params.append(limit)

    try:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        return json.dumps(result, ensure_ascii=False, default=str)
    except sqlite3.Error as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        conn.close()


@tool("query_channel_stats", parse_docstring=True, return_direct=True)
def query_channel_stats_tool(limit: int = 100) -> str:
    """Query channel statistics from FMCG database.

    Use this tool when the user wants to:
    - Get statistics about different sales channels
    - Understand channel distribution (CVS, MT, GT, etc.)
    - Analyze channel performance metrics

    Args:
        limit: Maximum number of results to return. Default is 100.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM v_channel_stats LIMIT {limit}")
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        return json.dumps(result, ensure_ascii=False, default=str)
    except sqlite3.Error as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        conn.close()


@tool("query_chain_stats", parse_docstring=True, return_direct=True)
def query_chain_stats_tool(limit: int = 100) -> str:
    """Query chain store statistics from FMCG database.

    Use this tool when the user wants to:
    - Get statistics about chain stores
    - Understand chain store distribution
    - Analyze chain store performance

    Args:
        limit: Maximum number of results to return. Default is 100.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM v_chain_stats LIMIT {limit}")
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        return json.dumps(result, ensure_ascii=False, default=str)
    except sqlite3.Error as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        conn.close()


@tool("query_trend", parse_docstring=True, return_direct=True)
def query_trend_tool(limit: int = 100) -> str:
    """Query monthly trend data from FMCG database.

    Use this tool when the user wants to:
    - Get historical trend data
    - Analyze monthly business trends
    - Understand temporal patterns

    Args:
        limit: Maximum number of results to return. Default is 100.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM v_monthly_trend LIMIT {limit}")
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        return json.dumps(result, ensure_ascii=False, default=str)
    except sqlite3.Error as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        conn.close()


@tool("query_geo_distribution", parse_docstring=True, return_direct=True)
def query_geo_distribution_tool(limit: int = 100) -> str:
    """Query geographic distribution data from FMCG database.

    Use this tool when the user wants to:
    - Get geographic distribution of POI
    - Understand regional coverage
    - Analyze location-based patterns

    Args:
        limit: Maximum number of results to return. Default is 100.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM v_geo_distribution LIMIT {limit}")
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        return json.dumps(result, ensure_ascii=False, default=str)
    except sqlite3.Error as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        conn.close()


@tool("query_poi_quality", parse_docstring=True, return_direct=True)
def query_poi_quality_tool(limit: int = 100) -> str:
    """Query POI quality analysis data from FMCG database.

    Use this tool when the user wants to:
    - Get quality metrics for POI data
    - Analyze POI reliability scores
    - Understand data quality patterns

    Args:
        limit: Maximum number of results to return. Default is 100.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM v_poi_quality_analysis LIMIT {limit}")
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        return json.dumps(result, ensure_ascii=False, default=str)
    except sqlite3.Error as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        conn.close()


@tool("execute_sql", parse_docstring=True, return_direct=True)
def execute_sql_tool(sql: str, limit: int = 100) -> str:
    """Execute arbitrary SQL query on FMCG database.

    Use this tool when:
    - You need to run a specific SQL query
    - Built-in query tools don't meet your needs
    - User provides a specific SQL query requirement

    WARNING: Only use for advanced queries. Prefer built-in query tools when possible.

    Args:
        sql: SQL query to execute. Must be a SELECT statement.
        limit: Maximum number of results to return. Default is 100.
    """
    sql = sql.strip()
    if "limit" not in sql.lower():
        sql = f"{sql} LIMIT {limit}"

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        return json.dumps(result, ensure_ascii=False, default=str)
    except sqlite3.Error as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        conn.close()
