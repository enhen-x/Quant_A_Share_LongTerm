# Git 上传脚本
# 使用方法：删除 .git/index.lock 文件后运行此脚本

Write-Host "开始上传代码到 GitHub..." -ForegroundColor Green

# 检查锁文件
if (Test-Path ".git/index.lock") {
    Write-Host "警告：发现 .git/index.lock 文件，正在尝试删除..." -ForegroundColor Yellow
    try {
        Remove-Item ".git/index.lock" -Force -ErrorAction Stop
        Write-Host "锁文件已删除" -ForegroundColor Green
    } catch {
        Write-Host "无法删除锁文件，请手动删除后再运行此脚本" -ForegroundColor Red
        Write-Host "文件路径: $PWD\.git\index.lock" -ForegroundColor Red
        exit 1
    }
}

# 添加所有更改
Write-Host "`n正在添加所有更改..." -ForegroundColor Cyan
git add -A
if ($LASTEXITCODE -ne 0) {
    Write-Host "添加文件失败" -ForegroundColor Red
    exit 1
}

# 显示将要提交的文件
Write-Host "`n将要提交的文件：" -ForegroundColor Cyan
git status --short

# 提交更改
Write-Host "`n正在提交更改..." -ForegroundColor Cyan
$commitMessage = "Update code: add research modules and analysis scripts"
git commit -m $commitMessage
if ($LASTEXITCODE -ne 0) {
    Write-Host "提交失败" -ForegroundColor Red
    exit 1
}

# 推送到 GitHub
Write-Host "`n正在推送到 GitHub..." -ForegroundColor Cyan
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "推送失败，请检查网络连接和权限" -ForegroundColor Red
    exit 1
}

Write-Host "`n代码已成功上传到 GitHub！" -ForegroundColor Green
