---
name: us-stock-report
description: 每日美股持仓分析报告。登录 eToro 和 Trade Republic 读取实时持仓，生成结构化投资分析 HTML 报告。每天至少运行一次，通常在美股收盘后。
allowed-tools: Read, Write, WebSearch, WebFetch, Edit, Bash, mcp__playwright__*
---

# US Stock Daily Report

## Overview

每日美股收盘后执行。流程：
1. **读取前日报告**，提取昨日持仓数量作为对比基准
2. 同时登录 eToro + Trade Republic 读取实时持仓数据
3. 搜索当日市场信息（板块轮动、重要财报、宏观事件）
4. 对比今昨持仓数量，生成变化高亮
5. 生成结构化 HTML 投资分析报告
6. 保存到 `~/Desktop/claude/{date}/report-{date}.html`

---

## Step 0: 读取前日持仓基准

**执行时机：** 登录任何账户之前。此步骤失败不阻断后续流程，仅跳过变化对比。

### 0a. 定位前日报告

```bash
# 计算前一个交易日（跳过周末：若今天是周一取周五，其余取昨天）
today=$(date +%Y-%m-%d)
dow=$(date +%u)   # 1=Mon … 7=Sun
if [ "$dow" = "1" ]; then prev=$(date -v-3d +%Y-%m-%d 2>/dev/null || date -d "3 days ago" +%Y-%m-%d)
else prev=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d); fi
echo "前日日期: $prev"
ls ~/Desktop/claude/$prev/report-$prev.html 2>/dev/null && echo "FOUND" || echo "NOT_FOUND"
```

- 若文件 **NOT_FOUND**：跳过 Step 0，报告中持仓变化列全部显示"—（无前日数据）"
- 若文件 **FOUND**：执行 0b

### 0b. 从前日 HTML 提取持仓数量

用 `Read` 工具读取前日报告，在 HTML 中定位两类持仓数据：

**eToro 持仓行格式（参考）：**
```html
<tr><td><b>NVDA</b></td><td>$215.20</td><td ...>+1.75%</td><td>50</td><td>$163.07</td>...
```
第 4 列 `<td>` 即为持仓数量（整数或小数）。

**TR 持仓行格式（参考）：**
```html
<tr><td><b>NVIDIA</b></td><td>76.260</td><td>13,905.31€</td>...
```
第 2 列 `<td>` 即为持仓量。

提取后构建前日持仓字典（在工作记忆中保存）：
```
prev_etoro = { "MSFT": 37, "NVDA": 50, "TSM": 20, "META": 13, ... }
prev_tr    = { "NVIDIA": 76.26, "AMD": 32.818, "Tesla": 28.18, ... }
```

**eToro Ticker → TR 名称对照（用于跨账户识别同一标的）：**
| eToro | TR |
|-------|----|
| NVDA | NVIDIA |
| AMD | AMD |
| AVGO | Broadcom |
| TSM | TSMC (ADR) |
| MSFT | Microsoft |
| AAPL | Apple |
| META | Meta Platforms (A) |
| GOOG | Alphabet (A) |
| AMZN | Amazon.com |
| TSLA | Tesla |
| GS | Goldman Sachs |
| WDC | Western Digital |
| MU | Micron Technology |

### 0c. 对比今昨持仓，生成变化记录

今日持仓数据在 Step 1 完成后获得。完成 Step 1 后立即执行对比：

对每个当前持仓：
- **新建仓**：今日有、昨日无 → `change_type = "NEW"`, `delta = +今日数量`
- **加仓**：今日数量 > 昨日数量 → `change_type = "ADD"`, `delta = +差值`
- **减仓**：今日数量 < 昨日数量 → `change_type = "REDUCE"`, `delta = -差值`
- **持平**：数量相同（允许 ±0.001 浮点误差）→ `change_type = "SAME"`

对每个昨日有、今日无的持仓：
- **已清仓**：`change_type = "CLOSED"`, `delta = -昨日数量`

**仅当 `change_type != "SAME"` 时，才需要在报告中 highlight。**

---

## 前置条件：必须获得实时数据，否则终止

**硬性规则：** eToro 和 Trade Republic 必须同时成功登录并获取实时数据，才能进行后续步骤。

- 如果任一账户登录失败（用户无法完成 2FA、页面无法加载等情况），**立即终止**，不执行搜索、分析、报告生成
- 不允许使用截图 OCR、历史数据估算、手动输入等方式替代实时数据
- 不允许只用一个账户的数据生成报告——两个账户都是必需的
- 终止时告知用户哪个账户登录失败并停止后续操作

---

## Step 1: Open Browser & Login

### 1a. 打开浏览器

使用 Playwright 打开浏览器。

### 1b. 登录 eToro

1. 导航到 `https://www.etoro.com/`
2. 告知用户需要手动登录（eToro 有 2FA，无法自动完成）
3. 等待用户登录完成（观察页面变化，检测到 Portfolio 入口出现即视为登录成功）
4. 导航到 `https://www.etoro.com/portfolio/`
5. 读取持仓表格数据

**eToro 持仓读取指引：**
- 页面加载后，用 `browser_snapshot` 获取页面结构
- 找到持仓表格行，每行包含：股票代码、当前价格、今日涨跌幅、持仓数量、均价、P&L、P&L%、总净值
- 提取全部行数据
- 同时提取页面顶部的总账户净值、今日 P&L、现金余额

### 1c. 登录 Trade Republic

1. 打开新标签页，导航到 `https://app.traderepublic.com/`
2. 告知用户需要手动登录（TR 有 2FA）
3. 等待用户登录完成
4. 登录后，导航到 `https://app.traderepublic.com/portfolio?timeframe=1d`
5. 使用 JS 切换视图到 "Since buy (€)"（参考记忆中的优化流程）：

```js
// 第一步：展开下拉菜单
() => {
  const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim().startsWith('Daily trend'));
  if (btn) { btn.click(); return 'dropdown triggered'; }
  return 'not found';
}
```

等待 500ms 后：

```js
// 第二步：点击 "Since buy (€)"
() => {
  const items = Array.from(document.querySelectorAll('li, [role="option"], [role="menuitem"]'));
  const target = items.find(el => el.innerText && el.innerText.trim() === 'Since buy (€)');
  if (target) { target.click(); return 'clicked'; }
  return 'not found';
}
```

6. 用 `browser_snapshot` 获取持仓列表
7. 提取每个持仓：名称、持仓量、当前市值、累计盈亏（€）
8. 同时提取页面顶部的总组合价值、今日 P&L
9. **提取 TR 现金余额**：TR 页面通常将未投资现金显示为 "Cash" 或 "Verrechnungskonto" 条目，或在账户摘要顶部显示"Uninvested cash"。用以下 JS 尝试读取：

```js
// 尝试从持仓列表中找到现金条目
() => {
  const items = Array.from(document.querySelectorAll('[data-testid*="cash"], [class*="cash"], [class*="Cash"]'));
  if (items.length) return items.map(el => el.innerText).join(' | ');
  // fallback: 找所有包含 "Cash" 文字的元素
  const all = Array.from(document.querySelectorAll('*')).filter(el =>
    el.children.length === 0 && el.innerText && el.innerText.match(/cash|verrechnungskonto/i)
  );
  return all.slice(0, 5).map(el => `${el.className}: ${el.innerText}`).join('\n');
}
```

如果 JS 无法提取，用 `browser_snapshot` 在页面中手动识别现金余额数字（通常在持仓列表最下方或账户摘要区域）。**现金余额必须提取，不可省略。**

### 1d. 获取 EUR/USD 汇率

从以下渠道获取，按优先级：
1. TR 搜索框 → 搜索 "EUR/USD" 获取实时汇率
2. eToro 页面的 EURUSD 报价
3. 如果上述不可用，用 Playwright 导航到 `https://finance.yahoo.com/quote/EURUSD=X/` 读取

---

## Step 2: Search Market Information

### 2a. 用 WebSearch 搜索（首选）

并行搜索以下内容：
1. `"US stock market today {date} sector performance market close"`
2. `"Magnificent 7 stocks today {date}"`（或挨个快速搜索 NVDA AMD AAPL MSFT GOOG META AMZN 当日表现）
3. 如果有重要财报（搜索 `"earnings calendar {date}"` 看是否有持仓股发布财报）
4. 如果有重大宏观事件（搜索 `"US economic data {date}"`）

### 2b. 如果 WebSearch/WebFetch 不可用 → Playwright 浏览器兜底

如果 WebSearch 或 WebFetch 返回错误（API 故障、网络策略限制等），**不得跳过搜索步骤**，立即用 Playwright 浏览器直接导航到以下数据源：

**大盘行情：**
- `https://finance.yahoo.com/quote/%5EGSPC/` → S&P 500 指数
- `https://finance.yahoo.com/quote/%5EIXIC/` → Nasdaq 综合指数
- `https://www.cnbc.com/markets/` → 当日市场总结

**持仓标的行情 + 新闻（并行抓取关键持仓）：**
- `https://finance.yahoo.com/quote/{TICKER}/` — 实时价格、涨跌幅、相关新闻
- `https://www.cnbc.com/quotes/{TICKER}` — 市场评论、分析师观点

**专业分析（选做，精力优先分配给当日波动大的持仓）：**
- `https://seekingalpha.com/symbol/{TICKER}` — 多空分析、财报评论
- `https://www.reddit.com/r/wallstreetbets/search/?q={TICKER}` — 社区情绪参考

**EUR/USD 汇率：**
- `https://www.bloomberg.com/quote/EURUSD:CUR` 或
- `https://finance.yahoo.com/quote/EURUSD=X/`

用 `browser_navigate` + `browser_snapshot`/`browser_evaluate` 提取上述页面的关键数据。

**优先级规则：** Yahoo Finance 数据最全、结构最稳定，优先抓取。

---

## Step 3: Generate HTML Report

使用 `<reference report>` 中的 HTML 格式。报告结构必须包含以下部分：

### 报告内容结构

1. **标题与副标题**
   - 报告日期 + 星期
   - EUR/USD 汇率
   - 当天最重要的催化剂（用 ⚡ 标注）
   - 最紧急的风险提示（用 ⚠️ 标注）

2. **数据来源验证 banner** — 确认数据已从 eToro + TR 实时获取

3. **持仓变化对比 banner**（紧跟数据来源验证，每日必须出现）

   - 若有前日数据：展示完整的变化对比表（见下方规范）
   - 若无前日数据：显示灰色提示条"⚪ 无前日数据，跳过持仓对比"

   **变化对比表规范：**
   ```html
   <h2>⚖️ 持仓变化对比（今日 vs 昨日）</h2>
   <!-- 若无任何变化，只显示：-->
   <div class="diff-none-banner">✅ 持仓数量与昨日完全一致，无变化</div>
   <!-- 若有变化，展示以下表格（仅列出 change_type != SAME 的行）：-->
   <table class="diff-table">
     <tr>
       <th>账户</th><th>股票</th><th>变化类型</th>
       <th>昨日数量</th><th>今日数量</th><th>变化量</th><th>说明</th>
     </tr>
     <!-- NEW 行 -->
     <tr class="diff-new">
       <td>eToro</td><td><b>LITE</b></td>
       <td><span class="diff-badge diff-badge-new">⭐ 新建仓</span></td>
       <td>—</td><td>1.08</td><td class="val-up">+1.08</td>
       <td>首次建仓</td>
     </tr>
     <!-- ADD 行 -->
     <tr class="diff-add">
       <td>TR</td><td><b>AMD</b></td>
       <td><span class="diff-badge diff-badge-add">🔼 加仓</span></td>
       <td>32.818</td><td>35.000</td><td class="val-up">+2.182</td>
       <td>补仓</td>
     </tr>
     <!-- REDUCE 行 -->
     <tr class="diff-reduce">
       <td>eToro</td><td><b>META</b></td>
       <td><span class="diff-badge diff-badge-reduce">🔽 减仓</span></td>
       <td>13</td><td>10</td><td class="val-down">-3</td>
       <td>止损/减持</td>
     </tr>
     <!-- CLOSED 行 -->
     <tr class="diff-close">
       <td>eToro</td><td><b>JEPI</b></td>
       <td><span class="diff-badge diff-badge-close">🔴 已清仓</span></td>
       <td>39</td><td>0</td><td class="val-down">-39</td>
       <td>完全退出</td>
     </tr>
   </table>
   ```

   **stock-card 中同步标注（在 ticker 右侧追加 badge）：**
   - 新建仓：`<span class="diff-inline diff-inline-new">⭐ NEW</span>`
   - 加仓：`<span class="diff-inline diff-inline-add">🔼 +N</span>`
   - 减仓：`<span class="diff-inline diff-inline-reduce">🔽 -N</span>`
   - 清仓：该 stock-card 的 header 改为暗红色背景 `style="background:#7b1a1a"`

4. **操作指令 banner**（如果有紧急操作建议）
   - 红色（背景 #fde8e8）：必须执行的操作
   - 黄色（背景 #fff8e1）：需要关注的事件

4. **上次建议执行对比 table**（执行/未执行/等待中）

5. **账户概览**
   - eToro 账户卡片：总净值、今日 P&L、**现金余额**、**已投资金额**（= 总净值 - 现金）、**现金占比**（现金 / 总净值，%）、全部持仓表格（含价格/今日涨跌/持仓/均价/P&L%/净值）
   - TR 账户卡片：总净值、今日 P&L、**现金余额（€）**、**已投资金额（€）**（= 总净值 - 现金）、**现金占比**（%）、全部持仓表格（含名称/持仓量/市值/累计盈亏）
   - 两账户合计：
     - 合并总净值（USD）= eToro 净值 + TR 净值 × EUR/USD
     - **合并现金（USD）** = eToro 现金 + TR 现金 × EUR/USD
     - **合并已投资（USD）** = 合并总净值 - 合并现金
     - **合并现金占比** = 合并现金 / 合并总净值（%）
     - 在 combined-total 区块中同时展示这四项数字

   **现金占比阈值参考**（在报告中用颜色标注）：
   - 现金占比 < 3%：标注为"现金极危 🔴"，可用机动资金极少
   - 现金占比 3%–8%：标注为"现金偏低 🟡"，谨慎加仓
   - 现金占比 8%–20%：标注为"现金充足 🟢"，有加仓能力
   - 现金占比 > 20%：标注为"现金过高 ⚪"，考虑择机部署

6. **持仓分析（按板块分组）**
   - **AI 芯片/半导体**：NVDA, TSM, AMD, MU, AVGO
   - **大型科技/云计算**：AAPL, MSFT, META, AMZN, GOOG
   - **消费科技/金融/存储**：TSLA, WDC, GS
   - **ETF/收益型/其他**：VOO, JEPQ, JEPI, CRISPR, IUIT, CNDX, NFLX

7. **每个 stock-card 的格式**：
   - header：ticker + 公司名 + 特殊标签（如"⚡ 今晚财报"）
   - body：
     - meta：价格、今日涨跌、持仓量、市值、P&L、P&L%、均价、两账户合并
     - verdict badge（buy/hold/sell）
     - targets：共识均值/最高目标/止损参考（含上行/下行空间 %）
     - 多头分析（s-bull badge）：基本面逻辑、催化剂
     - 空头分析（s-bear badge）：风险因素、估值压力
     - 结论：明确的操作建议

8. **操作建议汇总 table**
   - 按优先级排列（① 今日必须 ② 关注 ③ 等待 ④ 持有）
   - 列：优先级、股票、方向、账户、数量、参考价、理由

9. **近期重要事件**（财报日期、经济数据、政策事件）

10. **footer**：报告生成时间、数据来源

### HTML 样式规范

严格遵守参考报告的 CSS：
```css
body: font-family PingFang SC; padding 40px; color #1a1a2e
h1: color #0f3460; border-bottom 3px solid #e94560
h2: color #0f3460; border-left 4px solid #e94560
sector-header: background #16213e (深色)
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

**现金区块额外 CSS**（在 account-box 内新增）：
```css
.cash-row { display:flex; gap:16px; margin-top:8px; font-size:13px; flex-wrap:wrap }
.cash-item { flex:1; min-width:110px }
.cash-item .label { font-size:11px; color:#888 }
.cash-item .value { font-weight:700; font-size:15px }
.cash-ratio-badge { display:inline-block; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:700; margin-top:4px }
.cash-danger  { background:#fde8e8; color:#c0392b }   /* < 3% */
.cash-low     { background:#fff8e1; color:#856404 }   /* 3–8% */
.cash-ok      { background:#d4f5e9; color:#0a7a4f }   /* 8–20% */
.cash-high    { background:#f0f2fa; color:#555 }      /* > 20% */
```

**combined-total 区块现金行**（在合并总净值下方追加）：
```html
<div style="display:flex;gap:24px;justify-content:center;margin-top:10px;font-size:13px;opacity:.9">
  <span>现金 $XX,XXX (<span class="cash-ratio-badge cash-ok">X.X%</span>)</span>
  <span>已投资 $XXX,XXX (XX.X%)</span>
</div>
```

**持仓变化对比区块额外 CSS**（追加到 `<style>` 末尾）：
```css
/* 对比表整体 */
.diff-table th { background:#2c3e50; }
/* 行背景 */
.diff-new    { background:#d4f5e9; }
.diff-add    { background:#eafaf1; }
.diff-reduce { background:#fef9e7; }
.diff-close  { background:#fde8e8; }
/* 变化类型徽章 */
.diff-badge { display:inline-block; padding:2px 10px; border-radius:10px; font-size:11px; font-weight:700; }
.diff-badge-new    { background:#0a7a4f; color:#fff; }
.diff-badge-add    { background:#1e8bc3; color:#fff; }
.diff-badge-reduce { background:#e67e22; color:#fff; }
.diff-badge-close  { background:#c0392b; color:#fff; }
/* stock-card 内行内 badge */
.diff-inline { font-size:11px; padding:2px 8px; border-radius:8px; margin-left:6px; font-weight:700; vertical-align:middle; }
.diff-inline-new    { background:#0a7a4f; color:#fff; }
.diff-inline-add    { background:#1e8bc3; color:#fff; }
.diff-inline-reduce { background:#e67e22; color:#fff; }
/* 无变化提示条 */
.diff-none-banner { background:#f0f2fa; border:1px solid #c7d0f0; border-radius:6px; padding:10px 16px;
                    font-size:13px; color:#555; margin:10px 0; text-align:center; }
```

---

## Step 4: Save Report

将生成的 HTML 文件保存为：
```
~/Desktop/claude/{date}/report-{date}.html
```

确保 `~/Desktop/claude/{date}/` 目录存在，不存在则创建。

---

## 注意事项

### 投资哲学（生成建议时必须遵循）
- **长期主义 + 复利最大化**：持有优质赢家，让复利滚动；不以"锁利"为目标
- 减仓建议必须标注层级：
  - 个股层级（论文破裂 / 资本再配置 / 仓位超限 / 预设条件触发）
  - 组合层级（市场系统性风险）
- 以下不是合法减仓理由："涨太多了"、"锁利"、"涨了 X%"
- 每条操作建议必须锚定至少一个估值锚

### 数据安全问题
- 任何情况下不得保存用户名、密码、cookie、session token 到任何文件
- 用户必须手动完成登录（2FA）
- 登录完成后立即继续后续自动化步骤

### 数据对比逻辑
- **前日报告路径**：`~/Desktop/claude/{prev_trading_day}/report-{prev_trading_day}.html`（周一取周五）
- 若文件存在：执行 Step 0b-0c，提取 eToro + TR 持仓数量，与今日实时数量对比
- **高亮规则**（仅对 `change_type != SAME` 的持仓）：
  - ⭐ 新建仓（NEW）：今日有、昨日无
  - 🔼 加仓（ADD）：今日数量 > 昨日数量
  - 🔽 减仓（REDUCE）：今日数量 < 昨日数量
  - 🔴 已清仓（CLOSED）：昨日有、今日无
- 变化出现在两处：① 报告顶部独立对比表；② 对应 stock-card 的 ticker 旁 inline badge
- 若无任何变化：顶部显示"✅ 持仓数量与昨日完全一致，无变化"
- 若无前日文件：顶部显示"⚪ 无前日数据，跳过持仓对比"，不报错

### 推荐操作原则
- **现金管理**：始终跟踪 eToro + TR 双账户现金，按合并现金占比判断：
  - < 3%：现金极危，不得再加仓，先评估是否需要变现防御仓位
  - 3–8%：现金偏低，仅执行高确定性操作
  - 8–20%：正常区间，可按计划加仓
  - > 20%：现金过高，结合市场信号考虑择机部署
- eToro 单账户现金 < $500 单独标注（该账户机动性极低）
- 财报前不追高、不盲目止损
- 低于均价的持仓标记为"等待修复"
- 浮盈超过 +30% 的持仓考虑是否止损需要上移
