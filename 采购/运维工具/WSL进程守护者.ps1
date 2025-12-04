# ============================================================
# WSL采购系统进程守护者 - 自动监控和重启 (含Ollama)
# ============================================================

# 配置守护参数
$CHECK_INTERVAL = 10  # 检查间隔（秒）
$WSL_DISTRO = "Ubuntu-22.04"
$PROJECT_PATH = "/home/admin/caigou-prod"

# 日志文件
$LOG_FILE = "C:\Users\Admin\Desktop\采购\运维工具\守护者日志.txt"

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor Cyan
    Add-Content -Path $LOG_FILE -Value $logMessage
}

function Check-WSLProcess {
    param($ProcessName, $SearchPattern)

    $result = wsl -d $WSL_DISTRO -- bash -c "ps aux | grep '$SearchPattern' | grep -v grep | wc -l"
    return [int]$result -gt 0
}

function Check-SystemdService {
    param($ServiceName)

    $result = wsl -d $WSL_DISTRO -- bash -c "systemctl is-active $ServiceName 2>/dev/null"
    return $result -eq "active"
}

function Start-OllamaService {
    Write-Log "检测到Ollama服务停止，正在重启..."
    wsl -d $WSL_DISTRO -- bash -c "sudo systemctl restart ollama"
    Start-Sleep -Seconds 3
    Write-Log "✅ Ollama服务已重启"
}

function Start-BackendService {
    Write-Log "检测到后端服务停止，正在重启..."
    wsl -d $WSL_DISTRO -- bash -c "sudo systemctl restart caigou-backend"
    Start-Sleep -Seconds 3
    Write-Log "✅ 后端服务已重启"
}

function Start-FrontendService {
    Write-Log "检测到前端服务停止，正在重启..."
    wsl -d $WSL_DISTRO -- bash -c "sudo systemctl restart caigou-frontend"
    Start-Sleep -Seconds 3
    Write-Log "✅ 前端服务已重启"
}

function Start-CeleryService {
    Write-Log "检测到Celery服务停止，正在重启..."
    wsl -d $WSL_DISTRO -- bash -c "sudo systemctl restart caigou-celery"
    Start-Sleep -Seconds 3
    Write-Log "✅ Celery服务已重启"
}

# 主监控循环
Write-Log "======================================"
Write-Log "WSL采购系统进程守护者已启动 (含Ollama)"
Write-Log "监控间隔: $CHECK_INTERVAL 秒"
Write-Log "WSL发行版: $WSL_DISTRO"
Write-Log "======================================"

$consecutiveFailures = 0
$maxConsecutiveFailures = 3

while ($true) {
    try {
        # 检查WSL是否运行
        $wslRunning = wsl -l --running | Select-String $WSL_DISTRO

        if (-not $wslRunning) {
            Write-Log "⚠️  WSL未运行，等待WSL启动..."
            Start-Sleep -Seconds $CHECK_INTERVAL
            continue
        }

        # 检查Ollama服务
        $ollamaRunning = Check-SystemdService "ollama"
        if (-not $ollamaRunning) {
            Write-Log "⚠️  检测到Ollama服务停止"
            Start-OllamaService
        }

        # 检查Redis服务
        $redisRunning = Check-SystemdService "redis-server"
        if (-not $redisRunning) {
            Write-Log "⚠️  检测到Redis服务停止"
            wsl -d $WSL_DISTRO -- bash -c "sudo systemctl restart redis-server"
            Write-Log "✅ Redis服务已重启"
        }

        # 检查后端服务
        $backendRunning = Check-SystemdService "caigou-backend"
        if (-not $backendRunning) {
            $consecutiveFailures++
            Write-Log "⚠️  检测到后端服务停止 (连续失败: $consecutiveFailures)"
            if ($consecutiveFailures -ge 2) {
                Start-BackendService
                $consecutiveFailures = 0
            }
        }

        # 检查前端服务
        $frontendRunning = Check-SystemdService "caigou-frontend"
        if (-not $frontendRunning) {
            Write-Log "⚠️  检测到前端服务停止"
            Start-FrontendService
        }

        # 检查Celery服务
        $celeryRunning = Check-SystemdService "caigou-celery"
        if (-not $celeryRunning) {
            Write-Log "⚠️  检测到Celery服务停止"
            Start-CeleryService
        }

        # 所有服务正常
        if ($ollamaRunning -and $redisRunning -and $backendRunning -and $frontendRunning -and $celeryRunning) {
            if ($consecutiveFailures -eq 0) {
                # Write-Log "✅ 所有服务运行正常 (Ollama + Redis + Backend + Frontend + Celery)"
            }
            $consecutiveFailures = 0
        }

    }
    catch {
        Write-Log "❌ 监控出错: $($_.Exception.Message)"
    }

    Start-Sleep -Seconds $CHECK_INTERVAL
}
