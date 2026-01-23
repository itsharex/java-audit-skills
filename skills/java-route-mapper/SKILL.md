---
name: java-route-mapper
description: Java Web 源码路由与参数映射分析工具。当需要从 Java Web 项目源码中提取 HTTP 路由结构和请求参数时使用：(1) 无 API 文档的项目进行接口梳理，(2) 生成 Burp Suite 测试请求模板，(3) 分析源码中的可访问端点。支持 Spring MVC、Servlet、JAX-RS 等主流框架。
---

# Java Source Route & Parameter Mapper

分析 Java Web 项目源码，提取完整的 HTTP 路由与请求参数结构，生成 Burp Suite Repeater 请求模板。

## 工作流程

### 1. 项目分析初始化

```
输入: 项目源码路径
       可选: 项目上下文路径、已知框架信息
```

**初始化步骤：**

1. 识别项目类型和框架（通过配置文件和目录结构）
2. 确定路由加载方式（注解驱动 / XML 配置 / 混合）
3. 提取上下文路径和基础 URL

### 2. 路由枚举

扫描项目源码，提取所有对外可访问的 HTTP 路由。

**扫描范围：**
- `@Controller` / `@RestController` 类
- `@RequestMapping` 及其变体注解
- Servlet 配置（web.xml、@WebServlet）
- JAX-RS 注解（@Path、@GET、@POST 等）

**输出信息：**
- HTTP 方法
- URL 路径（完整路径）
- 对应的控制器类和方法

### 3. 参数结构解析

对每个路由解析其参数结构。

**参数来源：**
- **Path 变量**：`@PathVariable`、`@PathParam`
- **Query 参数**：`@RequestParam`、`@QueryParam`
- **Body 参数**：`@RequestBody`、请求对象、Form 表单
- **Header 参数**：`@RequestHeader`、`@HeaderParam`
- **Cookie 参数**：`@CookieValue`、`@CookieParam`

**参数类型分析：**
- 基本类型（String、int、long 等）
- 对象类型（POJO）
- 集合类型（List、Map、Set）
- 枚举类型

### 4. 反编译支持（必要时）

当接口定义或方法签名位于已编译的 .class 文件或第三方 JAR 中时：

1. 使用 MCP Java Decompiler 工具反编译目标文件
2. 提取方法签名和参数类型定义
3. 还原参数结构

**反编译策略：**
- 仅反编译包含目标接口或参数定义的类
- 优先使用已存在的源码
- 记录反编译来源以便追溯

### 5. 生成输出

为每个接口生成标准 HTTP 请求模板。

**输出格式（每条）：**

```
=== [序号] 接口标识 ===

描述: 简要描述（如有注解描述）
位置: ClassName.methodName (源文件:行号)

HTTP 方法: GET/POST/PUT/DELETE 等
URL 路径: /完整/路径/结构

参数结构:
  Path: {pathVar1}, {pathVar2}
  Query: param1, param2 (类型: String)
  Body: ContentType (类型定义)
  Header: X-Custom-Header
  Cookie: sessionId

Burp Suite 请求模板:
---
HTTP_METHOD /path/structure HTTP/1.1
Host: {{host}}
Content-Type: application/json
[其他必需 Header]

[请求 Body]
---
```

## 框架支持

### 主流框架（自动识别）

| 框架 | 识别特征 | 参考资料 |
|------|---------|---------|
| Spring MVC | `@Controller`、`@RequestMapping` | [SPRING_MVC.md](references/SPRING_MVC.md) |
| Spring Boot | `application.properties/yml`、Spring Boot starter | [SPRING_MVC.md](references/SPRING_MVC.md) |
| Servlet | `web.xml`、`@WebServlet` | [SERVLET.md](references/SERVLET.md) |
| JAX-RS | `@Path`、`@GET`、`@POST` | [JAXRS.md](references/JAXRS.md) |
| Struts 2 | `struts.xml` | [STRUTS.md](references/STRUTS.md) |

**非主流/自定义框架：** 按照配置文件模式分析，参见 [FRAMEWORK_PATTERNS.md](references/FRAMEWORK_PATTERNS.md)

## 工具使用

### MCP Java Decompiler

```bash
# 检查 CFR 反编译器状态
mcp__java-decompile-mcp__check_cfr_status()

# 获取当前系统的 Java 版本信息
mcp__java-decompile-mcp__get_java_version()

# 下载 CFR 反编译器到指定目录
mcp__java-decompile-mcp__download_cfr_tool(target_dir)

# 反编译单个 .class 或 .jar 文件
mcp__java-decompile-mcp__decompile_file(
  file_path,
  output_dir,      # 输出目录，默认为文件所在目录下的 decompiled 文件夹
  save_to_file     # 是否直接保存到文件系统(推荐)，默认为 True。设为 False 时会返回反编译内容
)

# 反编译指定目录下的所有 .class 和 .jar 文件(支持多线程)
mcp__java-decompile-mcp__decompile_directory(
  directory_path,
  output_dir,      # 输出目录，默认为目标目录下的 decompiled 文件夹
  recursive,       # 是否递归扫描子目录，默认为 True
  save_to_file,    # 是否直接保存到文件系统(推荐)，默认为 True
  show_progress,   # 是否显示详细进度信息，默认为 True
  max_workers      # 最大并发线程数，默认为 4(设为 1 则单线程处理)
)

# 反编译多个 .class 或 .jar 文件(支持多线程)
mcp__java-decompile-mcp__decompile_files(
  file_paths,
  output_dir,      # 输出目录，默认为当前目录下的 decompiled 文件夹
  save_to_file,    # 是否直接保存到文件系统(推荐)，默认为 True
  show_progress,   # 是否显示详细进度信息，默认为 True
  max_workers      # 最大并发线程数，默认为 4(设为 1 则单线程处理)
)
```

## 限制与边界

**仅执行以下操作：**
- 从源码/反编译结果中提取已有的路由定义
- 解析已声明的参数结构
- 生成 HTTP 请求模板

**不执行以下操作：**
- 不进行漏洞分析或安全风险判断
- 不推断接口业务逻辑或行为
- 不编造不存在的路由或参数
- 不推断默认值或可选性（除非明确标注）

## 最佳实践

1. **优先源码**：仅在必要时使用反编译
2. **记录来源**：标注每个路由的源文件位置
3. **保持一致**：输出格式统一，便于后续处理
4. **渐进式输出**：边分析边输出，避免长时间等待
5. **错误处理**：遇到无法解析的配置时记录并跳过

## 示例输出

```
=== [1] 用户登录 ===

位置: UserController.login (src/main/java/com/example/controller/UserController.java:45)

HTTP 方法: POST
URL 路径: /api/auth/login

参数结构:
  Body: LoginRequest (username: String, password: String)

Burp Suite 请求模板:
---
POST /api/auth/login HTTP/1.1
Host: {{host}}
Content-Type: application/json

{"username": "{{username}}", "password": "{{password}}"}
---
```

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| 无法识别框架 | 检查项目根目录的配置文件，参考 [FRAMEWORK_PATTERNS.md](references/FRAMEWORK_PATTERNS.md) |
| 路由路径不完整 | 检查类级别的 `@RequestMapping` 和上下文路径配置 |
| 参数类型未知 | 使用反编译工具获取完整的类型定义 |
| 生成的请求无法访问 | 确认未受安全拦截器/过滤器限制 |
