#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股早间交易策略报告
- 每天 08:00 由 LaunchAgent 自动触发
- 通过 claude CLI（OAuth 自动认证 + web_search 内置）生成下一交易日策略
- HTML 保存至 DougInvestment 文件夹
- 通过 macOS Mail.app 发送至 QQ 邮箱（无需 SMTP 密码）
"""

import subprocess
import re
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

# ── 配置 ─────────────────────────────────────────────────────────────────────
REPORT_DIR = Path.home() / "Desktop/claude/DougInvestment"
TO_EMAIL   = "505796889@qq.com"
LOG_F      = Path.home() / "Desktop/claude/daily/astock_report.log"
CLAUDE_BIN = "/Users/songsong/.local/bin/claude"   # Claude Code 安装路径


# ── 工具函数 ──────────────────────────────────────────────────────────────────
def log(msg):
    from datetime import datetime
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG_F, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def find_claude() -> str:
    """找到 claude CLI 路径"""
    for path in [CLAUDE_BIN, "/usr/bin/claude", "/opt/homebrew/bin/claude"]:
        if Path(path).exists():
            return path
    # fallback: which
    r = subprocess.run(["which", "claude"], capture_output=True, text=True)
    if r.returncode == 0:
        return r.stdout.strip()
    raise FileNotFoundError("未找到 claude CLI，请确认 Claude Code 已安装")


def next_trading_day() -> date:
    """获取下一个交易日（粗略跳过周末）"""
    d = date.today() + timedelta(days=1)
    while d.weekday() >= 5:   # 5=周六 6=周日
        d += timedelta(days=1)
    return d


# ── 报告生成 ──────────────────────────────────────────────────────────────────
def build_prompt(next_day: date) -> str:
    today     = date.today()
    today_str = today.strftime("%Y-%m-%d")
    next_str  = next_day.strftime("%Y-%m-%d")
    weekdays  = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    next_wd   = weekdays[next_day.weekday()]
    today_wd  = weekdays[today.weekday()]

    return f"""今天是 {today_str}（{today_wd}），请为 {next_str}（{next_wd}，下一个A股交易日）生成A股交易策略报告。

## 必须先搜索（至少4次 web_search）

1. "{today_str} A股收盘 沪指 创业板 指数涨跌幅"
2. "{today_str} A股热点板块 主力资金流向 涨停概念"
3. "A股 {next_str} 下周策略 板块推荐 机构观点"
4. "A股 近期政策 财报 重要事件 {today_str[:7]}"

根据搜索结果决定是否追加第5次（某热点板块的具体个股）。

## 输出要求

只输出完整 HTML，从 <!DOCTYPE html> 开始，不要任何解释文字。

### 报告结构（必须包含）

1. `<h1>A股交易策略报告</h1>` + `<p class="subtitle">{next_str}（{next_wd}）| [一句核心摘要]</p>`
2. 如有雷区/假期等风险，加 `<div class="alert-banner">⚠️ ...</div>`
3. `<div class="macro-box">` 宏观背景表格（信号/现状/机制判断/影响方向）
4. 关键事件日历（含 tag 标注 catalyst/risk/policy）
5. 3~5个推荐板块，每板块：
   - `sector-header`（板块名 + 时间维度）
   - `sector-verdict`（overweight/maintain/underweight + 逻辑 + 风险）
   - 2~3只 `stock-card`（代码+名称+verdict buy/watch/hold + s-bull/s-bear 分析 + 结论）
6. 风险提示表格（风险类型/内容/应对策略）
7. `<div class="footer">数据来源：[来源] | 生成时间：{today_str}</div>`

### CSS 样式（内联 `<style>` 标签，严格遵守）

```css
* {{ margin:0; padding:0; box-sizing:border-box }}
body {{ font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
       font-size:13px; color:#1a1a2e; background:#fff; padding:40px; line-height:1.7 }}
h1   {{ font-size:26px; color:#0f3460;
       border-bottom:3px solid #e94560; padding-bottom:10px; margin-bottom:6px }}
.subtitle {{ color:#666; font-size:13px; margin-bottom:24px }}
h2   {{ font-size:17px; color:#0f3460; margin:26px 0 10px;
       border-left:4px solid #e94560; padding-left:10px }}
.alert-banner {{ background:#fff3cd; border:1px solid #ffd966; border-radius:6px;
                 padding:10px 16px; margin-bottom:14px; font-size:12px; color:#856404 }}
.macro-box {{ background:#fff8e1; border:1px solid #ffe082; border-radius:8px;
              padding:14px 16px; margin-bottom:18px }}
table {{ width:100%; border-collapse:collapse; margin:6px 0; font-size:12px }}
th {{ background:#f0f2fa; color:#0f3460; padding:6px 10px; text-align:left; font-weight:600 }}
td {{ padding:5px 10px; border-bottom:1px solid #f0f2fa; vertical-align:top }}
.sector-block {{ margin-bottom:32px }}
.sector-header {{ background:#16213e; color:white; padding:10px 18px;
                  border-radius:8px 8px 0 0;
                  display:flex; justify-content:space-between; align-items:center }}
.sector-header .sn {{ font-size:15px; font-weight:700 }}
.sector-header .sm {{ font-size:12px; opacity:.8 }}
.sector-verdict {{ background:#f4f6ff; border:1px solid #c8d0f0;
                   border-top:none; padding:12px 16px }}
.stock-card {{ border:1px solid #e8eaf0; overflow:hidden; border-top:none }}
.stock-header {{ background:#0f3460; color:white; padding:9px 16px;
                 display:flex; justify-content:space-between; align-items:center }}
.stock-header .ticker {{ font-size:16px; font-weight:700 }}
.stock-header .name {{ font-size:11px; opacity:.8 }}
.stock-header .badge {{ font-size:11px; background:rgba(255,255,255,.2);
                        border-radius:4px; padding:2px 8px }}
.stock-body {{ padding:12px 16px }}
.verdict {{ display:inline-block; padding:3px 12px; border-radius:20px;
            font-weight:700; font-size:12px; margin-bottom:8px }}
.buy   {{ background:#d4f5e9; color:#0a7a4f }}
.watch {{ background:#e3f2fd; color:#1565c0 }}
.hold  {{ background:#fff3cd; color:#856404 }}
.overweight  {{ background:#d4f5e9; color:#0a7a4f; font-weight:700;
                padding:2px 10px; border-radius:20px; font-size:12px }}
.maintain    {{ background:#fff3cd; color:#856404; font-weight:700;
                padding:2px 10px; border-radius:20px; font-size:12px }}
.underweight {{ background:#fde8e8; color:#c0392b; font-weight:700;
                padding:2px 10px; border-radius:20px; font-size:12px }}
.s-bull {{ display:inline-block; background:#d4f5e9; color:#0a7a4f;
           border-radius:3px; padding:0 5px; font-weight:700; font-size:11px }}
.s-bear {{ display:inline-block; background:#fde8e8; color:#c0392b;
           border-radius:3px; padding:0 5px; font-weight:700; font-size:11px }}
.analysis-text {{ font-size:12px; color:#444; background:#f8f9ff;
                  border-left:3px solid #0f3460; padding:7px 12px;
                  border-radius:0 4px 4px 0; margin-top:8px }}
.tag {{ display:inline-block; font-size:10px; padding:1px 7px;
        border-radius:10px; font-weight:700; margin-right:4px }}
.tag-event  {{ background:#e3f2fd; color:#1565c0 }}
.tag-risk   {{ background:#fde8e8; color:#c0392b }}
.tag-policy {{ background:#f3e5f5; color:#6a1b9a }}
.footer {{ margin-top:36px; padding-top:14px; border-top:1px solid #e0e0e0;
           font-size:11px; color:#999; text-align:center }}
```

### 个股推荐原则

- 推荐用户未持有的A股标的（用户仅持有美股，A股空仓）
- 不推荐连板高位追入标的（加 ⚠️ 注明）
- 节前最后交易日提醒控仓
- 一季报最后披露周（4月最后一周）重点标注雷区风险
"""


def generate_html(claude_bin: str, next_day: date) -> str:
    prompt = build_prompt(next_day)

    # 写到临时文件，避免命令行长度限制
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        env = {**os.environ, "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"}
        with open(prompt_file, "r", encoding="utf-8") as pf:
            prompt_text = pf.read()

        result = subprocess.run(
            [claude_bin, "--print", "--output-format", "text",
             "--allowedTools", "WebSearch,Write",
             "--permission-mode", "acceptEdits",
             prompt_text],
            capture_output=True,
            text=True,
            timeout=360,   # 6分钟
            env=env,
        )
    finally:
        os.unlink(prompt_file)

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI 返回码 {result.returncode}: {result.stderr[:400]}")

    html = result.stdout.strip()

    # 去除 markdown 代码块包裹（如 ```html ... ```）
    html = re.sub(r"^```html\s*\n?", "", html, flags=re.IGNORECASE | re.MULTILINE)
    html = re.sub(r"\n?```\s*$", "", html, flags=re.MULTILINE)

    # 截取从 <!DOCTYPE 开始的部分
    idx = html.lower().find("<!doctype")
    if idx > 0:
        html = html[idx:]

    return html.strip()


# ── 保存 & 发送 ───────────────────────────────────────────────────────────────
def save_html(html: str, next_day: date) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    fname = REPORT_DIR / f"astock-{next_day.strftime('%Y-%m-%d')}.html"
    fname.write_text(html, encoding="utf-8")
    return fname


def send_email(html_path: Path, next_day: date) -> bool:
    date_str = next_day.strftime("%Y-%m-%d")
    subj  = f"A股交易策略 {date_str}"
    body  = (f"请查收 {date_str} A股交易策略报告（HTML 附件）。\\n\\n"
             f"包含下一交易日推荐板块及个股分析，祝交易顺利。")
    fpath = str(html_path)

    script = f"""
tell application "Mail"
    set m to make new outgoing message with properties {{subject:"{subj}", content:"{body}", visible:false}}
    tell m
        make new to recipient at end of to recipients with properties {{address:"{TO_EMAIL}"}}
        make new attachment with properties {{file name:(POSIX file "{fpath}") as alias}} at after last paragraph
    end tell
    send m
end tell
"""
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        log(f"osascript stderr: {r.stderr.strip()}")
    return r.returncode == 0


# ── 主程序 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log("=" * 50)
    log("A股策略报告生成开始")

    try:
        claude_bin = find_claude()
        log(f"Claude CLI: {claude_bin}")

        next_day = next_trading_day()
        log(f"目标交易日: {next_day}（{['周一','周二','周三','周四','周五','周六','周日'][next_day.weekday()]}）")

        log("正在调用 Claude CLI 搜索市场信息并生成报告（约2-4分钟）...")
        html = generate_html(claude_bin, next_day)

        if not html.lower().startswith("<!doctype"):
            log(f"⚠️  HTML 格式异常，前200字符: {html[:200]}")
        else:
            log(f"HTML 生成成功（{len(html):,} 字节）")

        path = save_html(html, next_day)
        log(f"✅ 报告已保存: {path}")

        ok = send_email(path, next_day)
        log(f"{'✅' if ok else '❌'} 邮件{'已发送至 ' + TO_EMAIL if ok else '发送失败'}")

    except Exception as exc:
        log(f"❌ 异常: {exc}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)

    log("完成")
    log("=" * 50)
