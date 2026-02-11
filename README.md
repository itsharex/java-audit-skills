# Java Audit Skills

专注于 Java 代码审计的 Claude Skills 集合，提供自动化源码分析、路由提取、参数映射等功能，辅助安全研究人员和开发者进行 Java Web 应用的安全审计工作。

## 功能特性

- **自动路由识别**：自动识别 Java Web 项目中的 HTTP 路由结构
- **多框架支持**：支持 Spring MVC、Servlet、JAX-RS、Struts 2 等主流框架
- **参数结构解析**：提取 Path、Query、Body、Header、Cookie 等各类参数
- **反编译集成**：集成 Java 反编译器，支持分析已编译的 .class 和 .jar 文件
- **Burp Suite 集成**：生成可直接用于 Burp Suite Repeater 的请求模板
- **接口文档生成**：为无 API 文档的项目生成接口清单
- **路由调用链追踪**：追踪从 Controller 到 DAO 层的完整调用链，分析参数流向
- **鉴权机制审计**：识别鉴权框架实现，分析鉴权绕过和越权访问风险
- **SQL 注入审计**：识别 SQL 执行框架，检测 SQL 注入漏洞风险
- **文件上传审计**：识别文件上传入口，分析路径穿越和可执行文件上传风险
- **文件读取审计**：识别文件读取操作，分析路径遍历攻击风险
- **XXE 审计**：识别 XML 解析操作，检测外部实体注入漏洞风险
- **组件漏洞检测**：扫描第三方依赖，匹配 130+ 条 CVE 规则，生成安全报告

## 前置要求

在使用之前需要安装 [java-decompile-mcp](https://github.com/RuoJi6/java-decompile-mcp) MCP 服务，该服务提供 Java 反编译能力，用于分析已编译的 Java 文件。

## 目录结构

```
java-audit-skills/
├── README.md                    # 项目说明文档
└── skills/                      # Skills 集合目录
    ├── README.md               # Skills 详细说明
    ├── shared/                 # 共享工具和资源
    ├── java-route-mapper/      # Java 路由与参数映射工具
    ├── java-route-tracer/      # Java 路由调用链追踪工具
    ├── java-sql-audit/         # Java SQL 注入审计工具
    ├── java-auth-audit/        # Java 鉴权机制审计工具
    ├── java-file-upload-audit/ # Java 文件上传漏洞审计工具
    ├── java-file-read-audit/   # Java 文件读取漏洞审计工具
    ├── java-xxe-audit/        # Java XXE 漏洞审计工具
    └── java-vuln-scanner/     # Java 组件版本漏洞检测工具
```

## 可用 Skills

| Skill                | 说明                                    |
| ------------------- | --------------------------------------- |
| java-route-mapper   | Java Web 源码路由与参数映射分析工具     |
| java-route-tracer   | Java Web 源码路由多层级调用链追踪工具   |
| java-sql-audit      | Java Web 源码 SQL 注入漏洞审计工具      |
| java-auth-audit     | Java Web 源码鉴权机制审计工具           |
| java-file-upload-audit | Java Web 源码文件上传漏洞审计工具     |
| java-file-read-audit   | Java Web 源码文件读取漏洞审计工具     |
| java-xxe-audit      | Java Web 源码 XXE 漏洞审计工具         |
| java-vuln-scanner   | Java 组件版本漏洞检测工具               |

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

**参数说明：**
- `/path/to/project` - Java 项目根目录，包含源码（.java）或编译文件（.class/.jar）
- `--route` - 指定要追踪的具体路由路径

```
/java-route-mapper /path/to/project
/java-route-tracer --route /api/users/login --project /path/to/project
/java-sql-audit /path/to/project
/java-auth-audit /path/to/project
/java-file-upload-audit /path/to/project
/java-file-read-audit /path/to/project
/java-xxe-audit /path/to/project
/java-vuln-scanner /path/to/project
```

**使用流程：**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Java 审计技能使用流程                            │
└─────────────────────────────────────────────────────────────────────────┘

步骤1: java-route-mapper
┌─────────────────────────────────────────────────────────────────────────┐
│ 项目路径作用：扫描项目源码，识别路由定义                                │
│ 输出：所有 HTTP 路由、参数定义、Burp Suite 请求模板                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
步骤2: java-route-tracer（指定单个路由 + java-route-mapper 结果目录）
┌─────────────────────────────────────────────────────────────────────────┐
│ 项目路径作用：基于项目源码定位路由入口并追踪调用链                      │
│ 输出：完整调用链、参数流向、Sink 识别、可控性分析                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
步骤3: java-sql-audit（java-route-tracer 结果 + 指定单个路由 + java-route-mapper 结果目录）
┌─────────────────────────────────────────────────────────────────────────┐
│ 项目路径作用：扫描项目源码，识别 SQL 执行点                             │
│ 输出：SQL 注入漏洞、参数化查询分析、验证 PoC                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
步骤4: java-auth-audit
┌─────────────────────────────────────────────────────────────────────────┐
│ 项目路径作用：扫描项目源码和配置，识别鉴权框架                          │
│ 输出：鉴权配置、拦截规则、越权风险、绕过漏洞                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
步骤5: java-file-upload-audit / java-file-read-audit / java-xxe-audit
┌─────────────────────────────────────────────────────────────────────────┐
│ 项目路径作用：扫描项目源码，识别文件上传/读取/XXE 操作点               │
│ 输出：相关漏洞风险、路径遍历分析、参数校验缺失检测                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
步骤6: java-vuln-scanner
┌─────────────────────────────────────────────────────────────────────────┐
│ 项目路径作用：扫描 pom.xml、build.gradle 或 .jar 文件                   │
│ 输出：CVE 漏洞匹配结果、组件版本漏洞报告                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
                    ┌─────────────────────────┐
                    │     审计报告输出目录     │
                    └─────────────────────────┘
                                    ↓
                    {project_name}_audit/
                    ├── route_mapper/
                    ├── route_tracer/
                    ├── sql_audit/
                    ├── auth_audit/
                    ├── file_upload_audit/
                    ├── file_read_audit/
                    ├── xxe_audit/
                    └── vuln_report/
```

**项目路径要求：**
- 源码项目：包含 `src/main/java` 等源码目录
- 编译项目：包含 `WEB-INF/classes` 或 .jar 文件
- 支持同时存在源码和编译文件的情况，优先使用源码

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
