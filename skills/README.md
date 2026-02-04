# Skills 详细说明

## java-route-mapper

**Java Web 源码路由与参数映射分析工具**

适用场景：
- 无 API 文档的项目进行接口梳理
- 生成 Burp Suite 测试请求模板
- 分析源码中的可访问端点

**支持框架：**
- Spring MVC / Spring Boot
- Servlet（web.xml、@WebServlet）
- JAX-RS（@Path、@GET、@POST 等）
- Struts 2
- CXF Web Services

**核心功能：**
1. 自动识别项目类型和框架
2. 扫描并提取 HTTP 路由（@Controller、@RequestMapping 等）
3. 解析参数结构（Path 变量、Query 参数、Body 参数、Header 参数、Cookie 参数）
4. 支持 .class 和 .jar 文件的反编译分析
5. 生成标准 HTTP 请求模板

**使用示例：**

```
输入: 项目源码路径
输出: 完整的路由清单和 Burp Suite 请求模板

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

---

## java-auth-audit

**Java Web 源码鉴权机制审计工具**

适用场景：
- 识别项目中使用的鉴权框架和实现方式
- 发现鉴权绕过漏洞
- 分析越权访问风险
- 审计权限校验逻辑

**支持框架：**
- Spring Security
- Apache Shiro
- JWT 鉴权
- Session 鉴权
- Filter/Interceptor 拦截器
- 自定义鉴权实现

**核心功能：**
1. 自动识别鉴权框架类型和版本
2. 提取鉴权配置和拦截规则
3. 分析鉴权绕过模式（URL 解析绕过、权限校验绕过等）
4. 识别越权访问风险（IDOR、水平/垂直越权）
5. 检测框架版本已知漏洞
6. 支持 .class 和 .jar 文件的反编译分析

**使用示例：**

```
输入: 项目源码路径
输出: 鉴权机制分析报告、漏洞发现清单

=== 鉴权框架识别 ===
框架: Spring Security
版本: 5.7.2

=== 鉴权配置 ===
SecurityFilterChain: /api/public/** = permitAll()
SecurityFilterChain: /api/admin/** = hasRole('ADMIN')

=== 潜在漏洞 ===
[高危] URI 解析绕过漏洞
  位置: SecurityConfig.java:45
  说明: 使用 regexMatcher() 可能导致 /admin/. 接口绕过鉴权

[高危] IDOR 越权漏洞
  位置: UserController.getUserById (UserController.java:78)
  说明: /api/user/{id} 接口缺少所有权校验，可能访问其他用户数据
```

---

## java-vuln-scanner

**Java 组件版本漏洞检测工具**

适用场景：
- Java 项目依赖安全审计
- 识别 Log4j、Fastjson、Shiro、Spring 等高危组件漏洞
- jar 包反编译后的依赖分析

**支持输入：**
- pom.xml - Maven 项目
- build.gradle - Gradle 项目
- .jar 文件 - 从文件名或 META-INF 提取依赖信息
- 目录 - 递归扫描，自动按模块分组

**漏洞规则覆盖（130+ CVE）：**

| 组件类别 | 主要漏洞 |
|---------|---------|
| Log4j | CVE-2021-44228 (Log4Shell), CVE-2021-45046 |
| Fastjson | CVE-2022-25845, CVE-2017-18349 |
| Spring | CVE-2022-22965 (Spring4Shell), CVE-2022-22963 |
| Struts2 | S2-045, S2-046, S2-057, S2-061 |
| Shiro | CVE-2016-4437, CVE-2020-11989, CVE-2020-17510 |
| Jackson | CVE-2020-36518, CVE-2019-12384 |
| XStream | CVE-2021-39144 等 15 个 CVE |
| ActiveMQ | CVE-2023-46604 |

**核心功能：**
1. 扫描项目依赖，匹配已知 CVE 规则
2. 按模块分组输出，按严重级别分类
3. AI 自动生成漏洞触发点分析
4. 支持 .class 和 .jar 文件的反编译分析

**使用示例：**

```
输入: 项目源码路径
输出: 漏洞扫描报告

📊 扫描摘要:
   模块数量: 4
   依赖总数: 262
   漏洞总数: 80
   🔴 严重: 24

=== 漏洞详情 ===
🔴 Critical - log4j-core 2.14.1
   CVE-2021-44228 (Log4Shell)
   影响: 远程代码执行
   修复版本: >= 2.17.1
```

---

## 输出目录结构

三个技能的输出统一到 `{项目名}_audit/` 目录下：

```
{project_name}_audit/
├── route_mapper/      # java-route-mapper 输出
├── auth_audit/        # java-auth-audit 输出
└── vuln_report/       # java-vuln-scanner 输出
```
