#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
安全性扫描脚本

该脚本检查项目中的常见安全问题，如：
1. 硬编码的密钥和密码
2. 不安全的配置
3. 缺少的安全防护措施
4. 最佳实践违规
"""

import os
import re
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("安全扫描")

# 路径设置
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全问题严重程度
class Severity:
    """安全问题严重程度"""
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"
    INFO = "信息"

class SecurityScanner:
    """安全扫描器类"""
    
    def __init__(self, base_dir: Path, exclude_dirs: List[str] = None):
        """初始化安全扫描器
        
        参数:
            base_dir: 项目根目录
            exclude_dirs: 排除的目录
        """
        self.base_dir = base_dir
        self.exclude_dirs = exclude_dirs or [
            ".git", "venv", "env", "__pycache__", "node_modules", 
            "dist", "build", ".pytest_cache", "uploads"
        ]
        self.issues = []
        
    def _is_excluded(self, path: Path) -> bool:
        """检查路径是否被排除
        
        参数:
            path: 要检查的路径
            
        返回:
            是否被排除
        """
        parts = path.parts
        return any(excluded in parts for excluded in self.exclude_dirs)
    
    def _scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """扫描单个文件中的安全问题
        
        参数:
            file_path: 文件路径
            
        返回:
            发现的安全问题列表
        """
        file_issues = []
        file_ext = file_path.suffix.lower()
        relative_path = file_path.relative_to(self.base_dir)
        
        # 跳过二进制文件和大文件
        if file_ext in ['.pyc', '.jpg', '.png', '.gif', '.pdf', '.zip', '.gz', '.exe']:
            return []
        
        try:
            file_size = file_path.stat().st_size
            if file_size > 1024 * 1024:  # 1MB
                logger.warning(f"跳过大文件 {relative_path} ({file_size/1024/1024:.2f} MB)")
                return []
                
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # 按文件类型检查特定问题
            if file_ext == '.py':
                file_issues.extend(self._scan_python_file(relative_path, content))
            elif file_ext in ['.env', '.flaskenv', '.ini', '.conf', '.cfg', '.yml', '.yaml', '.json']:
                file_issues.extend(self._scan_config_file(relative_path, content, file_ext))
            
            # 通用的检查（适用于所有文件类型）
            file_issues.extend(self._scan_common_issues(relative_path, content))
            
        except Exception as e:
            logger.error(f"扫描文件 {relative_path} 时发生错误: {e}")
        
        return file_issues
    
    def _scan_python_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        """扫描Python文件中的安全问题
        
        参数:
            file_path: 文件路径
            content: 文件内容
            
        返回:
            发现的安全问题列表
        """
        issues = []
        
        # 检查硬编码的密钥和密码
        secret_patterns = [
            (r'(?i)(api_key|apikey|secret|password|token)(?:\s*=\s*|\s*:\s*)[\'\"]([^\'\"\s]+)[\'\"]\s*$', 
             Severity.HIGH, "硬编码的敏感信息"),
            (r'(?i)const\s+(api_key|apikey|secret|password|token)\s*=\s*[\'\"]([^\'\"\s]+)[\'\"]\s*', 
             Severity.HIGH, "硬编码的敏感信息"),
        ]
        
        for i, line in enumerate(content.split('\n')):
            for pattern, severity, message in secret_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    # 排除变量名或引用
                    if 'os.environ' in line or 'settings.' in line or 'config.' in line:
                        continue
                    
                    # 排除明显的占位符和示例
                    value = match[1] if isinstance(match, tuple) and len(match) > 1 else match
                    if value in ['YOUR_API_KEY', 'INSERT_KEY_HERE', 'your_password', 'example', 'placeholder']:
                        continue
                        
                    issues.append({
                        "file": str(file_path),
                        "line": i + 1,
                        "severity": severity,
                        "message": f"{message}: {line.strip()}",
                        "type": "secret_exposure"
                    })
        
        # 检查不安全的导入和函数
        insecure_imports = [
            (r'from\s+pickle\s+import', Severity.MEDIUM, 
             "使用pickle模块可能导致反序列化漏洞，建议使用json或其他安全的序列化方式"),
            (r'import\s+pickle', Severity.MEDIUM, 
             "使用pickle模块可能导致反序列化漏洞，建议使用json或其他安全的序列化方式"),
            (r'os\.system\s*\(', Severity.MEDIUM, 
             "使用os.system可能导致命令注入，建议使用subprocess模块的安全函数"),
            (r'subprocess\.call\s*\(\s*(?:\'|\").*(?:\'|\")\s*\+', Severity.HIGH, 
             "构建命令字符串可能导致命令注入，应使用参数列表"),
            (r'subprocess\.Popen\s*\(\s*(?:\'|\").*(?:\'|\")\s*\+', Severity.HIGH, 
             "构建命令字符串可能导致命令注入，应使用参数列表"),
            (r'eval\s*\(', Severity.HIGH, 
             "使用eval可能导致代码注入，应避免使用"),
            (r'exec\s*\(', Severity.HIGH, 
             "使用exec可能导致代码注入，应避免使用"),
            (r'\.execute\s*\(\s*(?:\'|\").*(?:\'|\")\s*%', Severity.HIGH, 
             "直接构建SQL查询可能导致SQL注入，应使用参数化查询"),
            (r'\.execute\s*\(\s*(?:\'|\").*(?:\'|\")\s*\+', Severity.HIGH, 
             "直接构建SQL查询可能导致SQL注入，应使用参数化查询"),
            (r'\.execute\s*\(\s*(?:\'|\").*(?:\'|\")\s*\.format', Severity.HIGH, 
             "直接构建SQL查询可能导致SQL注入，应使用参数化查询"),
            (r'\.execute\s*\(\s*(?:\'|\").*(?:\'|\")\s*\{\}', Severity.HIGH, 
             "直接构建SQL查询可能导致SQL注入，应使用参数化查询"),
            (r'\.query\s*\(\s*(?:\'|\").*(?:\'|\")\s*%', Severity.HIGH, 
             "直接构建SQL查询可能导致SQL注入，应使用参数化查询"),
            (r'\.query\s*\(\s*(?:\'|\").*(?:\'|\")\s*\+', Severity.HIGH, 
             "直接构建SQL查询可能导致SQL注入，应使用参数化查询"),
            (r'\.query\s*\(\s*(?:\'|\").*(?:\'|\")\s*\.format', Severity.HIGH, 
             "直接构建SQL查询可能导致SQL注入，应使用参数化查询"),
        ]
        
        for pattern, severity, message in insecure_imports:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    "file": str(file_path),
                    "line": line_num,
                    "severity": severity,
                    "message": message,
                    "type": "insecure_code"
                })
        
        # 检查缺失的安全措施（需要上下文，只是初步判断）
        flask_patterns = [
            (r'app\s*=\s*Flask\s*\(', r'CSRFProtect\s*\(\s*app\s*\)', Severity.MEDIUM, 
             "Flask应用似乎没有启用CSRF保护，建议使用flask_wtf.CSRFProtect"),
            (r'@app\.route\s*\(\s*(?:\'|\")/api/', r'@jwt_required', Severity.MEDIUM, 
             "API端点似乎没有JWT认证保护，建议使用jwt_required装饰器")
        ]
        
        for pattern, required_pattern, severity, message in flask_patterns:
            if re.search(pattern, content) and not re.search(required_pattern, content):
                issues.append({
                    "file": str(file_path),
                    "line": 0,  # 整个文件
                    "severity": severity,
                    "message": message,
                    "type": "missing_protection"
                })
        
        # 检查调试/开发模式
        debug_patterns = [
            (r'DEBUG\s*=\s*True', Severity.MEDIUM, 
             "生产环境不应启用DEBUG模式，存在安全风险"),
            (r'app\.run\s*\(\s*debug\s*=\s*True', Severity.MEDIUM, 
             "生产环境不应启用DEBUG模式，存在安全风险"),
        ]
        
        for pattern, severity, message in debug_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                
                # 检查是否有开发环境条件判断
                context_start = max(0, match.start() - 100)
                context_end = min(len(content), match.end() + 100)
                context = content[context_start:context_end]
                
                if any(s in context for s in ["if os.environ.get('ENVIRONMENT') == 'development'", 
                                             "if app.debug", "if DEBUG", "if __name__ == '__main__'"]):
                    severity = Severity.LOW
                    message += "（但似乎有条件判断）"
                
                issues.append({
                    "file": str(file_path),
                    "line": line_num,
                    "severity": severity,
                    "message": message,
                    "type": "debug_enabled"
                })
        
        return issues
                
    def _scan_config_file(self, file_path: Path, content: str, file_ext: str) -> List[Dict[str, Any]]:
        """扫描配置文件中的安全问题
        
        参数:
            file_path: 文件路径
            content: 文件内容
            file_ext: 文件扩展名
            
        返回:
            发现的安全问题列表
        """
        issues = []
        
        # 检查敏感信息
        sensitive_patterns = [
            (r'(?i)(api_key|apikey|secret|password|token)(?:\s*[=:]\s*)[\'\"]([a-zA-Z0-9\-_\.]{8,})[\'\"]', 
             Severity.HIGH, "配置文件中的敏感信息"),
            (r'(?i)(auth|access)[_\-]token(?:\s*[=:]\s*)[\'\"]([a-zA-Z0-9\-_\.]{8,})[\'\"]', 
             Severity.HIGH, "配置文件中的敏感信息"),
            (r'(?i)connectionstring(?:\s*[=:]\s*).*password=([^\s;]+)', 
             Severity.HIGH, "数据库连接字符串包含明文密码"),
        ]
        
        # 排除样例文件
        if 'example' in file_path.name or 'sample' in file_path.name:
            for i, line in enumerate(content.split('\n')):
                # 仍然检查一些高风险情况，如实际的令牌
                for pattern, severity, message in sensitive_patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        value = match[1] if isinstance(match, tuple) and len(match) > 1 else match
                        if (len(value) > 20 and 
                            value not in ['YOUR_API_KEY', 'INSERT_KEY_HERE', 'your_password', 'example', 'placeholder']):
                            issues.append({
                                "file": str(file_path),
                                "line": i + 1,
                                "severity": severity,
                                "message": f"{message} (示例文件中的真实敏感信息): {line.strip()}",
                                "type": "secret_in_sample"
                            })
        else:
            # 正常配置文件检查
            for i, line in enumerate(content.split('\n')):
                for pattern, severity, message in sensitive_patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        value = match[1] if isinstance(match, tuple) and len(match) > 1 else match
                        if value not in ['YOUR_API_KEY', 'INSERT_KEY_HERE', 'your_password', 'example', 'placeholder']:
                            issues.append({
                                "file": str(file_path),
                                "line": i + 1,
                                "severity": severity,
                                "message": f"{message}: {line.strip()}",
                                "type": "sensitive_config"
                            })
        
        # 检查不安全的配置
        insecure_config_patterns = [
            (r'(?i)allow_origins\s*[=:]\s*[\'\"]?\*[\'\"]?', Severity.MEDIUM, 
             "CORS允许所有来源，这可能导致跨站请求伪造攻击"),
            (r'(?i)debug\s*[=:]\s*(?:true|1|yes)', Severity.MEDIUM, 
             "调试模式已启用，不应在生产环境中使用"),
            (r'(?i)ssl_verify\s*[=:]\s*(?:false|0|no)', Severity.HIGH, 
             "SSL验证已禁用，这可能导致中间人攻击"),
            (r'(?i)verify_ssl\s*[=:]\s*(?:false|0|no)', Severity.HIGH, 
             "SSL验证已禁用，这可能导致中间人攻击"),
        ]
        
        for i, line in enumerate(content.split('\n')):
            for pattern, severity, message in insecure_config_patterns:
                if re.search(pattern, line):
                    # 检查是否有开发环境条件判断
                    if 'development' in file_path.name or 'local' in file_path.name:
                        severity = Severity.LOW
                        message += "（在开发环境配置中）"
                    
                    issues.append({
                        "file": str(file_path),
                        "line": i + 1,
                        "severity": severity,
                        "message": message,
                        "type": "insecure_config"
                    })
        
        return issues
    
    def _scan_common_issues(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        """扫描所有文件中的通用安全问题
        
        参数:
            file_path: 文件路径
            content: 文件内容
            
        返回:
            发现的安全问题列表
        """
        issues = []
        
        # 检查AWS访问密钥
        aws_patterns = [
            (r'(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])', Severity.HIGH, 
             "可能的AWS密钥"),
            (r'AKIA[0-9A-Z]{16}', Severity.HIGH, 
             "可能的AWS访问密钥ID"),
        ]
        
        for i, line in enumerate(content.split('\n')):
            for pattern, severity, message in aws_patterns:
                if re.search(pattern, line):
                    issues.append({
                        "file": str(file_path),
                        "line": i + 1,
                        "severity": severity,
                        "message": message,
                        "type": "aws_key"
                    })
        
        # 检查私钥文件内容
        if "PRIVATE KEY" in content:
            issues.append({
                "file": str(file_path),
                "line": 0,
                "severity": Severity.HIGH,
                "message": "文件中包含私钥内容",
                "type": "private_key"
            })
            
        # 检查IP地址（信息性）
        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        localhost_ips = set(['127.0.0.1', '0.0.0.0', '192.168.0.1', '192.168.1.1', '10.0.0.1'])
        
        ip_matches = re.finditer(ip_pattern, content)
        for match in ip_matches:
            ip = match.group(0)
            if ip not in localhost_ips:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    "file": str(file_path),
                    "line": line_num,
                    "severity": Severity.INFO,
                    "message": f"硬编码的IP地址: {ip}",
                    "type": "hardcoded_ip"
                })
        
        return issues
    
    def scan(self) -> List[Dict[str, Any]]:
        """扫描整个项目的安全问题
        
        返回:
            发现的安全问题列表
        """
        logger.info(f"开始安全扫描，目录: {self.base_dir}")
        
        for root, dirs, files in os.walk(self.base_dir):
            # 跳过排除的目录
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            root_path = Path(root)
            if self._is_excluded(root_path):
                continue
                
            for file in files:
                file_path = root_path / file
                if not self._is_excluded(file_path):
                    file_issues = self._scan_file(file_path)
                    self.issues.extend(file_issues)
        
        logger.info(f"扫描完成，发现 {len(self.issues)} 个问题")
        
        # 按严重程度划分统计
        severity_counts = {
            Severity.HIGH: 0,
            Severity.MEDIUM: 0,
            Severity.LOW: 0,
            Severity.INFO: 0
        }
        
        for issue in self.issues:
            severity_counts[issue['severity']] += 1
        
        logger.info(f"问题统计: 高: {severity_counts[Severity.HIGH]}, "
                   f"中: {severity_counts[Severity.MEDIUM]}, "
                   f"低: {severity_counts[Severity.LOW]}, "
                   f"信息: {severity_counts[Severity.INFO]}")
        
        return self.issues
    
    def generate_report(self, output_file: str = "security_report.json") -> None:
        """生成安全报告
        
        参数:
            output_file: 输出文件路径
        """
        # 按严重程度排序
        severity_order = {
            Severity.HIGH: 0,
            Severity.MEDIUM: 1,
            Severity.LOW: 2,
            Severity.INFO: 3
        }
        
        sorted_issues = sorted(
            self.issues, 
            key=lambda x: (severity_order.get(x['severity'], 4), x['file'], x['line'])
        )
        
        report = {
            "scan_time": datetime.now().isoformat(),
            "total_issues": len(self.issues),
            "severity_counts": {
                "high": sum(1 for i in self.issues if i['severity'] == Severity.HIGH),
                "medium": sum(1 for i in self.issues if i['severity'] == Severity.MEDIUM),
                "low": sum(1 for i in self.issues if i['severity'] == Severity.LOW),
                "info": sum(1 for i in self.issues if i['severity'] == Severity.INFO)
            },
            "issues": sorted_issues
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"安全报告已保存到: {output_file}")


def main():
    """主函数"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description='项目安全扫描工具')
    parser.add_argument('--output', default='security_report.json', help='输出报告文件路径')
    parser.add_argument('--exclude', nargs='+', help='要排除的目录，以空格分隔')
    args = parser.parse_args()
    
    exclude_dirs = args.exclude if args.exclude else None
    
    scanner = SecurityScanner(BASE_DIR, exclude_dirs=exclude_dirs)
    scanner.scan()
    scanner.generate_report(args.output)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 