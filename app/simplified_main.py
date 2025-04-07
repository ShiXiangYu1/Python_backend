#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简易版FastAPI应用入口

在无法安装完整依赖的情况下，提供一个简化版的FastAPI应用入口。
使用Python标准库的http.server实现基本功能。
"""

import os
import sys
import json
import sqlite3
import http.server
import socketserver
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# 常量定义
PORT = 8000
HOST = "localhost"
DB_PATH = "app.db"
VERSION = "0.1.0"


def log(message, level="INFO"):
    """简单的日志输出函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


class JSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理日期等特殊类型"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class SimplifiedAPI(http.server.SimpleHTTPRequestHandler):
    """简化版API处理器"""

    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        # API路由
        if path.startswith("/api/v1"):
            route = path.replace("/api/v1", "")

            # 健康检查
            if route == "/health":
                self.handle_health()
            # 模型列表
            elif route == "/models":
                self.handle_models_list(query)
            # 用户信息
            elif route == "/users/me":
                self.handle_user_info()
            # API密钥列表
            elif route == "/api-keys":
                self.handle_api_keys_list(query)
            # 系统信息
            elif route == "/system-info":
                self.handle_system_info()
            # 数据库信息
            elif route == "/database-info":
                self.handle_database_info()
            else:
                self.send_error(404, "API路由不存在")
        # 静态文件或根页面
        else:
            self.handle_static_or_root()

    def send_json_response(self, data):
        """发送JSON响应"""
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            json.dumps(data, cls=JSONEncoder, ensure_ascii=False, indent=2).encode(
                "utf-8"
            )
        )

    def send_html_response(self, content):
        """发送HTML响应"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        if "<head>" in content and "<meta charset=" not in content:
            content = content.replace("<head>", '<head>\n<meta charset="utf-8">')
        self.wfile.write(content.encode("utf-8"))

    def handle_health(self):
        """处理健康检查端点"""
        response = {
            "status": "ok",
            "version": VERSION,
            "timestamp": datetime.now(),
            "database_connected": self.check_database_connection(),
        }
        self.send_json_response(response)

    def handle_models_list(self, query):
        """处理模型列表端点"""
        page = int(query.get("page", [1])[0])
        limit = int(query.get("limit", [10])[0])

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 获取模型总数
            cursor.execute("SELECT COUNT(*) as total FROM model;")
            total = cursor.fetchone()["total"]

            # 获取分页数据
            offset = (page - 1) * limit
            cursor.execute(
                """
                SELECT id, name, description, framework, version, status, 
                       is_public, file_path, file_size, created_at, updated_at, owner_id
                FROM model
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?;
            """,
                (limit, offset),
            )

            items = []
            for row in cursor.fetchall():
                items.append(dict(row))

            response = {
                "items": items,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit,
            }
            self.send_json_response(response)
        except sqlite3.Error as e:
            self.send_json_response({"error": "数据库错误", "detail": str(e)})
        finally:
            if conn:
                conn.close()

    def handle_user_info(self):
        """处理用户信息端点"""
        # 在简化版中，返回模拟用户
        user_info = {
            "id": "00000000-0000-0000-0000-000000000001",
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "管理员",
            "is_active": True,
            "role": "admin",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        self.send_json_response(user_info)

    def handle_api_keys_list(self, query):
        """处理API密钥列表端点"""
        # 在简化版中，返回模拟数据
        api_keys = []
        for i in range(5):
            api_keys.append(
                {
                    "id": f"00000000-0000-0000-0000-00000000000{i+1}",
                    "name": f"测试密钥 {i+1}",
                    "key": f"api_key_{i+1}",
                    "scopes": "read,write",
                    "is_active": True,
                    "expires_at": None,
                    "last_used_at": datetime.now(),
                    "usage_count": i * 10,
                    "user_id": "00000000-0000-0000-0000-000000000001",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "is_expired": False,
                    "is_valid": True,
                }
            )

        response = {
            "items": api_keys,
            "total": len(api_keys),
            "page": 1,
            "limit": 10,
            "pages": 1,
        }
        self.send_json_response(response)

    def handle_system_info(self):
        """处理系统信息端点"""
        info = {
            "python_version": sys.version,
            "platform": sys.platform,
            "server_time": datetime.now(),
            "env_variables": {
                "APP_NAME": os.environ.get("APP_NAME", "AI模型管理平台"),
                "API_PREFIX": os.environ.get("API_PREFIX", "/api/v1"),
                "APP_DEBUG": os.environ.get("APP_DEBUG", "true") == "true",
                "DATABASE_URL": os.environ.get("DATABASE_URL", "sqlite:///app.db"),
                "MODEL_UPLOAD_DIR": os.environ.get(
                    "MODEL_UPLOAD_DIR", "./uploads/models"
                ),
            },
        }
        self.send_json_response(info)

    def handle_database_info(self):
        """处理数据库信息端点"""
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row["name"] for row in cursor.fetchall()]

            # 获取每个表的行数
            table_counts = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table};")
                count = cursor.fetchone()["count"]
                table_counts[table] = count

            response = {
                "database": DB_PATH,
                "tables": tables,
                "table_counts": table_counts,
                "total_tables": len(tables),
                "connection_status": "connected",
            }
            self.send_json_response(response)
        except sqlite3.Error as e:
            self.send_json_response({"error": "数据库错误", "detail": str(e)})
        finally:
            if conn:
                conn.close()

    def handle_static_or_root(self):
        """处理静态文件或根页面请求"""
        if self.path == "/" or self.path == "":
            self.serve_index_page()
        else:
            # 尝试提供静态文件
            try:
                super().do_GET()
            except:
                self.serve_index_page()

    def serve_index_page(self):
        """提供简化的首页"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI模型管理平台 - 简化版</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #555; margin-top: 30px; }}
                .card {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .success {{ color: green; }}
                .warning {{ color: orange; }}
                .error {{ color: red; }}
                .info-row {{ display: flex; margin-bottom: 10px; }}
                .info-label {{ flex: 1; font-weight: bold; }}
                .info-value {{ flex: 2; }}
                a {{ color: #0066cc; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .api-section {{ background: #e9f7fe; padding: 15px; border-radius: 5px; margin-top: 10px; }}
                code {{ background: #f0f0f0; padding: 2px 4px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <h1>AI模型管理平台 - 简化版</h1>
            <p>这是AI模型管理平台的简化版，提供了基本的API访问功能。</p>
            
            <div class="card">
                <h2>服务器状态</h2>
                <div class="info-row">
                    <div class="info-label">版本:</div>
                    <div class="info-value">{VERSION}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">启动时间:</div>
                    <div class="info-value">{startup_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">运行时间:</div>
                    <div class="info-value">{str((datetime.now() - startup_time)).split('.')[0]}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">数据库状态:</div>
                    <div class="info-value">{'<span class="success">已连接</span>' if self.check_database_connection() else '<span class="error">未连接</span>'}</div>
                </div>
            </div>
            
            <div class="card">
                <h2>可用API端点</h2>
                <p>以下是可用的API端点列表:</p>
                
                <div class="api-section">
                    <h3>健康检查</h3>
                    <p><code>GET /api/v1/health</code> - 检查系统健康状态</p>
                    <p><a href="/api/v1/health" target="_blank">查看健康状态</a></p>
                </div>
                
                <div class="api-section">
                    <h3>模型管理</h3>
                    <p><code>GET /api/v1/models</code> - 获取模型列表</p>
                    <p><a href="/api/v1/models" target="_blank">查看模型列表</a></p>
                </div>
                
                <div class="api-section">
                    <h3>用户管理</h3>
                    <p><code>GET /api/v1/users/me</code> - 获取当前用户信息</p>
                    <p><a href="/api/v1/users/me" target="_blank">查看用户信息</a></p>
                </div>
                
                <div class="api-section">
                    <h3>API密钥管理</h3>
                    <p><code>GET /api/v1/api-keys</code> - 获取API密钥列表</p>
                    <p><a href="/api/v1/api-keys" target="_blank">查看API密钥列表</a></p>
                </div>
                
                <div class="api-section">
                    <h3>系统信息</h3>
                    <p><code>GET /api/v1/system-info</code> - 获取系统信息</p>
                    <p><a href="/api/v1/system-info" target="_blank">查看系统信息</a></p>
                </div>
                
                <div class="api-section">
                    <h3>数据库信息</h3>
                    <p><code>GET /api/v1/database-info</code> - 获取数据库信息</p>
                    <p><a href="/api/v1/database-info" target="_blank">查看数据库信息</a></p>
                </div>
            </div>
            
            <div class="card">
                <h2>说明</h2>
                <p>此简化版仅提供基本的API访问功能，无法使用完整的FastAPI功能。</p>
                <p>要运行完整版，请安装所有依赖:</p>
                <pre>pip install -r requirements.txt</pre>
                <p>然后使用以下命令启动:</p>
                <pre>python -m uvicorn app.main:app --reload</pre>
            </div>
        </body>
        </html>
        """
        self.send_html_response(html)

    def check_database_connection(self):
        """检查数据库连接状态"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            conn.close()
            return True
        except:
            return False

    def log_message(self, format, *args):
        """自定义日志输出"""
        log(f"{self.address_string()} - {format % args}")


def run_server():
    """运行HTTP服务器"""
    server_address = (HOST, PORT)
    httpd = socketserver.TCPServer(server_address, SimplifiedAPI)
    log(f"启动简易API服务器 http://{HOST}:{PORT}")
    log("按 Ctrl+C 停止服务器")
    httpd.serve_forever()


if __name__ == "__main__":
    # 记录启动时间
    startup_time = datetime.now()

    # 检查数据库文件
    if not os.path.exists(DB_PATH):
        log(f"警告: 数据库文件 {DB_PATH} 不存在", "WARNING")

    try:
        run_server()
    except KeyboardInterrupt:
        log("服务器已停止")
    except Exception as e:
        log(f"服务器出错: {str(e)}", "ERROR")
        sys.exit(1)
