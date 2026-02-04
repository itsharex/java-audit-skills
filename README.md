# Java Audit Skills

专注于 Java 代码审计的 Claude Skills 集合，提供自动化源码分析、路由提取、参数映射等功能，辅助安全研究人员和开发者进行 Java Web 应用的安全审计工作。

## 功能特性

- **自动路由识别**：自动识别 Java Web 项目中的 HTTP 路由结构
- **多框架支持**：支持 Spring MVC、Servlet、JAX-RS、Struts 2 等主流框架
- **参数结构解析**：提取 Path、Query、Body、Header、Cookie 等各类参数
- **反编译集成**：集成 Java 反编译器，支持分析已编译的 .class 和 .jar 文件
- **Burp Suite 集成**：生成可直接用于 Burp Suite Repeater 的请求模板
- **接口文档生成**：为无 API 文档的项目生成接口清单
- **鉴权机制审计**：识别鉴权框架实现，分析鉴权绕过和越权访问风险
- **组件漏洞检测**：扫描第三方依赖，匹配 130+ 条 CVE 规则，生成安全报告

## 前置要求

在使用之前需要安装 [java-decompile-mcp](https://github.com/RuoJi6/java-decompile-mcp) MCP 服务，该服务提供 Java 反编译能力，用于分析已编译的 Java 文件。

## 目录结构

```
java-audit-skills/
├── README.md                    # 项目说明文档
└── skills/                      # Skills 集合目录
    ├── README.md               # Skills 详细说明
    ├── java-route-mapper/       # Java 路由与参数映射工具
    ├── java-auth-audit/         # Java 鉴权机制审计工具
    └── java-vuln-scanner/       # Java 组件版本漏洞检测工具
```

## 可用 Skills

| Skill | 说明 |
|-------|------|
| java-route-mapper | Java Web 源码路由与参数映射分析工具 |
| java-auth-audit | Java Web 源码鉴权机制审计工具 |
| java-vuln-scanner | Java 组件版本漏洞检测工具 |

详细说明请参阅 [skills/README.md](skills/README.md)

## 安装与使用

### 1. 安装 MCP Java Decompiler

```bash
# 按照 java-decompile-mcp 仓库说明进行安装
# https://github.com/RuoJi6/java-decompile-mcp
```

### 2. 配置 Skills

将 skills 目录下的内容复制到 Claude Code 的 skills 配置目录中。

### 3. 使用 Skill

在 Claude Code 中调用 skill：

```
/java-route-mapper /path/to/java/project
/java-auth-audit /path/to/java/project
/java-vuln-scanner /path/to/java/project
```

建议先使用 java-route-mapper 提取所有路由，再使用 java-auth-audit 分析鉴权机制，最后使用 java-vuln-scanner 检测组件漏洞，三者结合可完整审计项目的接口、权限控制和依赖安全。

## 最佳实践

1. 优先使用源码，仅在必要时使用反编译
2. 记录每个路由的源文件位置便于追溯
3. 输出格式统一，便于后续处理
4. 遇到无法解析的配置时记录并跳过

## 贡献

欢迎提交 Issue 和 Pull Request 来完善项目功能。

## 许可证

本项目仅供学习和研究使用。

## 交流群

![](assets/image-20260123114132975.png)

## 相关链接

- [java-decompile-mcp](https://github.com/RuoJi6/java-decompile-mcp) - Java 反编译 MCP 服务
- [Claude Code](https://claude.ai/claude-code) - Claude CLI 工具
