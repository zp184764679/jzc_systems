# GPU 加速安装指南

## 🎯 当前状态
- **PyTorch**: `2.8.0+cpu` ❌ CPU版本
- **PaddlePaddle**: `3.2.1` ❌ 可能是CPU版本
- **CUDA**: 未检测到

---

## 📋 前置要求

### 1. 检查显卡
```bash
# 打开设备管理器 -> 显示适配器
# 或运行：
nvidia-smi
```

确认你的NVIDIA显卡型号和驱动版本。

### 2. 安装 CUDA Toolkit

**推荐版本**: CUDA 12.1 或 12.4

下载地址：https://developer.nvidia.com/cuda-downloads

```bash
# 验证安装
nvcc --version
nvidia-smi
```

---

## 🚀 安装 GPU 版本

### Step 1: 卸载 CPU 版本

```bash
cd C:\Users\Admin\Desktop\采购\backend

# 卸载CPU版PyTorch
pip uninstall torch torchvision torchaudio

# 卸载PaddlePaddle
pip uninstall paddlepaddle
```

### Step 2: 安装 GPU 版 PyTorch

```bash
# PyTorch 2.8.0 + CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 或 CUDA 12.4
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

**验证安装**:
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"Device name: {torch.cuda.get_device_name(0)}")
```

### Step 3: 安装 GPU 版 PaddlePaddle

```bash
# CUDA 12.3
pip install paddlepaddle-gpu==3.2.1 -i https://mirror.baidu.com/pypi/simple

# 或从官网选择版本：
# https://www.paddlepaddle.org.cn/install/quick
```

**验证安装**:
```python
import paddle
print(f"Paddle compiled with CUDA: {paddle.is_compiled_with_cuda()}")
print(f"GPU count: {paddle.device.cuda.device_count()}")
```

---

## ⚡ Ollama GPU 加速

### 安装 Ollama（已支持GPU）

```bash
# Windows 下载
https://ollama.com/download/windows

# 安装后启动
ollama serve

# 拉取模型（自动使用GPU）
ollama pull qwen2.5:7b
```

### 验证 GPU 使用

```bash
# 运行模型时查看GPU使用
nvidia-smi

# 应该看到 ollama.exe 占用GPU显存
```

---

## 🔧 配置检查清单

### ✅ 完成后检查

1. **PyTorch GPU**:
```bash
python -c "import torch; print(torch.cuda.is_available())"
# 输出: True
```

2. **PaddlePaddle GPU**:
```bash
python -c "import paddle; print(paddle.device.cuda.device_count())"
# 输出: 1 (或你的GPU数量)
```

3. **Ollama**:
```bash
curl http://localhost:11434/api/tags
# 应返回模型列表
```

4. **重启后端，查看日志**:
```bash
cd C:\Users\Admin\Desktop\采购\backend
python app.py

# 应该看到：
# ✅ PaddleOCR初始化成功 (Device: GPU (NVIDIA GeForce RTX ...))
# ✅ Ollama 后端初始化成功
```

---

## 📊 性能对比

| 组件 | CPU | GPU | 加速比 |
|------|-----|-----|--------|
| PaddleOCR 发票识别 | ~2-3秒 | ~0.3-0.5秒 | 5-10x |
| Ollama AI分类 | ~5-10秒 | ~0.5-1秒 | 10-20x |
| 总体用户体验 | 慢 😞 | 流畅 🚀 | - |

---

## ⚠️ 故障排查

### 问题1: `torch.cuda.is_available()` 返回 False

**可能原因**:
1. CUDA驱动版本不匹配
2. PyTorch和CUDA版本不匹配
3. 环境变量未设置

**解决**:
```bash
# 检查CUDA版本
nvcc --version
nvidia-smi  # 查看CUDA Driver Version

# 重新安装匹配版本的PyTorch
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### 问题2: PaddleOCR 仍使用CPU

**检查**:
```python
import paddle
print(paddle.device.get_device())  # 应输出 'gpu:0'
```

**强制使用GPU**:
```python
paddle.device.set_device('gpu:0')
```

### 问题3: Ollama GPU显存不足

**解决**: 减少模型大小
```bash
# 使用更小的模型
ollama pull qwen2.5:3b  # 3B参数 (替代 7B)
```

---

## 🎯 推荐配置

**最佳性能**:
- CUDA 12.1+
- PyTorch 2.8.0 GPU
- PaddlePaddle 3.2.1 GPU
- Ollama + qwen2.5:7b (GPU)

**最低要求**:
- NVIDIA GPU (4GB+ 显存)
- CUDA 11.8+
- 对应的GPU版本库

---

完成上述步骤后，你的AI/OCR组件将全部运行在GPU上，性能提升5-20倍！🚀
