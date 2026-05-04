# Daily Investment Report Agent

每日投资日报生成器。自动登录 eToro + Trade Republic，抓取实时持仓数据，生成 HTML 报告。

## 功能

- 🔐 Playwright 浏览器自动化登录（支持 2FA，等待最多 3 分钟）
- 📊 实时读取 eToro 全部持仓（价格 · 持仓量 · 均价 · 盈亏）
- 🇩🇪 实时读取 Trade Republic 全部持仓（EUR 市值 · Since Buy 盈亏）
- 💱 自动抓取 EUR/USD 汇率（Frankfurter API）
- 😱 Fear & Greed 指数（CNN）
- 📈 市场指数（S&P500 · NDX100 · DJI，via yfinance）
- 💾 输出自包含 HTML 报告，自动在浏览器打开

## 安装

```bash
pip install -r requirements.txt
playwright install chromium
```

## 凭据配置

凭据存储在本地，**不进入 git**：

```bash
mkdir -p ~/.credentials
cat > ~/.credentials/investment_accounts.json << 'EOF'
{
  "etoro": {
    "username": "your_etoro_username",
    "password": "your_etoro_password"
  },
  "trade_republic": {
    "phone": "+49 XXXXXXXXXXX",
    "pin":   "1234"
  }
}
EOF
chmod 600 ~/.credentials/investment_accounts.json
```

## 使用

```bash
# 生成今日报告（保存到 ~/Desktop/claude/YYYY-MM-DD/report-YYYY-MM-DD.html）
python agent.py

# 指定输出路径
python agent.py --out /path/to/report.html
```

登录过程中，如需 2FA 验证，会在弹出的浏览器窗口中等待你完成操作（最多 3 分钟）。

## 项目结构

```
daily-report-agent/
├── agent.py              # 入口，运行此文件
├── config.py             # 路径与超时配置
├── brokers/
│   ├── etoro.py          # eToro Playwright 抓取
│   └── tr.py             # Trade Republic Playwright 抓取
├── report/
│   └── generator.py      # HTML 报告生成
├── utils/
│   └── market.py         # EUR/USD · F&G · 指数
├── requirements.txt
└── .gitignore
```

## 输出示例

报告保存至 `~/Desktop/claude/2026-05-05/report-2026-05-05.html`，包含：

- 账户概览（eToro USD + TR EUR + 合计折算）
- eToro 全部持仓明细（价格 · 持仓量 · 均价 · 总盈亏 · 净值）
- Trade Republic 全部持仓明细（持仓量 · EUR 市值 · 累计盈亏）
- 市场指数 + Fear & Greed

## 注意事项

- 运行时需要显示器（Playwright `headless=False`），用于 2FA 交互
- 凭据文件权限设为 `600`，仅本人可读
- 凭据文件路径 `~/.credentials/` 在系统级不纳入任何 git 追踪
