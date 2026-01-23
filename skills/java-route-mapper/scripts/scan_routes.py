#!/usr/bin/env python3
"""
Java Route Scanner - 快速扫描 Java Web 项目中的路由定义

用法：
    python scan_routes.py <project_path> [--output <output_file>] [--format <format>]

示例：
    python scan_routes.py /path/to/project
    python scan_routes.py /path/to/project --output routes.json --format json
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class Route:
    """路由信息"""
    http_method: str
    path: str
    class_name: str
    method_name: str
    source_file: str
    line_number: int
    parameters: List[Dict[str, str]] = field(default_factory=list)
    description: str = ""


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    source_file: str
    base_path: str = ""
    class_level_annotations: List[str] = field(default_factory=list)


class JavaRouteScanner:
    """Java 路由扫描器"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.routes: List[Route] = []
        self.class_info: Dict[str, ClassInfo] = {}

        # 注解模式
        self.patterns = {
            'spring_class': re.compile(r'@(?:Rest)?Controller\s+(?:public\s+)?class\s+(\w+)'),
            'spring_base_path': re.compile(r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']'),
            'spring_method': re.compile(r'@(Get|Post|Put|Patch|Delete)Mapping\s*\(\s*["\']([^"\']+)["\']'),
            'spring_request_mapping': re.compile(
                r'@RequestMapping\s*\(\s*.*?method\s*=\s*RequestMethod\.(\w+).*?(?:value\s*=\s*["\']([^"\']+)["\'])?',
                re.DOTALL
            ),
            'jaxrs_path': re.compile(r'@Path\s*\(\s*["\']([^"\']+)["\']'),
            'jaxrs_method': re.compile(r'@(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*\)'),
            'servlet': re.compile(r'@WebServlet\s*\(\s*(?:urlPatterns\s*=\s*)?["\']([^"\']+)["\']'),
            'public_method': re.compile(r'public\s+(?:[\w<>]+\s+)+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{'),
        }

        # 参数注解模式
        self.param_patterns = {
            'path_variable': re.compile(r'@PathVariable\s*(?:\(\s*(?:value\s*=\s*)?["\']?(\w+)["\']?\s*\))?'),
            'request_param': re.compile(r'@RequestParam\s*(?:\(\s*(?:value\s*=\s*)?["\']?(\w+)["\']?\s*(?:,.*?required\s*=\s*(\w+))?.*?\))?'),
            'request_body': re.compile(r'@RequestBody'),
            'request_header': re.compile(r'@RequestHeader\s*(?:\(\s*(?:value\s*=\s*)?["\']?(\w+)["\']?\s*\))?'),
            'cookie_value': re.compile(r'@CookieValue\s*(?:\(\s*(?:value\s*=\s*)?["\']?(\w+)["\']?\s*\))?'),
        }

    def scan(self) -> List[Route]:
        """扫描项目"""
        self._scan_java_files()
        return self.routes

    def _scan_java_files(self):
        """扫描所有 Java 文件"""
        java_files = list(self.project_path.rglob("*.java"))
        print(f"Found {len(java_files)} Java files...")

        for java_file in java_files:
            self._parse_java_file(java_file)

    def _parse_java_file(self, file_path: Path):
        """解析单个 Java 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return

        # 检测框架类型
        framework = self._detect_framework(content)

        if framework == 'spring':
            self._parse_spring_controller(file_path, lines)
        elif framework == 'jaxrs':
            self._parse_jaxrs_resource(file_path, lines)
        elif framework == 'servlet':
            self._parse_servlet(file_path, lines)

    def _detect_framework(self, content: str) -> Optional[str]:
        """检测使用的框架"""
        if re.search(r'@(?:Rest)?Controller|@RequestMapping|@Get|Post|Put|Delete|PatchMapping', content):
            return 'spring'
        elif re.search(r'@Path|@GET|@POST|@PUT|@DELETE', content):
            return 'jaxrs'
        elif re.search(r'@WebServlet|extends\s+HttpServlet', content):
            return 'servlet'
        return None

    def _parse_spring_controller(self, file_path: Path, lines: List[str]):
        """解析 Spring MVC 控制器"""
        content = '\n'.join(lines)

        # 查找类名和基础路径
        class_match = self.patterns['spring_class'].search(content)
        if not class_match:
            return

        class_name = class_match.group(1)
        base_path = ""

        # 查找 @RequestMapping 类级别注解
        for i, line in enumerate(lines):
            if '@RequestMapping' in line:
                path_match = self.patterns['spring_base_path'].search(line)
                if path_match:
                    base_path = path_match.group(1)
                break

        # 存储类信息
        self.class_info[class_name] = ClassInfo(
            name=class_name,
            source_file=str(file_path.relative_to(self.project_path)),
            base_path=base_path
        )

        # 查找方法
        for i, line in enumerate(lines, 1):
            # 检查 @GetMapping, @PostMapping 等
            method_match = self.patterns['spring_method'].search(line)
            if method_match:
                http_method = method_match.group(1).upper()
                method_path = method_match.group(2)
                self._add_spring_route(lines, i, class_name, http_method, method_path, base_path)
                continue

            # 检查 @RequestMapping with method
            mapping_match = self.patterns['spring_request_mapping'].search(line)
            if mapping_match:
                http_method = mapping_match.group(1).upper()
                method_path = mapping_match.group(2) if mapping_match.group(2) else ""
                self._add_spring_route(lines, i, class_name, http_method, method_path, base_path)

    def _add_spring_route(self, lines: List[str], start_line: int,
                          class_name: str, http_method: str, method_path: str, base_path: str):
        """添加 Spring 路由"""
        # 查找方法定义
        for i in range(start_line, min(start_line + 10, len(lines))):
            method_match = self.patterns['public_method'].search(lines[i])
            if method_match:
                method_name = method_match.group(1)

                # 组合完整路径
                full_path = base_path.rstrip('/') + '/' + method_path.lstrip('/')
                full_path = full_path.rstrip('/')

                # 解析参数
                parameters = self._parse_parameters(lines[start_line:i+1])

                self.routes.append(Route(
                    http_method=http_method,
                    path=full_path,
                    class_name=class_name,
                    method_name=method_name,
                    source_file=self.class_info[class_name].source_file,
                    line_number=start_line,
                    parameters=parameters
                ))
                break

    def _parse_jaxrs_resource(self, file_path: Path, lines: List[str]):
        """解析 JAX-RS 资源类"""
        # TODO: 实现 JAX-RS 解析
        pass

    def _parse_servlet(self, file_path: Path, lines: List[str]):
        """解析 Servlet"""
        # TODO: 实现 Servlet 解析
        pass

    def _parse_parameters(self, lines: List[str]) -> List[Dict[str, str]]:
        """解析方法参数"""
        parameters = []
        content = '\n'.join(lines)

        # 查找 @PathVariable
        for match in self.param_patterns['path_variable'].finditer(content):
            param_name = match.group(1) or 'pathVar'
            parameters.append({
                'name': param_name,
                'source': 'path',
                'type': 'unknown'
            })

        # 查找 @RequestParam
        for match in self.param_patterns['request_param'].finditer(content):
            param_name = match.group(1) or 'param'
            required = match.group(2) if match.group(2) else 'true'
            parameters.append({
                'name': param_name,
                'source': 'query',
                'type': 'unknown',
                'required': required
            })

        # 检查 @RequestBody
        if self.param_patterns['request_body'].search(content):
            parameters.append({
                'name': 'body',
                'source': 'body',
                'type': 'application/json'
            })

        return parameters

    def generate_burp_templates(self) -> List[str]:
        """生成 Burp Suite 请求模板"""
        templates = []

        for route in self.routes:
            template = self._generate_template(route)
            templates.append(template)

        return templates

    def _generate_template(self, route: Route) -> str:
        """生成单个路由的 Burp 模板"""
        lines = []

        # 请求行
        lines.append(f"{route.http_method} {route.path} HTTP/1.1")
        lines.append("Host: {{host}}")

        # 添加 Content-Type（如果有 body 参数）
        has_body = any(p['source'] == 'body' for p in route.parameters)
        if has_body:
            lines.append("Content-Type: application/json")

        lines.append("")  # 空行

        # 添加请求体
        if has_body:
            lines.append('{"key": "value"}')

        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Scan Java Web project for routes')
    parser.add_argument('project_path', help='Path to the Java project')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--format', '-f', choices=['json', 'text', 'burp'],
                        default='text', help='Output format')

    args = parser.parse_args()

    # 扫描项目
    scanner = JavaRouteScanner(args.project_path)
    routes = scanner.scan()

    print(f"\nFound {len(routes)} routes:")

    # 输出结果
    if args.format == 'json':
        output = json.dumps([asdict(r) for r in routes], indent=2)
    elif args.format == 'burp':
        output = '\n\n===\n\n'.join(scanner.generate_burp_templates())
    else:
        output = '\n'.join([
            f"{r.http_method:6} {r.path:40} -> {r.class_name}.{r.method_name}()"
            for r in routes
        ])

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\nOutput saved to: {args.output}")
    else:
        print('\n' + output)


if __name__ == '__main__':
    main()
