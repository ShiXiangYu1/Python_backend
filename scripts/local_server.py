#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
本地简易HTTP服务器

当无法安装依赖或运行完整的FastAPI应用时，
可以使用此脚本启动一个简单的HTTP服务器，提供项目的基本状态信息。
"""

import os
import sys
import json
import socket
import platform
import http.server
import socketserver
import sqlite3
from datetime import datetime
from threading import Thread
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# 常量定义
PORT = 8000
HOST = "localhost"

# 日志输出
def log(message, level="INFO"):
    """简单的日志输出函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    """
    简单的HTTP请求处理器
    
    提供基本的API端点，展示项目状态信息。
    """
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path.rstrip('/')
        
        # 处理API路由
        if path == '/api/v1/health':
            self.send_health_response()
        elif path == '/api/v1/status':
            self.send_status_response()
        elif path == '/api/v1/database':
            self.send_database_info()
        elif path == '/api/v1/environment':
            self.send_environment_info()
        elif path == '/api':
            self.send_api_docs()
        elif path == '':
            # 根路径，显示欢迎页面
            self.send_welcome_page()
        else:
            # 其他路径返回404
            self.send_error(404, "Not Found")
    
    def send_json_response(self, data):
        """发送JSON响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8'))
    
    def send_html_response(self, html):
        """发送HTML响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        # 添加HTML的meta标签确保正确编码
        if '<head>' in html and '<meta charset=' not in html:
            html = html.replace('<head>', '<head>\n<meta charset="utf-8">')
        self.wfile.write(html.encode('utf-8'))
    
    def send_health_response(self):
        """发送健康检查响应"""
        data = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "version": "local-server-0.1.0",
            "uptime": (datetime.now() - startup_time).total_seconds(),
        }
        self.send_json_response(data)
    
    def send_status_response(self):
        """发送状态信息响应"""
        status_info = get_status_info()
        self.send_json_response(status_info)
    
    def send_database_info(self):
        """发送数据库信息响应"""
        db_info = get_database_info()
        self.send_json_response(db_info)
    
    def send_environment_info(self):
        """发送环境信息响应"""
        env_info = get_environment_info()
        self.send_json_response(env_info)
    
    def send_api_docs(self):
        """发送API文档页面"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>AI模型管理平台 - API文档</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #555; margin-top: 30px; }}
                .endpoint {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .method {{ display: inline-block; padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; }}
                .get {{ background-color: #61affe; }}
                .url {{ margin-left: 10px; font-family: monospace; }}
                .description {{ margin-top: 10px; color: #555; }}
            </style>
        </head>
        <body>
            <h1>AI模型管理平台 - API文档 (简易服务器)</h1>
            <p>这是一个简易的HTTP服务器，提供以下API端点用于检查项目状态：</p>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="url">/api/v1/health</span>
                <div class="description">健康检查端点，返回服务器的基本健康状态</div>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="url">/api/v1/status</span>
                <div class="description">状态信息端点，返回服务器和项目的详细状态</div>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="url">/api/v1/database</span>
                <div class="description">数据库信息端点，返回项目数据库的基本信息</div>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="url">/api/v1/environment</span>
                <div class="description">环境信息端点，返回项目的环境设置信息</div>
            </div>
            
            <h2>正式启动说明</h2>
            <p>此服务器仅用于临时替代，要启动完整的应用，请先安装所有依赖：</p>
            <pre>pip install -r requirements.txt</pre>
            <p>然后使用以下命令启动：</p>
            <pre>python -m uvicorn app.main:app --reload</pre>
        </body>
        </html>
        """
        self.send_html_response(html)
    
    def send_welcome_page(self):
        """发送欢迎页面"""
        status_info = get_status_info()
        db_info = get_database_info()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>AI模型管理平台 - 简易服务器</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #555; margin-top: 30px; }}
                .card {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .success {{ color: green; }}
                .warning {{ color: orange; }}
                .error {{ color: red; }}
                .info-row {{ display: flex; margin-bottom: 10px; }}
                .info-label {{ flex: 1; font-weight: bold; }}
                .info-value {{ flex: 2; }}
            </style>
        </head>
        <body>
            <h1>AI模型管理平台 - 简易服务器</h1>
            <p>这是一个简易的HTTP服务器，提供项目状态信息。完整的FastAPI应用程序需要安装依赖后启动。</p>
            
            <div class="card">
                <h2>服务器状态</h2>
                <div class="info-row">
                    <div class="info-label">启动时间:</div>
                    <div class="info-value">{startup_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">运行时间:</div>
                    <div class="info-value">{str((datetime.now() - startup_time)).split('.')[0]}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Python版本:</div>
                    <div class="info-value">{platform.python_version()}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">系统平台:</div>
                    <div class="info-value">{platform.platform()}</div>
                </div>
            </div>
            
            <div class="card">
                <h2>项目环境检查</h2>
                <div class="info-row">
                    <div class="info-label">.env文件:</div>
                    <div class="info-value">{'<span class="success">存在</span>' if status_info.get('env_file_exists') else '<span class="error">不存在</span>'}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">数据库文件:</div>
                    <div class="info-value">{'<span class="success">存在</span>' if status_info.get('database_file_exists') else '<span class="error">不存在</span>'}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">数据库表数量:</div>
                    <div class="info-value">{db_info.get('table_count', '未知')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">上传目录:</div>
                    <div class="info-value">{'<span class="success">存在</span>' if status_info.get('uploads_dir_exists') else '<span class="warning">不存在</span>'}</div>
                </div>
            </div>
            
            <div class="card">
                <h2>启动完整应用</h2>
                <p>要启动完整的FastAPI应用，请先安装所有依赖：</p>
                <pre>pip install -r requirements.txt</pre>
                <p>然后使用以下命令启动应用：</p>
                <pre>python -m uvicorn app.main:app --reload</pre>
                <p>或使用Docker启动：</p>
                <pre>docker-compose up -d</pre>
            </div>
            
            <div class="card">
                <h2>API端点</h2>
                <p>此简易服务器提供以下API端点：</p>
                <ul>
                    <li><a href="/api/v1/health">/api/v1/health</a> - 健康检查</li>
                    <li><a href="/api/v1/status">/api/v1/status</a> - 服务器状态</li>
                    <li><a href="/api/v1/database">/api/v1/database</a> - 数据库信息</li>
                    <li><a href="/api/v1/environment">/api/v1/environment</a> - 环境信息</li>
                    <li><a href="/api">/api</a> - API文档</li>
                </ul>
            </div>
        </body>
        </html>
        """
        self.send_html_response(html)
    
    def log_message(self, format, *args):
        """自定义日志输出"""
        log(f"{self.address_string()} - {format % args}")

def get_status_info():
    """获取状态信息"""
    return {
        "status": "running",
        "startup_time": startup_time.isoformat(),
        "uptime_seconds": (datetime.now() - startup_time).total_seconds(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "directory": os.getcwd(),
        "env_file_exists": os.path.exists(".env"),
        "database_file_exists": os.path.exists("app.db"),
        "uploads_dir_exists": os.path.exists("uploads"),
        "is_simplified_server": True,
    }

def get_database_info():
    """获取数据库信息"""
    db_info = {
        "database_file": "app.db",
        "exists": os.path.exists("app.db"),
        "size_mb": round(os.path.getsize("app.db") / (1024 * 1024), 2) if os.path.exists("app.db") else 0,
        "table_count": 0,
        "tables": [],
    }
    
    # 如果数据库文件存在，尝试读取表信息
    if db_info["exists"]:
        try:
            conn = sqlite3.connect("app.db")
            cursor = conn.cursor()
            
            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            db_info["table_count"] = len(tables)
            db_info["tables"] = [table[0] for table in tables]
            
            # 获取每个表的行数
            table_rows = {}
            for table in db_info["tables"]:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    table_rows[table] = count
                except sqlite3.Error:
                    table_rows[table] = "error"
            
            db_info["table_rows"] = table_rows
            
            conn.close()
        except sqlite3.Error as e:
            db_info["error"] = str(e)
    
    return db_info

def get_environment_info():
    """获取环境变量信息"""
    env_info = {
        "system": platform.system(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "directory": os.getcwd(),
    }
    
    # 读取.env文件中的部分安全信息
    if os.path.exists(".env"):
        try:
            env_vars = {}
            with open(".env", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        try:
                            key, value = line.split("=", 1)
                            # 过滤敏感信息
                            if "SECRET" in key or "KEY" in key or "PASSWORD" in key:
                                value = "******"
                            env_vars[key] = value
                        except ValueError:
                            pass
            env_info["env_variables"] = env_vars
        except Exception as e:
            env_info["env_error"] = str(e)
    
    return env_info

def run_server():
    """运行HTTP服务器"""
    with socketserver.TCPServer((HOST, PORT), SimpleHandler) as httpd:
        log(f"启动简易HTTP服务器在 http://{HOST}:{PORT}")
        log(f"按 Ctrl+C 停止服务器")
        httpd.serve_forever()

if __name__ == "__main__":
    # 记录启动时间
    startup_time = datetime.now()
    
    try:
        run_server()
    except KeyboardInterrupt:
        log("服务器已停止")
    except Exception as e:
        log(f"服务器出错: {str(e)}", "ERROR")
        sys.exit(1) 