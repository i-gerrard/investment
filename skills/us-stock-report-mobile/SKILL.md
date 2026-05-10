---
name: us-stock-report-mobile
description: 手机端（iPhone）每日美股持仓分析报告。通过预配置的 iOS 快捷指令自动提取 eToro + Trade Republic 持仓数据，调用市场分析 Skills，生成结构化投资分析报告并内联输出至对话。每天至少运行一次，通常在美股收盘后。
allowed-tools: Read, Write, WebSearch, WebFetch, Bash
---

# US Stock Daily Report（手机端 / iPhone）

## Overview

每日美股收盘后执行。与桌面端的区别：

| 项目 | 桌面端 | 手机端（本 Skill） |
|------|--------|-----------------|
| 持仓数据获取 | Playwright 自动登录 eToro + TR | iOS 快捷指令一键提取 |
| 用户操作 | 完成 2FA 登录 | 运行快捷指令 + 粘贴数据 |
| 报告保存 | `~/Desktop/claude/{date}/report-{date}.html` | 内联输出至对话 |

**每日使用流程（首次配置后）：**
1. 运行 iOS 快捷指令（一键）→ 数据自动复制到剪贴板
2. 切换到 Claude，将剪贴板内容粘贴至对话
3. Claude 自动执行 Step 0–4b，生成完整报告

---

## 初次配置：iOS 快捷指令设置（仅需一次）

> 告知用户：首次使用前须完成以下配置步骤，约需 10 分钟。

### 配置前提

- iPhone 已安装"快捷指令"App（iOS 系统自带）
- Safari 中已登录 eToro 网页版（`https://www.etoro.com`）
- Safari 中已登录 Trade Republic 网页版（`https://app.traderepublic.com`）
- 两个网站保持"记住登录状态"（勿使用无痕模式）

### 创建快捷指令步骤

在"快捷指令"App 中新建一个快捷指令，依次添加以下动作：

---

**动作 1：提取 eToro 持仓数据**

动作类型：`Safari - 在网页上运行 JavaScript`
URL：`https://www.etoro.com/portfolio/`

JavaScript 内容：
```javascript
(function() {
  // 账户摘要
  var equity = document.querySelector('[automation-id="portfolio-overview-total-equity"]')?.innerText?.trim() || '';
  var todayPL = document.querySelector('[automation-id="portfolio-overview-daily-profit"]')?.innerText?.trim() || '';
  var cash = document.querySelector('[automation-id="portfolio-overview-available"]')?.innerText?.trim() || '';

  // 持仓行
  var rows = Array.from(document.querySelectorAll('[automation-id="portfolio-grid-row"]'));
  var positions = rows.map(function(row) {
    var cells = Array.from(row.querySelectorAll('td, [class*="cell"]'));
    return cells.map(function(c) { return c.innerText.trim(); }).filter(Boolean).join(' | ');
  }).filter(Boolean).join('\n');

  return [
    '--- eToro Account ---',
    'Total Value: ' + equity,
    'Today P&L: ' + todayPL,
    'Cash: ' + cash,
    '',
    'Positions (ticker | price | change% | qty | avg_price | pnl%):',
    positions || '(no positions found - check login status)'
  ].join('\n');
})()
```

将动作输出保存到变量 `etoroData`。

---

**动作 2：提取 Trade Republic 持仓数据**

动作类型：`Safari - 在网页上运行 JavaScript`
URL：`https://app.traderepublic.com/portfolio`

JavaScript 内容：
```javascript
(function() {
  // 账户摘要
  var totalEl = document.querySelector('[data-testid="total-portfolio-value"], [class*="totalValue"], [class*="portfolio-value"]');
  var total = totalEl ? totalEl.innerText.trim() : '';

  var plEl = document.querySelector('[data-testid="portfolio-performance-today"], [class*="dailyChange"], [class*="today"]');
  var todayPL = plEl ? plEl.innerText.trim() : '';

  var cashEl = Array.from(document.querySelectorAll('*')).find(function(el) {
    return el.children.length === 0 && el.innerText && el.innerText.match(/cash|verrechnungskonto/i);
  });
  var cash = cashEl ? cashEl.innerText.trim() : '(check manually)';

  // 持仓行
  var items = Array.from(document.querySelectorAll('[data-testid*="instrument-list-item"], [class*="portfolioInstrument"], [class*="instrument-row"]'));
  var positions = items.map(function(item) {
    return item.innerText.replace(/\n+/g, ' | ').trim();
  }).filter(Boolean).join('\n');

  return [
    '--- Trade Republic Account ---',
    'Total Value: ' + total,
    'Today P&L: ' + todayPL,
    'Cash: ' + cash,
    '',
    'Positions (name | qty | value | pnl):',
    positions || '(no positions found - check login status)'
  ].join('\n');
})()
```

将动作输出保存到变量 `trData`。

---

**动作 3：组合并复制到剪贴板**

动作类型：`文本`

文本内容（将以下内容原样输入，变量用快捷指令"变量"动作插入）：
```
=== US STOCK REPORT DATA ===
Date: [插入"日期"动作，格式 YYYY-MM-DD]

[变量 etoroData]

[变量 trData]
=== END ===
```

动作类型：`复制到剪贴板`（复制上面的文本）

---

**动作 4：完成提示**

动作类型：`显示通知`
标题：`持仓数据已复制`
正文：`请切换到 Claude 并粘贴`

---

**完成后：** 将快捷指令命名为"美股日报数据"，添加到主屏幕或 Lock Screen 快速启动。

### JS 适配说明

eToro 和 TR 的 Web 组件 class 名称可能随版本更新。如果运行后出现 `(no positions found)`：
1. 在 Safari 打开对应页面
2. 长按持仓行 → 检查元素 → 获取实际 class 名
3. 更新快捷指令中对应的 CSS selector

---

## Step 0: 读取前日持仓基准

**执行时机：** 在处理用户粘贴的数据之前。此步骤失败不阻断后续流程，仅跳过变化对比。

### 0a. 定位前日数据

前日数据存储于对话历史。在当前对话中搜索最近一条包含 `=== US STOCK REPORT DATA ===` 标记的历史消息，若找到则提取数据；若对话历史中无此记录，跳过对比。

### 0b. 从前日数据提取持仓数量

从对话历史中定位前日的 `=== US STOCK REPORT DATA ===` 块，提取 eToro 和 TR 的持仓数量，构建字典：

```
prev_etoro = { "NVDA": 50, "MSFT": 37, "TSM": 20, ... }
prev_tr    = { "NVIDIA": 76.260, "AMD": 32.818, ... }
```

### 0c. 对比今昨持仓，生成变化记录

今日持仓数据在 Step 1 完成后获得。完成 Step 1 后立即对比：

- **新建仓**：今日有、昨日无 → `change_type = "NEW"`, `delta = +今日数量`
- **加仓**：今日数量 > 昨日数量 → `change_type = "ADD"`, `delta = +差值`
- **减仓**：今日数量 < 昨日数量 → `change_type = "REDUCE"`, `delta = -差值`
- **持平**：数量相同（允许 ±0.001 浮点误差）→ `change_type = "SAME"`
- **已清仓**：昨日有、今日无 → `change_type = "CLOSED"`, `delta = -昨日数量`

**仅当 `change_type != "SAME"` 时，才需要在报告中 highlight。**

---

## 前置条件：必须收到完整的快捷指令数据

**规则：** 用户粘贴的数据必须同时包含 eToro 和 TR 两个账户的内容，且均无 `(no positions found)` 错误。

- 若任一账户显示 `(no positions found)`：提示用户检查 Safari 是否已登录对应网站，重新运行快捷指令
- 若数据不完整或格式无法识别：告知用户具体缺失的字段，等待用户补充或重新运行
- 不允许只用一个账户数据生成报告

---

## Step 1: 解析快捷指令数据

用户将粘贴以下格式的文本（由 iOS 快捷指令生成）：

```
=== US STOCK REPORT DATA ===
Date: 2026-05-10

--- eToro Account ---
Total Value: $125,432.50
Today P&L: +$2,341.20
Cash: $3,210.00

Positions (ticker | price | change% | qty | avg_price | pnl%):
NVDA | $215.20 | +1.75% | 50 | $163.07 | +31.98%
MSFT | $420.50 | -0.32% | 37 | $380.20 | +10.60%

--- Trade Republic Account ---
Total Value: €45,231.80
Today P&L: +€821.40
Cash: €1,200.00

Positions (name | qty | value | pnl):
NVIDIA | 76.260 | €13,905.31 | +€4,521.18
AMD | 32.818 | €4,200.50 | +€890.20
=== END ===
```

**解析步骤：**

1. 确认 `=== US STOCK REPORT DATA ===` 和 `=== END ===` 标记存在
2. 提取 eToro 账户摘要（Total Value / Today P&L / Cash）
3. 逐行解析 eToro 持仓，容错：字段分隔符可能是 ` | ` 或多个空格或 tab
4. 提取 TR 账户摘要
5. 逐行解析 TR 持仓
6. 若字段解析有歧义，尽力推断；实在无法确定时询问用户一个具体问题

**EUR/USD 汇率：** 快捷指令不提供汇率，统一通过 `WebSearch "EUR USD exchange rate today"` 自动获取。

**解析完成后构建内存数据结构，立即进入 Step 0c 对比变化，然后进入 Step 2。**

---

## Step 2: 市场信息采集

Step 1 完成后立即执行，分三层：必选 Skills → 可选 Skills → 直接搜索补充。

### 2a. 必选 Skills（每次运行，并行调用）

| Skill | 调用目的 | 输出用途 |
|-------|---------|---------|
| `market-breadth-analyzer` | 市场广度 0–100 评分 | 写入报告标题副栏 + ⚠️ 风险 banner |
| `market-top-detector` | 市场顶部概率 0–100 | 写入 ⚠️ 风险 banner，≥60 触发减仓警告 |
| `sector-analyst` | 板块轮动分析 | 填充各板块 stock-card 的板块背景描述 |
| `earnings-calendar` | 持仓股未来 7 天财报日 | 填充"近期重要事件"表，stock-card 加"⚡ 今晚财报"标签 |
| `economic-calendar-fetcher` | 未来 7 天宏观事件 | 填充"近期重要事件"表 |

**调用方式：** 在 Step 1 完成后立即并行触发全部 5 个 skill，等待所有结果后进入 2b。

### 2b. 可选 Skills（按当日情况决定）

| Skill | 调用条件 | 输出用途 |
|-------|---------|---------|
| `market-news-analyst` | 每次运行（推荐）或有重大新闻事件 | 填充 ⚡ 催化剂 banner，补充当日最重要新闻 |
| `theme-detector` | 每次运行（推荐） | 补充 ⚡ 催化剂 banner 的主题叙事 |
| `exposure-coach` | 每次运行（推荐） | 生成净敞口姿态摘要，嵌入"操作建议汇总"顶部 |
| `institutional-flow-tracker` | 持仓中有单日 ±5% 以上大波动的股票时 | 补充对应 stock-card 的多头/空头分析 |
| `earnings-trade-analyzer` | 持仓股当日刚发布财报时 | 对财报反应评分，嵌入对应 stock-card |
| `market-environment-analysis` | WebSearch 不可用时作为全量替代 | 替代 2c 的全部 WebSearch 内容 |

### 2c. WebSearch 直接搜索（补充剩余数据）

skill 调用完成后，用 WebSearch 并行补充以下内容（skill 已覆盖的部分跳过）：

1. `"US stock market {date} S&P 500 Nasdaq close"` — 指数收盘数据
2. `"NVDA AMD AAPL MSFT GOOG META AMZN stock price {date}"` — 重仓股当日涨跌
3. 如果 earnings-calendar skill 未执行：`"earnings calendar this week {date}"` — 财报日期
4. 如果 economic-calendar-fetcher skill 未执行：`"economic calendar this week FOMC CPI"` — 宏观事件

### 2d. 全量兜底：WebSearch 和 Skills 均不可用

仅当 WebSearch 返回错误且所有 skill 均失败时启用，使用 `WebFetch` 抓取以下 URL：

- `https://finance.yahoo.com/quote/%5EGSPC/` → S&P 500
- `https://finance.yahoo.com/quote/%5EIXIC/` → Nasdaq
- `https://finance.yahoo.com/quote/{TICKER}/` → 各持仓标的
- `https://finance.yahoo.com/quote/EURUSD=X/` → EUR/USD

无法访问时在报告中标注"数据不可用"。

---

## Step 3: Generate HTML Report

使用与桌面端相同的 HTML 格式和 CSS 规范。报告结构必须包含以下部分：

### 报告内容结构

1. **标题与副标题**
   - 报告日期 + 星期
   - EUR/USD 汇率
   - 当天最重要的催化剂（用 ⚡ 标注）——来源：`market-news-analyst` + `theme-detector` 输出
   - 最紧急的风险提示（用 ⚠️ 标注）——嵌入 `market-top-detector` 分数
   - 市场广度摘要（一行）

2. **数据来源验证 banner** — 确认数据已从 iOS 快捷指令获取（注明：eToro + TR Safari 网页）

3. **持仓变化对比 banner**

   - 若有前日数据：展示完整变化对比表（`change_type != SAME` 的行）
   - 若无前日数据：显示"⚪ 无前日数据，跳过持仓对比"

   变化对比表、stock-card inline badge 规范与桌面端完全相同。

4. **操作指令 banner**（如果有紧急操作建议）

5. **上次建议执行对比 table**

6. **账户概览**
   - eToro 账户卡片：总净值、今日 P&L、现金余额、已投资金额、现金占比、全部持仓表格
   - TR 账户卡片：总净值、今日 P&L、现金余额（€）、已投资金额（€）、现金占比、全部持仓表格
   - 两账户合计：合并总净值（USD）、合并现金（USD）、合并已投资（USD）、合并现金占比（%）

   **现金占比阈值颜色：**
   - < 3%：现金极危 🔴 / 3–8%：现金偏低 🟡 / 8–20%：现金充足 🟢 / > 20%：现金过高 ⚪

7. **持仓分析（按板块分组）**
   - AI 芯片/半导体：NVDA, TSM, AMD, MU, AVGO
   - 大型科技/云计算：AAPL, MSFT, META, AMZN, GOOG
   - 消费科技/金融/存储：TSLA, WDC, GS
   - ETF/收益型/其他：VOO, JEPQ, JEPI, CRISPR, IUIT, CNDX, NFLX

8. **每个 stock-card**：header（ticker + 公司名 + 特殊标签）、meta、verdict badge、targets、多头/空头分析、结论

9. **市场环境摘要**（账户概览之后、持仓分析之前）
   ```
   广度评分：{score}/100 · 顶部风险：{score}/100 · 板块轮动：{领涨} > {领跌}
   仓位姿态：{净敞口上限} · 当前主题：{主题1} · {主题2}
   ```

   market-top-detector 对报告的强制影响：
   - 0–39（安全）：正常，可包含加仓建议
   - 40–59（观察）：⚠️ 黄色，新建仓需额外说明
   - 60–79（警惕）：⚠️ 橙色，暂停新建仓，评估止损
   - 80–100（危险）：⚠️ 红色，触发组合层级减仓评估

10. **操作建议汇总 table**（含 exposure-coach 姿态结论 + 按优先级排列的操作）

11. **近期重要事件**（earnings-calendar + economic-calendar-fetcher 输出）

12. **footer**：报告生成时间、数据来源（iOS 快捷指令 · eToro Safari · TR Safari）

### HTML 样式规范

```css
body: font-family PingFang SC; padding 40px; color #1a1a2e
h1: color #0f3460; border-bottom 3px solid #e94560
h2: color #0f3460; border-left 4px solid #e94560
sector-header: background #16213e
stock-header: background #0f3460
s-bull: background #d4f5e9; color #0a7a4f
s-bear: background #fde8e8; color #c0392b
verdict buy: background #d4f5e9; color #0a7a4f; border-radius 20px
verdict hold: background #fff3cd; color #856404
verdict sell: background #fde8e8; color #c0392b
pnl-pos: color #0a7a4f; font-weight 600
pnl-neg: color #c0392b; font-weight 600
action-banner: background #fff0e8; border 2px solid #e67e22
tonight-box: background #fff8e1; border 2px solid #f39c12
exec-box: background #e8f5e9; border 1px solid #a5d6a7
overview-grid: display grid; 2 columns; gap 16px
account-box: background #f8f9ff; border 1px solid #e0e4f0
stock-card: border 1px solid #e8eaf0; border-radius 8px
analysis-text: border-left 3px solid #0f3460; background #f8f9ff
```

```css
/* 现金区块 */
.cash-row { display:flex; gap:16px; margin-top:8px; font-size:13px; flex-wrap:wrap }
.cash-item { flex:1; min-width:110px }
.cash-item .label { font-size:11px; color:#888 }
.cash-item .value { font-weight:700; font-size:15px }
.cash-ratio-badge { display:inline-block; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:700; margin-top:4px }
.cash-danger  { background:#fde8e8; color:#c0392b }
.cash-low     { background:#fff8e1; color:#856404 }
.cash-ok      { background:#d4f5e9; color:#0a7a4f }
.cash-high    { background:#f0f2fa; color:#555 }

/* 持仓变化对比 */
.diff-table th { background:#2c3e50; }
.diff-new    { background:#d4f5e9; }
.diff-add    { background:#eafaf1; }
.diff-reduce { background:#fef9e7; }
.diff-close  { background:#fde8e8; }
.diff-badge { display:inline-block; padding:2px 10px; border-radius:10px; font-size:11px; font-weight:700; }
.diff-badge-new    { background:#0a7a4f; color:#fff; }
.diff-badge-add    { background:#1e8bc3; color:#fff; }
.diff-badge-reduce { background:#e67e22; color:#fff; }
.diff-badge-close  { background:#c0392b; color:#fff; }
.diff-inline { font-size:11px; padding:2px 8px; border-radius:8px; margin-left:6px; font-weight:700; vertical-align:middle; }
.diff-inline-new    { background:#0a7a4f; color:#fff; }
.diff-inline-add    { background:#1e8bc3; color:#fff; }
.diff-inline-reduce { background:#e67e22; color:#fff; }
.diff-none-banner { background:#f0f2fa; border:1px solid #c7d0f0; border-radius:6px; padding:10px 16px;
                    font-size:13px; color:#555; margin:10px 0; text-align:center; }
```

---

## Step 4: 输出报告（手机端）

手机端不写入本地文件系统，按以下顺序执行：

1. **输出完整 HTML 为代码块**，顶部附提示：
   ```
   📋 报告已生成。长按代码块 → 全选 → 复制，粘贴到备忘录或任意文本编辑器，保存为 report.html，用浏览器打开查看完整报告。
   ```

2. **代码块之后输出纯文本摘要**（方便直接在对话中快速浏览）：
   ```
   ── 今日报告摘要 ──────────────────────
   日期：{date}（{weekday}）  EUR/USD：{rate}
   合并总净值：${total}  现金占比：{cash_ratio}%
   eToro：${etoro_total}  TR：€{tr_total}
   市场：广度 {breadth}/100 · 顶部风险 {top}/100
   最高优先级：
   ① {操作1}
   ② {操作2}
   ──────────────────────────────────────
   ```

---

## Step 4b: 质量保障（报告生成后执行）

### 4b-1. 数据校验 → `data-quality-checker`

将报告 HTML 传入 data-quality-checker，检查价格单位一致性、日期匹配、现金合计、P&L 方向。

若 checker 返回警告，在报告 footer 追加：
```html
<div style="background:#fff8e1;border:1px solid #f39c12;border-radius:6px;padding:8px 14px;margin-top:12px;font-size:12px;">
  ⚠️ 数据质检警告：{checker 返回的警告内容}
</div>
```

### 4b-2. 报告评分 → `report-scorer`

调用 report-scorer 对当日报告打分，结果嵌入报告第五节。

**4b 整体失败处理：** 若两个 skill 均失败，跳过 4b，不影响主报告。

---

## 注意事项

### 投资哲学（生成建议时必须遵循）
- **长期主义 + 复利最大化**：持有优质赢家，让复利滚动；不以"锁利"为目标
- 减仓建议必须标注层级：个股层级 或 组合层级
- 以下不是合法减仓理由："涨太多了"、"锁利"、"涨了 X%"
- 每条操作建议必须锚定至少一个估值锚

### 数据安全
- 不得将用户粘贴的持仓数据保存到对话外的任何存储
- iOS 快捷指令的 JS 仅在本地 Safari 执行，不发送数据到外部服务器

### 数据对比逻辑
- **前日数据来源**：当前对话历史中最近一条 `=== US STOCK REPORT DATA ===` 块
- 若无前日数据：显示"⚪ 无前日数据，跳过持仓对比"
- 高亮规则：NEW / ADD / REDUCE / CLOSED（与桌面端相同）

### Skill 调用优先级与降级规则

| 层级 | Skill | 不可用时降级方案 |
|------|-------|--------------|
| 必选 | market-breadth-analyzer | 广度评分留空，注明"数据不可用" |
| 必选 | market-top-detector | 顶部风险评分留空，不触发减仓逻辑 |
| 必选 | sector-analyst | 板块背景描述留空 |
| 必选（需 FMP key） | earnings-calendar | 用 WebSearch 搜索财报日期补充 |
| 必选（需 FMP key） | economic-calendar-fetcher | 用 WebSearch 搜索宏观日历补充 |
| 可选 | market-news-analyst | 用 WebSearch 新闻搜索替代 |
| 可选 | theme-detector | 催化剂 banner 仅用新闻概括 |
| 可选 | exposure-coach | 操作建议不含姿态行 |
| 可选 | institutional-flow-tracker | 对应 stock-card 不含机构资金行 |
| 质量 | data-quality-checker | 静默跳过，不影响主报告 |
| 质量 | report-scorer | 静默跳过，报告无评分节 |

### 推荐操作原则
- 现金占比 < 3%：现金极危，不得加仓
- 现金占比 3–8%：仅执行高确定性操作
- 现金占比 8–20%：正常区间，可按计划加仓
- 现金占比 > 20%：现金过高，考虑择机部署
- 财报前不追高、不盲目止损
- 低于均价的持仓标记为"等待修复"
- 浮盈超过 +30% 的持仓考虑是否止损需要上移
