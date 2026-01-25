# 上传代码到 GitHub 的步骤

## 当前问题
存在 `.git/index.lock` 锁文件，阻止了 git 操作。这通常是因为之前的 git 进程异常退出导致的。

## 解决步骤

### 1. 删除锁文件
请按照以下方式之一删除锁文件：

**方法 1：在文件资源管理器中**
- 打开文件资源管理器
- 导航到项目目录：`G:\理财\Quant_A_share_position_manage`
- 进入 `.git` 文件夹（可能需要显示隐藏文件）
- 删除 `index.lock` 文件

**方法 2：使用 PowerShell（以管理员身份运行）**
```powershell
cd "G:\理财\Quant_A_share_position_manage"
Remove-Item -Path ".git\index.lock" -Force
```

**方法 3：使用命令提示符（以管理员身份运行）**
```cmd
cd /d "G:\理财\Quant_A_share_position_manage"
del /f /q .git\index.lock
```

### 2. 执行 Git 操作
删除锁文件后，在项目目录中执行以下命令：

```powershell
# 添加所有更改
git add -A

# 提交更改
git commit -m "Update code: add research modules and analysis scripts"

# 推送到 GitHub
git push origin main
```

## 待提交的文件
- 修改的文件：
  - `scripts/analysis/plot_index_distribution.py`
  - `scripts/data/fetch_industry_data.py`
  - `scripts/data/test_fetch.py` (已删除)

- 新增的文件：
  - `results/`
  - `scripts/__init__.py`
  - `scripts/analysis/RESEARCH_PLAN.md`
  - `scripts/research/__init__.py`
  - `scripts/research/industry_analysis.py`
  - `scripts/research/research/`
  - `scripts/utils/`

## 远程仓库
已配置的远程仓库：`https://github.com/enhen-x/Quant_A_Share_LongTerm.git`
