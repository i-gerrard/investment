---
name: git-sync
description: 多终端开发时的 Git 版本管理工作流。安全地将本地变更同步到远端，处理 WIP 暂存、rebase 冲突、推送失败等常见场景。当用户说"提交"、"同步"、"push"、"上传到git"时使用。
allowed-tools: Bash, Read, Edit
---

# Git Sync — 版本管理工作流

## 适用项目

- **investment-manager**：`~/Desktop/investment-manager/`，远端 `https://github.com/i-gerrard/investment-manager`
- **investment（skills仓库）**：`/tmp/investment-repo/`（按需 clone），远端 `https://github.com/i-gerrard/investment`

---

## 核心原则

1. **永远只提交明确指定的文件**，不用 `git add .` 或 `git add -A`
2. **推送前必须先同步远端**，避免 non-fast-forward 错误
3. **WIP 改动用 stash 保护**，不随手提交半成品
4. **冲突时保守处理**：优先保留用户本地 WIP，不自作主张丢弃未提交内容
5. **永不 force push main**

---

## 标准流程

### 场景 A：提交并推送指定文件

适用：用户明确说"提交 X 文件"或"把这个改动推上去"。

```
Step 1  诊断当前状态
  git status
  git log --oneline origin/main..HEAD   # 确认本地是否已有未推送提交

Step 2  暂存指定文件（绝不 add .）
  git add <file1> <file2> ...

Step 3  确认暂存内容
  git diff --cached --stat

Step 4  提交（Conventional Commit 格式）
  git commit -m "type: description

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

Step 5  推送（处理远端有新提交的情况）
  → 先执行【推送前同步】流程（见下）
  → 再 git push origin main
```

**Conventional Commit 类型速查：**

| type | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更（PRD、README 等） |
| `refactor` | 重构（不改功能） |
| `chore` | 构建配置、依赖、gitignore 等 |
| `style` | 格式、lint |
| `test` | 测试 |

---

### 场景 B：开始新工作前同步远端（多终端场景）

适用：在另一台终端开始工作前，确保拿到最新代码。

```
Step 1  检查本地是否有未提交改动
  git status

Step 2a  若工作区干净 → 直接 pull
  git pull --rebase origin main

Step 2b  若有 WIP 改动 → 执行【WIP 保护性 stash】流程（见下）
```

---

### 场景 C：推送前同步（远端有新提交时）

适用：`git push` 被拒绝（rejected, non-fast-forward）时。

```
Step 1  检查工作区状态
  git status

Step 2a  工作区干净 → 直接 rebase
  git pull --rebase origin main
  git push origin main

Step 2b  工作区有未提交改动 → 执行【WIP 保护性 stash】
  git stash push -u -m "wip: <简短描述>"
  git pull --rebase origin main

  → 若 rebase 成功：
    git stash pop
    → 若 pop 无冲突：git push origin main
    → 若 pop 有冲突：执行【Stash Pop 冲突处理】

  → 若 rebase 有冲突：执行【Rebase 冲突处理】
```

---

### 场景 D：WIP 保护性 Stash

```
# stash 名称必须包含描述，方便识别
git stash push -u -m "wip: <当前工作描述>"

# 确认 stash 成功
git stash list

# 完成 pull/rebase 后恢复
git stash pop

# 若不再需要 stash 内容
git stash drop
```

**`-u` 标志**：包含 untracked 文件（避免 rebase 时 "untracked files would be overwritten" 错误）。

**注意**：`next-env.d.ts`、`package-lock.json`、`venv/` 已在 `.gitignore` 中，不会被 stash 影响。

---

### 场景 E：Rebase 冲突处理

```
# 查看冲突文件
git status   # 显示 "both modified"

# 对每个冲突文件：
# - 如果是用户的 WIP 内容（暂存的文件）→ 保留用户版本
  git checkout --ours <file>
  git add <file>

# - 如果是纯远端新增内容 → 保留远端版本
  git checkout --theirs <file>
  git add <file>

# - 如果两边都有重要改动 → 人工 Review
  # 打开文件，搜索 <<<<<<, 手动合并，再 git add

# 解决所有冲突后继续 rebase
git rebase --continue

# 推送
git push origin main
```

---

### 场景 F：Stash Pop 冲突处理

stash pop 冲突意味着 stash 中的 WIP 改动与远端拉取的内容有重叠。

```
# 查看冲突
git status

# 策略：优先保留 stash（本地 WIP）版本
git checkout --ours <conflicted-file>
git add <conflicted-file>

# 标记冲突已解决（不需要 git rebase --continue，stash pop 不是 rebase）
# 直接验证文件内容是否正确，然后继续工作

# 不需要 push stash 的改动，WIP 继续在工作区
```

---

## 执行前诊断

每次操作前先运行诊断，确认当前状态：

```bash
echo "=== Branch ===" && git branch -v
echo "=== Status ===" && git status --short
echo "=== Ahead/Behind ===" && git log --oneline origin/main..HEAD
echo "=== Remote Ahead ===" && git log --oneline HEAD..origin/main
echo "=== Stash ===" && git stash list
```

根据输出判断走哪个场景：

| 状态 | 场景 |
|------|------|
| 工作区干净，本地无新提交，远端有新提交 | B |
| 工作区干净，本地有提交，远端无新提交 | 直接 push |
| 工作区干净，本地有提交，远端也有新提交 | C（2a） |
| 工作区有 WIP，需要推送已暂存内容 | A + C（2b） |
| 工作区有 WIP，只需同步远端 | B（2b） |

---

## Investment-Manager 项目特定规则

### 永远不要提交的文件

```
backend/venv/          ← Python 虚拟环境（.gitignore 已覆盖）
frontend/node_modules/ ← JS 依赖
frontend/.next/        ← Next.js 构建产物
frontend/next-env.d.ts ← Next.js 自动生成（.gitignore 已覆盖）
*.db / investr.db      ← 本地数据库
.env                   ← 环境变量（含密钥）
pgdata/                ← Postgres 数据目录
```

### 提交前检查命令

```bash
git diff --cached --stat   # 确认暂存内容
git status --short          # 确认没有意外文件混入
```

### 推荐的分支策略（多终端开发）

目前只有 `main` 分支。为避免冲突，建议：

- **功能开发**：在本地创建短生命周期特性分支，完成后 merge 到 main
  ```bash
  git checkout -b feat/portfolio-snapshot
  # ... 开发 ...
  git checkout main && git merge feat/portfolio-snapshot && git push
  git branch -d feat/portfolio-snapshot
  ```
- **文档/配置类改动**：直接在 main 提交

---

## 快速参考卡

```
开工前同步：   git pull --rebase origin main
提交：         git add <具体文件> → git commit -m "type: ..."
推送：         git push origin main
被拒绝时：     git pull --rebase origin main → git push origin main
有WIP被拒绝： git stash push -u -m "wip: ..." → pull rebase → stash pop → push
查看stash：   git stash list
```
