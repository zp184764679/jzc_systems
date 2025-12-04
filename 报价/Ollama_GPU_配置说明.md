# Ollama GPU 配置说明

## 生产系统配置（WSL）

### 关键配置

1. **Ollama 版本**: 0.12.11 (支持 CUDA)
2. **监听端口**: 11435
3. **GPU**: NVIDIA GeForce RTX 4080 (16GB VRAM)
4. **模型**: qwen3-vl:8b-instruct (14.6GB GPU 内存)

### Systemd 服务配置

```ini
# /etc/systemd/system/ollama.service
[Unit]
Description=Ollama AI Service (WSL Port 11435)
After=network.target

[Service]
Type=simple
User=admin
Group=admin
Environment="HOME=/home/admin"
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="OLLAMA_HOST=0.0.0.0:11435"
Environment="CUDA_VISIBLE_DEVICES=0"
Environment="LD_LIBRARY_PATH=/usr/lib/wsl/lib"
Environment="OLLAMA_ORIGINS=*"
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3
StandardOutput=append:/var/log/ollama.log
StandardError=append:/var/log/ollama.error.log

[Install]
WantedBy=multi-user.target
```

### 重要注意事项

1. **停止 Windows Ollama**: Windows Ollama 会占用 GPU，必须停止才能让 WSL Ollama 使用 GPU
   ```powershell
   Stop-Process -Name "ollama*" -Force
   ```

2. **安装带 CUDA 支持的 Ollama**:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

3. **GPU 检测验证**:
   ```bash
   tail -20 /var/log/ollama.error.log | grep -E "inference compute"
   # 应显示: id=GPU... library=CUDA... name=CUDA0 description="NVIDIA GeForce RTX 4080"
   ```

---

## Windows 开发环境配置

### 方案 1: 使用 Windows 本地 Ollama (推荐开发环境)

1. **修改 OCR 服务配置**:
   ```python
   # backend/services/invoice_ocr_service.py
   self.ollama_base = os.getenv('LLM_BASE', 'http://localhost:11434')  # Windows 默认端口
   ```

2. **启动 Windows Ollama**:
   - 确保 Ollama 应用已安装并运行
   - 默认监听 `localhost:11434`

3. **下载视觉模型**:
   ```bash
   ollama pull qwen3-vl:8b-instruct
   ```

### 方案 2: 使用 WSL Ollama

1. **环境变量配置** (backend/.env):
   ```
   LLM_BASE=http://localhost:11435
   ```

2. **确保 WSL Ollama 运行**:
   ```bash
   wsl -u root systemctl status ollama
   ```

3. **停止 Windows Ollama** (避免 GPU 冲突):
   ```powershell
   Stop-Process -Name "ollama*" -Force
   ```

---

## OCR 服务关键更改

### 1. PaddleOCR 3.x API 兼容

```python
# 旧 API (已废弃)
self.ocr_engine = PaddleOCR(use_gpu=True, use_angle_cls=True)
result = self.ocr_engine.ocr(file_path)

# 新 API (3.x)
self.ocr_engine = PaddleOCR()
result = self.ocr_engine.predict(file_path)
# 返回格式: [{'rec_texts': [...], 'rec_scores': [...]}]
```

### 2. Qwen3-VL Vision OCR

- **优先级**: Qwen3-VL > PaddleOCR > Fallback
- **准确率**: 95%+ (发票号码、金额、税额、销售方等)
- **GPU 内存**: ~14.6GB
- **推理速度**: 2-5秒/张发票

### 3. 服务初始化逻辑

```python
# 检查 Ollama 可用性
self.ollama_available = self._check_ollama()
if self.ollama_available:
    self.ocr_type = 'ollama_vision'
    self.ollama_vision_model = 'qwen3-vl:8b-instruct'
else:
    self.ocr_type = 'paddleocr'  # 降级到 PaddleOCR
```

---

## 测试命令

### 检查 OCR 状态
```bash
curl http://localhost:5001/api/v1/suppliers/public/ocr-status
```

### 测试 Vision OCR
```bash
curl http://localhost:5001/api/v1/suppliers/public/test-vision
```

### 检查 GPU 使用
```bash
# WSL
wsl bash -c "nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader"

# Windows
nvidia-smi
```

---

## 系统整合建议

1. **开发环境**: 使用 Windows Ollama (11434) + 简化配置
2. **生产环境**: 使用 WSL Ollama (11435) + GPU 加速
3. **代码同步**: 确保 OCR 服务代码保持一致
4. **环境变量**: 通过 .env 文件区分端口配置
