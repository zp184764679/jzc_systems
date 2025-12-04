# -*- coding: utf-8 -*-
"""
测试 Qwen3-VL Vision OCR 发票识别
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# 加载.env文件
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, '.env'))

def create_test_invoice():
    """创建测试发票图片"""
    print("📄 创建测试发票图片...")

    # 创建一个简单的发票图片
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)

    # 尝试使用系统字体
    try:
        font_paths = [
            r"C:\Windows\Fonts\msyh.ttc",  # 微软雅黑
            r"C:\Windows\Fonts\simsun.ttc",  # 宋体
        ]
        font_large = None
        font_normal = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                font_large = ImageFont.truetype(font_path, 32)
                font_normal = ImageFont.truetype(font_path, 20)
                break

        if font_large is None:
            font_large = ImageFont.load_default()
            font_normal = ImageFont.load_default()
    except:
        font_large = ImageFont.load_default()
        font_normal = ImageFont.load_default()

    # 绘制发票内容
    y_pos = 30

    # 标题
    draw.text((300, y_pos), "增值税专用发票", fill='black', font=font_large)
    y_pos += 60

    # 发票代码和号码
    draw.text((50, y_pos), "发票代码: 1234567890AB", fill='black', font=font_normal)
    y_pos += 40
    draw.text((50, y_pos), "发票号码: 20250001", fill='black', font=font_normal)
    y_pos += 40
    draw.text((50, y_pos), "开票日期: 2025-11-08", fill='black', font=font_normal)
    y_pos += 60

    # 购买方信息
    draw.text((50, y_pos), "购买方信息:", fill='black', font=font_normal)
    y_pos += 35
    draw.text((70, y_pos), "名称: 测试采购公司有限公司", fill='black', font=font_normal)
    y_pos += 35
    draw.text((70, y_pos), "纳税人识别号: 91110000123456789X", fill='black', font=font_normal)
    y_pos += 60

    # 销售方信息
    draw.text((50, y_pos), "销售方信息:", fill='black', font=font_normal)
    y_pos += 35
    draw.text((70, y_pos), "名称: 测试供应商股份有限公司", fill='black', font=font_normal)
    y_pos += 35
    draw.text((70, y_pos), "纳税人识别号: 91110000987654321M", fill='black', font=font_normal)
    y_pos += 60

    # 金额信息
    draw.text((50, y_pos), "合计金额: ¥10,000.00", fill='black', font=font_normal)
    y_pos += 35
    draw.text((50, y_pos), "合计税额: ¥1,300.00", fill='black', font=font_normal)
    y_pos += 35
    draw.text((50, y_pos), "价税合计: ¥11,300.00", fill='black', font=font_normal)

    # 保存图片
    test_img_path = os.path.join(backend_dir, 'test_invoice.png')
    img.save(test_img_path)
    print(f"✅ 测试发票已创建: {test_img_path}")

    return test_img_path

def test_vision_ocr():
    """测试 Vision OCR"""
    print("=" * 60)
    print("🤖 测试 Qwen3-VL Vision OCR")
    print("=" * 60)
    print()

    try:
        # 创建测试发票
        invoice_path = create_test_invoice()
        print()

        # 导入OCR服务
        print("[1/3] 初始化OCR服务...")
        from services.invoice_ocr_service import get_ocr_service
        ocr_service = get_ocr_service()
        print(f"✅ OCR类型: {ocr_service.ocr_type}")
        print(f"✅ Vision模型: {ocr_service.ollama_vision_model}")
        print()

        # 执行OCR识别
        print("[2/3] 执行发票识别...")
        print("⏳ 调用 Qwen3-VL 模型识别中...")
        result = ocr_service.extract_invoice_info(invoice_path)
        print()

        # 显示结果
        print("[3/3] 识别结果:")
        print("-" * 60)

        if result.get('success'):
            print("✅ 识别成功！")
            print()
            print(f"OCR方法: {result.get('ocr_method', 'unknown')}")
            print(f"置信度: {result.get('confidence', 0)}")
            print()
            print("📋 提取的字段:")
            print(f"  发票代码: {result.get('invoice_code', '未识别')}")
            print(f"  发票号码: {result.get('invoice_number', '未识别')}")
            print(f"  开票日期: {result.get('invoice_date', '未识别')}")
            print(f"  购买方名称: {result.get('buyer_name', '未识别')}")
            print(f"  购买方税号: {result.get('buyer_tax_id', '未识别')}")
            print(f"  销售方名称: {result.get('seller_name', '未识别')}")
            print(f"  销售方税号: {result.get('seller_tax_id', '未识别')}")
            print(f"  不含税金额: ¥{result.get('amount_before_tax', 0):,.2f}")
            print(f"  税额: ¥{result.get('tax_amount', 0):,.2f}")
            print(f"  价税合计: ¥{result.get('total_amount', 0):,.2f}")
        else:
            print("❌ 识别失败")
            print(f"错误: {result.get('error', '未知错误')}")

        print("-" * 60)
        print()

        # 清理测试文件
        if os.path.exists(invoice_path):
            os.remove(invoice_path)
            print("🧹 测试文件已清理")

        print()
        print("=" * 60)
        print("✅ Vision OCR 测试完成")
        print("=" * 60)

        return result.get('success', False)

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_vision_ocr()
    sys.exit(0 if success else 1)
