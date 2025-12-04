# -*- coding: utf-8 -*-
"""
初始化PaddleOCR并下载模型文件
"""
import os
import sys

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

def download_ocr_models():
    """下载PaddleOCR模型文件"""
    print("=" * 60)
    print("🚀 开始下载PaddleOCR模型文件...")
    print("=" * 60)
    print()

    try:
        # 检查PaddlePaddle
        print("[1/4] 检查PaddlePaddle...")
        import paddle
        print(f"✅ PaddlePaddle {paddle.__version__} 已安装")

        # 检查GPU
        use_gpu = paddle.device.cuda.device_count() > 0
        if use_gpu:
            device_name = paddle.device.cuda.get_device_name(0)
            print(f"✅ 检测到GPU: {device_name}")
        else:
            print("ℹ️  未检测到GPU，将使用CPU模式")
        print()

        # 检查PaddleOCR
        print("[2/4] 检查PaddleOCR...")
        import paddleocr
        print(f"✅ PaddleOCR {paddleocr.__version__} 已安装")
        print()

        # 初始化PaddleOCR（这会自动下载模型）
        print("[3/4] 初始化PaddleOCR（首次运行会下载模型，请耐心等待）...")
        print("⏳ 正在下载检测模型、识别模型和方向分类器...")
        print("ℹ️  提示：如果下载缓慢，模型文件会缓存到本地，之后无需重复下载")
        print()

        from paddleocr import PaddleOCR

        # 创建OCR实例 - 会自动下载模型
        # PaddleOCR 3.3.1使用新的参数
        ocr = PaddleOCR(
            ocr_version='PP-OCRv4',  # 使用最新的PP-OCRv4模型
            lang='ch',              # 中文
            use_gpu=use_gpu,        # 使用GPU（如果可用）
            use_angle_cls=True,     # 启用方向分类器
            show_log=True           # 显示日志
        )

        print()
        print("✅ OCR引擎初始化成功！")
        print()

        # 测试OCR
        print("[4/4] 测试OCR功能...")
        print("ℹ️  创建测试图片...")

        # 创建一个简单的测试图片
        from PIL import Image, ImageDraw, ImageFont
        import io

        # 创建测试图片
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)

        # 尝试使用系统字体
        try:
            # Windows系统字体路径
            font_paths = [
                r"C:\Windows\Fonts\msyh.ttc",  # 微软雅黑
                r"C:\Windows\Fonts\simsun.ttc",  # 宋体
                r"C:\Windows\Fonts\simhei.ttf",  # 黑体
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 32)
                    break

            if font is None:
                # 如果找不到字体，使用默认字体
                font = ImageFont.load_default()
                draw.text((20, 30), "Test Invoice 12345678", fill='black', font=font)
            else:
                draw.text((20, 30), "测试发票 12345678", fill='black', font=font)
        except Exception as e:
            # 使用默认字体
            draw.text((20, 30), "Test 12345678", fill='black')

        # 保存测试图片
        test_img_path = os.path.join(backend_dir, 'test_ocr.png')
        img.save(test_img_path)
        print(f"✅ 测试图片已创建: {test_img_path}")

        # 执行OCR识别
        print("⏳ 正在识别测试图片...")
        result = ocr.ocr(test_img_path, cls=True)

        # 解析结果
        if result and len(result) > 0 and result[0]:
            ocr_result = result[0]

            # 提取文本
            recognized_texts = []
            if hasattr(ocr_result, 'json'):
                # 新格式
                if 'rec_texts' in ocr_result.json:
                    recognized_texts = ocr_result.json['rec_texts']
            else:
                # 旧格式
                for line in ocr_result:
                    if isinstance(line, (list, tuple)) and len(line) >= 2:
                        text_data = line[1]
                        if isinstance(text_data, (list, tuple)) and len(text_data) >= 1:
                            recognized_texts.append(str(text_data[0]))

            if recognized_texts:
                print(f"✅ OCR识别成功！识别到 {len(recognized_texts)} 行文本:")
                for idx, text in enumerate(recognized_texts, 1):
                    print(f"   {idx}. {text}")
            else:
                print("⚠️  OCR未识别到文本，但引擎运行正常")
        else:
            print("⚠️  OCR返回空结果，但引擎运行正常")

        # 清理测试文件
        if os.path.exists(test_img_path):
            os.remove(test_img_path)
            print(f"✅ 测试文件已清理")

        print()
        print("=" * 60)
        print("🎉 PaddleOCR配置完成！")
        print("=" * 60)
        print()
        print("📊 系统信息:")
        print(f"   - PaddlePaddle: {paddle.__version__}")
        print(f"   - PaddleOCR: {paddleocr.__version__}")
        print(f"   - 运行设备: {'GPU' if use_gpu else 'CPU'}")
        print(f"   - 模型已下载: ✅")
        print()
        print("✅ 现在可以使用发票OCR自动识别功能了！")
        print()

        return True

    except ImportError as e:
        print(f"❌ 导入失败: {str(e)}")
        print()
        print("请确保已安装以下依赖:")
        print("  pip install paddlepaddle")
        print("  pip install paddleocr")
        print("  pip install Pillow")
        return False

    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        import traceback
        print()
        print("详细错误:")
        traceback.print_exc()
        print()
        print("可能的原因:")
        print("1. 网络连接问题 - 无法下载模型文件")
        print("2. 磁盘空间不足 - 模型文件需要约200MB空间")
        print("3. 防火墙阻止 - 允许Python访问网络")
        print()
        print("解决方案:")
        print("1. 检查网络连接")
        print("2. 尝试使用VPN或代理")
        print("3. 手动下载模型文件并放置到 %USERPROFILE%/.paddleocr 目录")
        return False

if __name__ == '__main__':
    success = download_ocr_models()
    sys.exit(0 if success else 1)
