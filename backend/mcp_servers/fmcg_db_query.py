#!/usr/bin/env python3
"""FMCG Database Query MCP Server.

This MCP server provides tools for querying the FMCG wide table SQLite database.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(db_path: str, sql: str, limit: int = 100) -> list[dict]:
    """Execute a SQL query and return results as list of dicts."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Add LIMIT if not present
    sql = sql.strip()
    if "limit" not in sql.lower():
        sql = f"{sql} LIMIT {limit}"
    
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        return [{"error": str(e)}]
    finally:
        conn.close()


def get_table_schema(db_path: str, table_name: str = "tx_poi_information_total") -> list[dict]:
    """Get the schema for a table."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall()
        return [{"cid": r[0], "name": r[1], "type": r[2], "notnull": r[3], "dflt_value": r[4], "pk": r[5]} for r in rows]
    except sqlite3.Error as e:
        return [{"error": str(e)}]
    finally:
        conn.close()


def get_table_list(db_path: str) -> list[str]:
    """Get list of tables in the database."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        return [f"error: {str(e)}"]
    finally:
        conn.close()


def get_poi_by_conditions(
    db_path: str,
    city: str | None = None,
    district: str | None = None,
    channel: str | None = None,
    chain: str | None = None,
    industry: str | None = None,
    scene: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Query POI data by various conditions."""
    conn = get_db_connection(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Build WHERE clause
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
    
    # Industry field mapping
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
    
    # Scene field mapping
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
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        return [{"error": str(e)}]
    finally:
        conn.close()


def get_trend_data(db_path: str, table_name: str = "v_monthly_trend", limit: int = 100) -> list[dict]:
    """Query monthly trend data."""
    return execute_query(db_path, f"SELECT * FROM {table_name}", limit)


def get_channel_stats(db_path: str, limit: int = 100) -> list[dict]:
    """Query channel statistics."""
    return execute_query(db_path, "SELECT * FROM v_channel_stats", limit)


def get_chain_stats(db_path: str, limit: int = 100) -> list[dict]:
    """Query chain store statistics."""
    return execute_query(db_path, "SELECT * FROM v_chain_stats", limit)


def get_poi_quality_analysis(db_path: str, limit: int = 100) -> list[dict]:
    """Query POI quality analysis data."""
    return execute_query(db_path, "SELECT * FROM v_poi_quality_analysis", limit)


def get_geo_distribution(db_path: str, limit: int = 100) -> list[dict]:
    """Query geographic distribution data."""
    return execute_query(db_path, "SELECT * FROM v_geo_distribution", limit)


# MCP Server implementation using stdio
def main():
    parser = argparse.ArgumentParser(description="FMCG Database Query MCP Server")
    parser.add_argument("--db-path", default="data/fmcg_wide_table.db", help="Path to SQLite database")
    args = parser.parse_args()
    
    # Resolve db path relative to backend directory
    db_path = Path(args.db_path)
    if not db_path.is_absolute():
        db_path = Path(__file__).parent.parent / db_path
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line.strip())
            method = request.get("method")
            params = request.get("params", {})
            
            result = {"jsonrpc": "2.0", "id": request.get("id")}
            
            if method == "tools/list":
                result["result"] = {
                    "tools": [
                        {
                            "name": "execute_sql",
                            "description": "Execute arbitrary SQL query on FMCG database",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "sql": {"type": "string", "description": "SQL query to execute"},
                                    "limit": {"type": "integer", "description": "Max rows to return", "default": 100},
                                },
                                "required": ["sql"],
                            },
                        },
                        {
                            "name": "get_table_schema",
                            "description": "Get schema for a table",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "table_name": {"type": "string", "description": "Table name", "default": "tx_poi_information_total"},
                                },
                            },
                        },
                        {
                            "name": "get_tables",
                            "description": "Get list of tables in database",
                            "inputSchema": {"type": "object", "properties": {}},
                        },
                        {
                            "name": "query_poi",
                            "description": "Query POI data by conditions",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "city": {"type": "string", "description": "City name"},
                                    "district": {"type": "string", "description": "District name"},
                                    "channel": {"type": "string", "description": "Channel type (CVS/MT/GT)"},
                                    "chain": {"type": "string", "description": "Chain name (partial match)"},
                                    "industry": {"type": "string", "description": "Industry (水饮/啤酒/零食/奶粉/日化/眼镜/调料/白酒)"},
                                    "scene": {"type": "string", "description": "Scene (社区/商场/医院/写字楼/园区/学校/交通)"},
                                    "limit": {"type": "integer", "description": "Max rows to return", "default": 100},
                                },
                            },
                        },
                        {
                            "name": "query_trend",
                            "description": "Query monthly trend data",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "limit": {"type": "integer", "description": "Max rows to return", "default": 100},
                                },
                            },
                        },
                        {
                            "name": "query_channel_stats",
                            "description": "Query channel statistics",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "limit": {"type": "integer", "description": "Max rows to return", "default": 100},
                                },
                            },
                        },
                        {
                            "name": "query_chain_stats",
                            "description": "Query chain store statistics",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "limit": {"type": "integer", "description": "Max rows to return", "default": 100},
                                },
                            },
                        },
                        {
                            "name": "query_poi_quality",
                            "description": "Query POI quality analysis",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "limit": {"type": "integer", "description": "Max rows to return", "default": 100},
                                },
                            },
                        },
                        {
                            "name": "query_geo_distribution",
                            "description": "Query geographic distribution data",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "limit": {"type": "integer", "description": "Max rows to return", "default": 100},
                                },
                            },
                        },
                    ]
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                if tool_name == "execute_sql":
                    sql = tool_args.get("sql", "")
                    limit = tool_args.get("limit", 100)
                    data = execute_query(str(db_path), sql, limit)
                    result["result"] = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}
                elif tool_name == "get_table_schema":
                    table_name = tool_args.get("table_name", "tx_poi_information_total")
                    data = get_table_schema(str(db_path), table_name)
                    result["result"] = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}
                elif tool_name == "get_tables":
                    data = get_table_list(str(db_path))
                    result["result"] = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}
                elif tool_name == "query_poi":
                    data = get_poi_by_conditions(
                        str(db_path),
                        city=tool_args.get("city"),
                        district=tool_args.get("district"),
                        channel=tool_args.get("channel"),
                        chain=tool_args.get("chain"),
                        industry=tool_args.get("industry"),
                        scene=tool_args.get("scene"),
                        limit=tool_args.get("limit", 100),
                    )
                    result["result"] = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}
                elif tool_name == "query_trend":
                    data = get_trend_data(str(db_path), limit=tool_args.get("limit", 100))
                    result["result"] = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}
                elif tool_name == "query_channel_stats":
                    data = get_channel_stats(str(db_path), limit=tool_args.get("limit", 100))
                    result["result"] = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}
                elif tool_name == "query_chain_stats":
                    data = get_chain_stats(str(db_path), limit=tool_args.get("limit", 100))
                    result["result"] = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}
                elif tool_name == "query_poi_quality":
                    data = get_poi_quality_analysis(str(db_path), limit=tool_args.get("limit", 100))
                    result["result"] = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}
                elif tool_name == "query_geo_distribution":
                    data = get_geo_distribution(str(db_path), limit=tool_args.get("limit", 100))
                    result["result"] = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}
                else:
                    result["error"] = {"code": -32601, "message": f"Unknown tool: {tool_name}"}
            else:
                result["error"] = {"code": -32601, "message": f"Unknown method: {method}"}
            
            print(json.dumps(result), flush=True)
        except Exception as e:
            error_result = {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}
            print(json.dumps(error_result), flush=True)


if __name__ == "__main__":
    main()
