# A股早间交易策略报告

手动触发时，生成下一个A股交易日的策略报告并保存至 DougInvestment 文件夹。

## 触发方式

用户输入 `/a-share-morning-report` 时执行以下流程。

## 执行步骤

### 第一步：搜索当前市场信息（必须搜索4-5次）

用 WebSearch 依次搜索：
1. `"今日 A股收盘 沪指 创业板 涨跌 {今天日期}"`
2. `"A股 主力资金流向 热点板块 涨停概念 {今天日期}"`
3. `"A股 下周策略 板块推荐 {今天年月}"`
4. `"A股 近期政策 财报日历 重要事件 {今天年月}"`
5. （可选）根据搜索结果发现的热点板块做追加搜索

### 第二步：生成 HTML 报告

**报告结构（必须包含以下所有部分）：**

1. **标题与副标题** — 报告日期 + 核心要点摘要（一句话）
2. **风险提醒 banner**（如有一季报雷区、假期等特殊情况）
3. **宏观背景表格** — 信号/现状/机制判断/影响方向，4-6行
4. **关键事件日历** — 含日期、催化剂/风险标签、描述
5. **3-5个推荐板块**，每个板块包含：
   - `sector-header`：板块名、时间维度
   - `sector-verdict`：配置建议（增配/持仓/减配）、催化剂、风险
   - 2-3个 `stock-card`：代码+名称+逻辑分析（多/空）+操作建议
6. **风险提示表格** — 风险类型/内容/应对策略
7. **footer** — 数据来源 + 生成时间

**HTML 样式（严格遵守，与现有报告一致）：**

```css
body: font-family PingFang SC; padding 40px; color #1a1a2e
h1: color #0f3460; border-bottom 3px solid #e94560
h2: color #0f3460; border-left 4px solid #e94560
sector-header: background #16213e (深色)
stock-header: background #0f3460
s-bull: background #d4f5e9; color #0a7a4f
s-bear: background #fde8e8; color #c0392b
overweight badge: background #d4f5e9; color #0a7a4f; border-radius 20px
maintain badge: background #fff3cd; color #856404
underweight badge: background #fde8e8; color #c0392b
analysis-text: border-left 3px solid #0f3460; background #f8f9ff
macro-box: background #fff8e1; border #ffe082
```

### 第三步：保存文件

将生成的 HTML 保存至：
`/Users/songsong/Desktop/claude/DougInvestment/astock-{下一交易日日期}.html`

用 Write 工具直接写入，文件名格式：`astock-YYYY-MM-DD.html`

### 第四步：发送邮件（自动，无需询问）

用 Apple Mail 将报告作为附件自动发送到 **505796889@qq.com**，无需询问。

```applescript
tell application "Mail"
    set newMessage to make new outgoing message with properties ¬
        {subject:"A股交易策略报告 - {日期}", ¬
         content:"请查收今日A股交易策略报告。"}
    tell newMessage
        make new to recipient at end of to recipients ¬
            with properties {address:"505796889@qq.com"}
        make new attachment with properties ¬
            {file name:("{报告文件路径}" as POSIX file)}
    end tell
    send newMessage
end tell
```

### 第五步：告知用户

报告已保存并发送，简要列出本次推荐的板块和核心逻辑。

## 注意事项

- 只推荐用户**不持有**的股票（用户持有美股：NVDA MSFT TSM META GOOG AMD AMZN AVGO AAPL TSLA RXRX GS WDC MU NFLX VOO JEPQ JEPI）
- 股票代码格式：A股代码（6位数字）
- 不推荐连板高位追入标的
- 节前最后1-2个交易日提醒控仓
- 一季报披露最后一周（通常4月最后一周）强调雷区风险
