# 🚁 无人机资讯网站自动化部署指南

## 当前状态
✅ 静态网站已成功部署在 Cloudflare Pages  
🔗 访问地址：https://drone-information.pages.dev/

---

## 📋 完整的自动化部署流程

### 方法一：本地采集 + GitHub Actions 发布（推荐）

这是最完整的方案，包含数据采集、网站生成和部署的全流程。

#### 1. 本地数据采集（您的电脑上）

```bash
# 运行数据采集程序
python drone_scout.py

# 或使用批处理脚本
start_server.bat
```

#### 2. 更新数据库和静态网站

```bash
# 生成最新的静态网站
python static_site_generator.py

# 将变更提交到 git
git add data/ static_site/
git commit -m "chore: 更新资讯数据和静态网站"
git push
```

#### 3. GitHub Actions 自动触发

一旦您推送到 GitHub，会自动：
1. 触发 GitHub Actions 工作流
2. Cloudflare Pages 检测到新的提交
3. 自动重新部署网站（约 1-2 分钟）

---

### 方法二：仅使用 GitHub Actions（无需本地操作）

注意：此方法需要数据库文件已在 git 仓库中（需要修改 `.gitignore`）。

#### 配置步骤：

1. **取消数据库文件的忽略**（可选，不推荐，因为数据库文件较大）

编辑 `.gitignore`，注释掉这一行：
```
# data/*.db  # 注释掉这行
```

2. **提交数据库文件**（可选）

```bash
git add -f data/drone_scout.db
git commit -m "feat: 添加数据库文件"
git push
```

3. **GitHub Actions 定时运行**

工作流已配置为每天 UTC 时间 00:00 运行（北京时间 08:00），它会：
- 运行 `static_site_generator.py` 生成静态网站
- 检测文件是否有变更
- 有变更则自动提交和推送

---

## 🔧 已配置的 GitHub Actions

工作流文件位置：[`.github/workflows/deploy-static-site.yml`](file:///e:\TRAE_PROJECT\UAV_info_collect\.github\workflows\deploy-static-site.yml)

### 触发方式：
1. **推送到 main/master 分支** - 自动触发
2. **定时任务** - 每天 UTC 00:00（北京时间 08:00）
3. **手动触发** - 在 GitHub Actions 页面手动运行

---

## 📊 Cloudflare Pages 配置确认

请确认您的 Cloudflare Pages 设置：

1. 项目名称：`drone-information`
2. 构建输出目录：`static_site` ✅
3. 生产分支：`main` 或 `master`
4. 构建命令：（留空）

---

## 🚀 日常使用建议

### 日常更新流程：

```bash
# 1. 采集新数据（本地运行）
python drone_scout.py

# 2. 生成静态网站
python static_site_generator.py

# 3. 提交并推送
git add data/ static_site/
git commit -m "chore: 更新资讯 [$(date +%Y-%m-%d)]"
git push

# 4. Cloudflare Pages 自动部署完成！
```

---

## 💡 其他优化建议

### 1. 使用批处理脚本一键更新

可以创建一个 `update_and_deploy.bat` 脚本，自动完成上述步骤。

### 2. 配置网站访问分析

在 Cloudflare Pages 中启用 Web Analytics，查看访问量。

### 3. 自定义域名

在 Cloudflare Pages 项目设置 → Custom domains 中绑定您的域名。

---

## ❓ 常见问题

**Q: 数据库文件太大怎么办？**  
A: 建议只提交静态网站文件（`static_site/`），数据库保留在本地。

**Q: 如何查看部署日志？**  
A: 在 GitHub 仓库 → Actions 页面查看工作流运行历史。

**Q: 部署失败怎么办？**  
A: 检查：1) 数据库是否存在 2) 依赖是否完整 3) 静态网站是否成功生成
