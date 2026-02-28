---
name: java-audit-pipeline
description: Java Web 全链路自动化安全审计流水线。使用 agent team 编排多个审计 skill，自动完成路由分析→鉴权审计→组件漏洞→交叉筛选→调用链追踪→漏洞深度分析→质量校验的完整流程。适用于：(1) 一键启动 Java 项目全量安全审计，(2) 自动识别无鉴权高危路由并精准分析漏洞，(3) 基于调用链的精准漏洞审计（减少误报），(4) 自动校验每个 skill 输出质量。用户只需提供源码路径和输出路径。注意：此 skill 依赖 Claude Code agent teams 功能，需在配置文件 `~/.claude/settings.json` 的 `env` 中添加 `"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"` 开启。
---

# Java 全链路审计流水线

使用 agent team 编排 7 个 agent，分 5 个阶段自动完成 Java Web 项目的完整安全审计。

## 输入

用户提供：
- **source_path**: 源码目录路径
- **output_path**: 输出目录路径（默认 `{source_path}_audit`）

## 流程总览

```
阶段1: 信息收集（agent-1/2/3 并行）
  ├─ agent-1: /java-route-mapper   → 全量路由+参数  → agent-7 立即校验
  ├─ agent-2: /java-auth-audit     → 路由鉴权映射    → agent-7 立即校验
  └─ agent-3: /java-vuln-scanner   → 组件漏洞        → agent-7 立即校验
        ↓ 三个校验全部通过后
阶段2: 交叉分析（agent-4）
  └─ 筛选无鉴权+有漏洞触发点的高危路由
        ↓ agent-7 校验
阶段3: 调用链追踪（agent-5）
  └─ /java-route-tracer 追踪高危路由参数流向
        ↓ agent-7 校验
阶段4: 漏洞深度分析（agent-6）
  └─ 根据调用链 sink 类型选择对应漏洞 skill
        ↓ agent-7 校验
阶段5: 汇总报告（agent-7）
  └─ 整合所有校验结果，生成最终 quality_report.md
```

**关键设计：agent-7 在每个阶段完成后立即校验，不合格则通知重做，避免错误传递到下游。**

## 执行指令

### 团队负责人职责

1. 解析用户输入的 source_path 和 output_path
2. 创建输出目录结构（一次性创建所有子目录）：
   ```bash
   mkdir -p {output_path}/route_mapper {output_path}/auth_audit {output_path}/vuln_report {output_path}/route_tracer {output_path}/sql_audit {output_path}/xxe_audit {output_path}/file_upload_audit {output_path}/file_read_audit
   ```
3. 创建 agent team
4. 使用 TaskCreate 创建 7 个 agent 任务并设置依赖：

```
task-1:  agent-1 路由分析           (pending)
task-2:  agent-2 鉴权分析           (pending)
task-3:  agent-3 组件漏洞扫描       (pending)
task-4:  agent-7 校验 agent-1       (blockedBy: [1])
task-5:  agent-7 校验 agent-2       (blockedBy: [2])
task-6:  agent-7 校验 agent-3       (blockedBy: [3])
task-7:  agent-4 交叉分析           (blockedBy: [4,5,6])
task-8:  agent-7 校验阶段2          (blockedBy: [7])
task-9:  agent-5 调用链追踪         (blockedBy: [8])
task-10: agent-7 校验阶段3          (blockedBy: [9])
task-11: agent-6 漏洞深度分析       (blockedBy: [10])
task-12: agent-7 校验阶段4+汇总     (blockedBy: [11])
```

5. agent-1/2/3 并行分配，每个完成后负责人立即触发 agent-7 校验该 agent 的输出，不合格则通知重做；三个校验全部通过后 agent-4 才启动

### 通用执行要求（传递给每个 agent）

```
执行要求：
1. 输出目录已由负责人预先创建，禁止自行创建或修改目录结构，直接写入指定目录
2. 先探索源代码目录结构，了解项目的模块组成、技术栈和代码分布
3. 根据探索结果，使用 TaskCreate 自行规划详细的 todo 子任务列表
4. 按照你规划的任务列表逐项执行，每完成一项用 TaskUpdate 标记为 completed
5. 全部完成后，自查输出文件的完整性和数量，确认无遗漏后通知团队负责人
全程自主规划、自主执行，无需等待确认。
```

---

## Agent 详细指令

### Agent-1: 路由分析员

```
角色: 路由分析员
技能: /java-route-mapper
源代码: {source_path}
输出目录: {output_path}/route_mapper/（已创建，直接写入）
任务: 提取项目所有 HTTP 路由和参数结构，生成 Burp Suite 请求模板
```

### Agent-2: 鉴权分析员

```
角色: 鉴权分析员
技能: /java-auth-audit
源代码: {source_path}
输出目录: {output_path}/auth_audit/（已创建，直接写入）
任务: 识别鉴权框架，分析每条路由的鉴权状态，检测鉴权绕过漏洞
```

### Agent-3: 组件扫描员

```
角色: 组件扫描员
技能: /java-vuln-scanner
源代码: {source_path}
输出目录: {output_path}/vuln_report/（已创建，直接写入）
任务: 扫描项目依赖中的已知漏洞（CVE），生成触发点分析
```

### Agent-4: 交叉分析员

```
角色: 交叉分析员
等待: agent-1、agent-2、agent-3 全部完成
输出: {output_path}/high_risk_routes.md
```

**执行步骤：**

1. 读取 agent-2 鉴权映射表，提取 ❌无鉴权 和 ⚠️仅认证 的路由
2. 读取 agent-3 漏洞报告，提取有漏洞组件的触发点
3. 读取 agent-1 路由列表，获取完整参数结构
4. 交叉匹配生成高危路由清单，按优先级排序：

| 优先级 | 条件 |
|:-------|:-----|
| P0 | ❌无鉴权 + 有漏洞组件触发点 |
| P1 | ❌无鉴权 + 无已知组件漏洞 |
| P2 | ⚠️仅认证 + 有漏洞组件触发点 |
| P3 | ⚠️仅认证 + 无已知组件漏洞 |

**输出 `high_risk_routes.md` 包含：**
- 按优先级分组的路由表格（路由、方法、鉴权状态、关联漏洞、参数）
- 「建议追踪路由列表」— 供 agent-5 使用

### Agent-5: 调用链追踪员

```
角色: 调用链追踪员
等待: agent-4 完成
技能: /java-route-tracer
源代码: {source_path}
输出目录: {output_path}/route_tracer/（已创建，直接写入）
输入: {output_path}/high_risk_routes.md 中的「建议追踪路由列表」
任务: 按 P0→P1→P2 优先级逐条追踪调用链
```

### Agent-6: 漏洞审计员

```
角色: 漏洞审计员
等待: agent-5 完成
源代码: {source_path}
输出目录: {output_path}/（各子目录已创建：sql_audit/、xxe_audit/、file_upload_audit/、file_read_audit/，直接写入对应目录）
输入: {output_path}/route_tracer/ 下所有调用链报告
```

**执行步骤：**

1. 遍历所有调用链报告，识别最终使用点（sink）类型
2. 根据 sink 类型选择对应 skill：

| Sink 类型 | 特征 | Skill |
|:----------|:-----|:------|
| SQL 拼接 | `Statement.execute()`, `sql +`, MyBatis `${}` | `/java-sql-audit` |
| XML 解析 | `DocumentBuilder.parse()`, `SAXParser` | `/java-xxe-audit` |
| 文件上传 | `MultipartFile`, `transferTo()` | `/java-file-upload-audit` |
| 文件读取 | `BufferedReader`, `Files.read` | `/java-file-read-audit` |

3. 基于调用链做精准分析（非全量扫描），减少误报
4. 一条调用链有多种 sink 时分别执行对应 skill

### Agent-7: 检查员（CRITICAL — 贯穿全流程）

```
角色: 质量检查员（常驻）
校验依据: 使用 Skill 工具加载对应 skill（如 /java-route-mapper），从加载的 skill 上下文中提取输出规范作为校验标准
输出: {output_path}/quality_report.md
工作模式: 每个阶段完成后立即校验，不合格则通知对应 agent 重做
```

**核心原则：每个阶段的输出必须通过校验后，才允许下一阶段启动。避免错误数据传递到下游。**

#### 校验触发时机

| 触发点 | 校验对象 | 不合格处理 |
|:-------|:---------|:-----------|
| agent-1 完成后 | java-route-mapper 输出 | 通知 agent-1 重做 |
| agent-2 完成后 | java-auth-audit 输出 | 通知 agent-2 重做 |
| agent-3 完成后 | java-vuln-scanner 输出 | 通知 agent-3 重做 |
| agent-4 完成后 | `high_risk_routes.md` | 通知 agent-4 重做，阻塞 agent-5 |
| agent-5 完成后 | route_tracer 所有输出 | 通知 agent-5 补充，阻塞 agent-6 |
| agent-6 完成后 | 漏洞审计 skill 所有输出 | 通知 agent-6 补充 |
| 全部通过后 | 跨 skill 数据一致性 | 生成最终 quality_report.md |

#### 通用校验方法

每次校验时：
1. 使用 Skill 工具加载被校验 agent 对应的 skill（如 `/java-route-mapper`），从 skill 上下文中提取输出规范作为校验标准
2. 读取实际输出文件
3. 逐项检查：文件存在性、章节完整性、内容非空、格式规范
4. 不合格 → 通知对应 agent 具体缺失项，要求补充
5. 合格 → 通知负责人启动下一阶段

#### 阶段1 校验（每个 agent 完成后立即独立校验）

**校验 agent-1（java-route-mapper）：**
- 检查：路由列表表格、参数结构、Burp Suite 请求模板、文件位置标注
- 不合格 → 通知 agent-1 补充

**校验 agent-2（java-auth-audit）：**
- 检查：鉴权框架识别、组件版本分析、路由鉴权映射表（✅/⚠️/❌）、风险统计、高危详情+PoC
- **关键**：映射表路由数 vs agent-1 路由总数，覆盖率 < 80% 则不合格
- 不合格 → 通知 agent-2 补充遗漏路由

**校验 agent-3（java-vuln-scanner）：**
- 检查：扫描概览、模块风险摘要、漏洞详情（CVE）、触发点分析章节
- 不合格 → 通知 agent-3 补充

**三个都通过 → 通知负责人启动 agent-4**

#### 阶段2 校验（agent-4 完成后）

- 检查 `high_risk_routes.md` 存在且非空
- 检查优先级分组表格（P0/P1/P2/P3）存在
- 检查「建议追踪路由列表」存在且有内容
- 交叉验证：P0 路由同时满足"无鉴权"+"有漏洞触发点"
- 通过 → 通知负责人启动 agent-5

#### 阶段3 校验（agent-5 完成后）

- 逐文件检查：HTTP数据包、层级调用链、参数追踪表、执行路径结论
- **特殊检查**：grep 所有文件中的 `${`，发现未替换变量则不合格
- 文件数量 = 方法数 + 1（总索引）
- 追踪覆盖率：已追踪数 / high_risk 建议追踪数 >= 90%
- 通过 → 通知负责人启动 agent-6

#### 阶段4 校验（agent-6 完成后）

- 根据实际执行的 skill 类型，使用 Skill 工具加载对应 skill（如 `/java-sql-audit`），从 skill 上下文中提取输出规范，逐项检查
- 审计覆盖率：已审计调用链数 / 有 sink 的调用链总数 >= 90%
- 通过 → 进入最终汇总

#### 最终汇总：生成 `quality_report.md`

整合所有阶段的校验结果：

```markdown
# 审计质量检查报告

## 总览
| 阶段 | Skill | 状态 | 通过项/总项 | 重做次数 |
|:-----|:------|:-----|:-----------|:---------|

## 各阶段校验详情

### 阶段1
- ✅ java-route-mapper: 4/4 项通过
- ❌→✅ java-auth-audit: 首次 5/7，补充后 7/7（重做1次）
- ✅ java-vuln-scanner: 6/6 项通过

### 阶段2
- ✅ 交叉分析: high_risk_routes.md 校验通过

### 阶段3
- ✅ java-route-tracer: 10/10 项通过

### 阶段4
- ✅ java-sql-audit: 4/4 项通过

## 数据一致性
| 校验项 | 实际值 | 阈值 | 状态 |
|:-------|:-------|:-----|:-----|
| 路由覆盖率 | 85% | 80% | ✅ |
| 高危路由追踪率 | 100% | 90% | ✅ |
| 漏洞审计覆盖率 | 95% | 90% | ✅ |

## 审计统计汇总
| 指标 | 数量 |
|:-----|:-----|
| 总路由数 | |
| 无鉴权路由数 | |
| 组件漏洞数 | |
| 高危路由数 | |
| 已追踪调用链数 | |
| 发现代码漏洞数 | |
```

---

## 输出目录结构

```
{output_path}/
├── route_mapper/              # 阶段1 - agent-1
├── auth_audit/                # 阶段1 - agent-2
├── vuln_report/               # 阶段1 - agent-3
├── high_risk_routes.md        # 阶段2 - agent-4
├── route_tracer/              # 阶段3 - agent-5
├── sql_audit/                 # 阶段4 - agent-6
├── xxe_audit/                 # 阶段4 - agent-6
├── file_upload_audit/         # 阶段4 - agent-6
├── file_read_audit/           # 阶段4 - agent-6
└── quality_report.md          # 阶段5 - agent-7
```

## Skill 输出规范引用

agent-7 校验时使用 Skill 工具加载对应 skill 获取输出规范：

| 校验对象 | 加载 Skill |
|:---------|:-----------|
| agent-1 输出 | `/java-route-mapper` |
| agent-2 输出 | `/java-auth-audit` |
| agent-3 输出 | `/java-vuln-scanner` |
| agent-5 输出 | `/java-route-tracer` |
| agent-6 输出（按 sink 类型） | `/java-sql-audit`、`/java-xxe-audit`、`/java-file-upload-audit`、`/java-file-read-audit` |
