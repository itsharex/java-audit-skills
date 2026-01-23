#!/usr/bin/env python3
"""
Java Framework Detector - 检测 Java Web 项目使用的框架

用法：
    python detect_framework.py <project_path>

示例：
    python detect_framework.py /path/to/project
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class FrameworkDetector:
    """框架检测器"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)

        # 框架特征模式
        self.framework_signatures = {
            'spring_boot': {
                'files': [
                    'src/main/resources/application.properties',
                    'src/main/resources/application.yml',
                    'src/main/resources/application.yaml',
                ],
                'dependencies': [
                    'spring-boot-starter-web',
                    'spring-boot-starter-parent',
                ],
                'annotations': [
                    '@SpringBootApplication',
                    '@RestController',
                ]
            },
            'spring_mvc': {
                'files': [
                    'src/main/webapp/WEB-INF/[servlet]-servlet.xml',
                    'src/main/webapp/WEB-INF/applicationContext.xml',
                ],
                'dependencies': [
                    'spring-webmvc',
                    'spring-web',
                ],
                'annotations': [
                    '@Controller',
                    '@RequestMapping',
                    '@GetMapping',
                ]
            },
            'jersey': {
                'dependencies': [
                    'jersey-server',
                    'jersey-container-servlet',
                    'jersey-core',
                ],
                'annotations': [
                    '@Path',  # JAX-RS
                    '@GET',
                    '@POST',
                ]
            },
            'resteasy': {
                'dependencies': [
                    'resteasy-jaxrs',
                    'resteasy-spring',
                ],
                'annotations': [
                    '@Path',
                ]
            },
            'struts2': {
                'files': [
                    'src/main/webapp/WEB-INF/struts.xml',
                    'src/main/resources/struts.xml',
                ],
                'dependencies': [
                    'struts2-core',
                    'struts2-convention-plugin',
                ],
                'classes': [
                    'ActionSupport',
                    'com.opensymphony.xwork2.',
                ]
            },
            'servlet': {
                'files': [
                    'src/main/webapp/WEB-INF/web.xml',
                ],
                'annotations': [
                    '@WebServlet',
                    '@WebFilter',
                ]
            },
        }

    def detect(self) -> Dict[str, any]:
        """检测项目使用的框架"""
        results = {
            'primary_framework': None,
            'detected_frameworks': [],
            'details': {}
        }

        detected_scores = {}

        for framework, signatures in self.framework_signatures.items():
            score = 0
            details = []

            # 检查文件
            file_matches = self._check_files(signatures.get('files', []))
            if file_matches:
                score += len(file_matches) * 10
                details.append(f"Found files: {', '.join(file_matches)}")

            # 检查依赖
            dep_matches = self._check_dependencies(signatures.get('dependencies', []))
            if dep_matches:
                score += len(dep_matches) * 5
                details.append(f"Found dependencies: {', '.join(dep_matches)}")

            # 检查注解
            annotation_matches = self._check_annotations(signatures.get('annotations', []))
            if annotation_matches:
                score += len(annotation_matches) * 3
                details.append(f"Found annotations: {', '.join(annotation_matches)}")

            # 检查类引用
            class_matches = self._check_classes(signatures.get('classes', []))
            if class_matches:
                score += len(class_matches) * 2
                details.append(f"Found class references: {', '.join(class_matches)}")

            if score > 0:
                detected_scores[framework] = {
                    'score': score,
                    'details': details
                }

        # 按分数排序
        sorted_frameworks = sorted(detected_scores.items(), key=lambda x: x[1]['score'], reverse=True)

        if sorted_frameworks:
            results['primary_framework'] = sorted_frameworks[0][0]
            results['detected_frameworks'] = [f[0] for f in sorted_frameworks]
            results['details'] = {f: info for f, info in sorted_frameworks}

        return results

    def _check_files(self, patterns: List[str]) -> List[str]:
        """检查文件是否存在（支持通配符）"""
        found = []

        for pattern in patterns:
            # 处理通配符
            if '[' in pattern and ']' in pattern:
                # 简单的 [servlet] 替换为 *
                pattern = re.sub(r'\[\w+\]', '*', pattern)

            matches = list(self.project_path.glob(pattern))
            found.extend([str(m.relative_to(self.project_path)) for m in matches])

        return found

    def _check_dependencies(self, dependencies: List[str]) -> List[str]:
        """检查 Maven/Gradle 依赖"""
        found = []

        # 检查 pom.xml
        pom_path = self.project_path / 'pom.xml'
        if pom_path.exists():
            content = pom_path.read_text()
            for dep in dependencies:
                if dep in content:
                    found.append(dep)

        # 检查 build.gradle
        gradle_paths = [
            self.project_path / 'build.gradle',
            self.project_path / 'build.gradle.kts',
        ]
        for gradle_path in gradle_paths:
            if gradle_path.exists():
                content = gradle_path.read_text()
                for dep in dependencies:
                    if dep in content:
                        found.append(dep)

        return found

    def _check_annotations(self, annotations: List[str]) -> List[str]:
        """检查源码中的注解使用"""
        found = []
        java_files = list(self.project_path.rglob('*.java'))

        for annotation in annotations:
            pattern = re.compile(re.escape(annotation))
            for java_file in java_files[:100]:  # 限制检查文件数量
                try:
                    content = java_file.read_text(encoding='utf-8', errors='ignore')
                    if pattern.search(content):
                        found.append(annotation)
                        break
                except:
                    continue

        return found

    def _check_classes(self, patterns: List[str]) -> List[str]:
        """检查源码中的类引用"""
        found = []
        java_files = list(self.project_path.rglob('*.java'))

        for pattern in patterns:
            search_pattern = re.compile(re.escape(pattern))
            for java_file in java_files[:50]:  # 限制检查文件数量
                try:
                    content = java_file.read_text(encoding='utf-8', errors='ignore')
                    if search_pattern.search(content):
                        found.append(pattern)
                        break
                except:
                    continue

        return found

    def get_context_path(self) -> Optional[str]:
        """获取应用上下文路径"""
        context_paths = []

        # 检查 application.properties
        props_path = self.project_path / 'src/main/resources/application.properties'
        if props_path.exists():
            content = props_path.read_text()
            matches = re.findall(r'server\.servlet\.context-path\s*=\s*(.+)', content)
            matches.extend(re.findall(r'server\.contextPath\s*=\s*(.+)', content))
            context_paths.extend(matches)

        # 检查 application.yml
        yml_path = self.project_path / 'src/main/resources/application.yml'
        if yml_path.exists():
            content = yml_path.read_text()
            matches = re.findall(r'context-path:\s*(.+)', content)
            context_paths.extend(matches)

        # 检查 web.xml
        web_xml_path = self.project_path / 'src/main/webapp/WEB-INF/web.xml'
        if web_xml_path.exists():
            content = web_xml_path.read_text()

        return context_paths[0] if context_paths else None

    def get_base_package(self) -> Optional[str]:
        """获取基础包名"""
        # 从 pom.xml 获取
        pom_path = self.project_path / 'pom.xml'
        if pom_path.exists():
            content = pom_path.read_text()
            group_match = re.search(r'<groupId>(.+?)</groupId>', content)
            if group_match:
                return group_match.group(1).strip()

        # 从源码目录推断
        src_main_java = self.project_path / 'src/main/java'
        if src_main_java.exists():
            for item in src_main_java.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    return item.name

        return None


def print_results(results: Dict[str, any], context_path: Optional[str], base_package: Optional[str]):
    """打印检测结果"""
    print("=" * 60)
    print("Java Framework Detection Results")
    print("=" * 60)

    if results['primary_framework']:
        print(f"\nPrimary Framework: {results['primary_framework'].upper()}")

        print(f"\nAll Detected Frameworks:")
        for framework in results['detected_frameworks']:
            details = results['details'][framework]
            print(f"\n  {framework.upper()} (score: {details['score']})")
            for detail in details['details']:
                print(f"    - {detail}")
    else:
        print("\nNo frameworks detected.")

    print("\n" + "=" * 60)
    print("Additional Information")
    print("=" * 60)

    if context_path:
        print(f"Context Path: {context_path}")
    else:
        print("Context Path: Not found (default: '/')")

    if base_package:
        print(f"Base Package: {base_package}")
    else:
        print("Base Package: Not found")

    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python detect_framework.py <project_path>")
        sys.exit(1)

    project_path = sys.argv[1]

    if not Path(project_path).exists():
        print(f"Error: Project path does not exist: {project_path}")
        sys.exit(1)

    detector = FrameworkDetector(project_path)
    results = detector.detect()

    context_path = detector.get_context_path()
    base_package = detector.get_base_package()

    print_results(results, context_path, base_package)


if __name__ == '__main__':
    main()
