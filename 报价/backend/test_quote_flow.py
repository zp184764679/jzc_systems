# test_quote_flow.py
"""
完整报价流程测试
测试从图纸上传到报价单生成的完整流程
"""
import requests
import os
import sys
import time

BASE_URL = "http://localhost:8000"

def test_complete_quote_flow():
    """测试完整报价流程"""
    print("=" * 80)
    print("🚀 测试完整报价流程")
    print("=" * 80)

    # ==================== 第1步：上传图纸 ====================
    print("\n【步骤1】上传图纸")
    print("-" * 80)

    test_pdf = r"C:\Users\Admin\Desktop\报价\8001-0003095捻钞辊轴CPN01802-不锈钢材质.pdf"

    if not os.path.exists(test_pdf):
        print(f"❌ 测试文件不存在: {test_pdf}")
        return False

    with open(test_pdf, 'rb') as f:
        files = {'file': (os.path.basename(test_pdf), f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/api/drawings/upload", files=files)

    if response.status_code != 201:
        print(f"❌ 上传失败: {response.json()}")
        return False

    drawing = response.json()
    drawing_id = drawing['id']
    print(f"✅ 图纸上传成功, ID: {drawing_id}")

    # ==================== 第2步：OCR识别 ====================
    print("\n【步骤2】OCR识别图纸")
    print("-" * 80)
    print("⏳ 识别中，请稍候（约10-30秒）...")

    response = requests.post(f"{BASE_URL}/api/drawings/{drawing_id}/ocr")

    if response.status_code != 200:
        print(f"❌ OCR识别失败: {response.json()}")
        return False

    ocr_result = response.json()

    if ocr_result['success']:
        print(f"✅ OCR识别成功")
        print(f"   图号: {ocr_result.get('drawing_number', 'N/A')}")
        print(f"   客户: {ocr_result.get('customer_name', 'N/A')}")
        print(f"   产品: {ocr_result.get('product_name', 'N/A')}")
        print(f"   材质: {ocr_result.get('material', 'N/A')}")
        print(f"   外径: {ocr_result.get('outer_diameter', 'N/A')}")
        print(f"   长度: {ocr_result.get('length', 'N/A')}")
    else:
        print(f"❌ OCR识别失败: {ocr_result.get('error')}")
        return False

    # ==================== 第3步：计算报价 ====================
    print("\n【步骤3】自动计算报价")
    print("-" * 80)

    params = {
        "drawing_id": drawing_id,
        "lot_size": 2000
    }

    response = requests.post(f"{BASE_URL}/api/quotes/calculate", params=params)

    if response.status_code != 200:
        print(f"❌ 报价计算失败: {response.json()}")
        return False

    quote_calc = response.json()

    if quote_calc['success']:
        print(f"✅ 报价计算成功\n")

        quote_data = quote_calc['quote']
        material_data = quote_calc['material']
        process_data = quote_calc['process']

        print(f"📊 报价明细:")
        print(f"   材料成本: ¥{quote_data['material_cost']:.4f}")
        print(f"     - 单件重量: {material_data['weight_per_piece']:.2f}g")
        print(f"     - 材料单价: 根据材料库")

        print(f"\n   加工成本: ¥{quote_data['process_cost']:.4f}")
        print(f"     - 工序数量: {len(process_data['process_details'])}")
        for proc in process_data['process_details']:
            print(f"       • {proc['process_name']}: ¥{proc['process_cost']:.4f}")

        print(f"\n   其他费用: ¥{quote_data['other_cost']:.4f}")
        print(f"   管理费: ¥{quote_data['management_cost']:.4f} ({quote_data['rates']['management_rate']*100:.1f}%)")
        print(f"   利润: ¥{quote_data['profit']:.4f} ({quote_data['rates']['profit_rate']*100:.1f}%)")

        print(f"\n   {'='*40}")
        print(f"   单价: ¥{quote_data['total_price']:.4f} /件")
        print(f"   批量: {quote_calc['lot_size']} 件")
        print(f"   总金额: ¥{quote_data['total_price'] * quote_calc['lot_size']:,.2f}")
        print(f"   {'='*40}")

    else:
        print(f"❌ 报价计算失败: {quote_calc.get('error')}")
        return False

    # ==================== 第4步：保存报价单 ====================
    print("\n【步骤4】保存报价单")
    print("-" * 80)

    save_data = {
        "drawing_id": drawing_id,
        "calculation_result": quote_calc
    }

    response = requests.post(f"{BASE_URL}/api/quotes/save", json=save_data)

    if response.status_code != 201:
        print(f"❌ 保存失败: {response.json()}")
        return False

    saved_quote = response.json()
    quote_id = saved_quote['id']
    quote_number = saved_quote['quote_number']

    print(f"✅ 报价单已保存")
    print(f"   报价单号: {quote_number}")
    print(f"   报价单ID: {quote_id}")
    print(f"   状态: {saved_quote['status']}")
    print(f"   有效期至: {saved_quote.get('valid_until', 'N/A')}")

    # ==================== 第5步：导出报价单 ====================
    print("\n【步骤5】导出报价单")
    print("-" * 80)

    # 导出Excel
    print("📄 导出Excel...")
    excel_url = f"{BASE_URL}/api/quotes/{quote_id}/export/excel"
    excel_response = requests.get(excel_url)

    if excel_response.status_code == 200:
        excel_filename = f"test_quote_{quote_number}.xlsx"
        with open(excel_filename, 'wb') as f:
            f.write(excel_response.content)
        print(f"✅ Excel报价单已生成: {excel_filename}")
    else:
        print(f"⚠️  Excel导出失败")

    # 导出PDF
    print("📄 导出PDF...")
    pdf_url = f"{BASE_URL}/api/quotes/{quote_id}/export/pdf"
    pdf_response = requests.get(pdf_url)

    if pdf_response.status_code == 200:
        pdf_filename = f"test_quote_{quote_number}.pdf"
        with open(pdf_filename, 'wb') as f:
            f.write(pdf_response.content)
        print(f"✅ PDF报价单已生成: {pdf_filename}")
    else:
        print(f"⚠️  PDF导出失败")

    # ==================== 第6步：查询报价列表 ====================
    print("\n【步骤6】查询报价列表")
    print("-" * 80)

    response = requests.get(f"{BASE_URL}/api/quotes")

    if response.status_code == 200:
        quotes_list = response.json()
        print(f"✅ 报价单总数: {quotes_list['total']}")

        if quotes_list['items']:
            print(f"\n最近的报价单:")
            for quote in quotes_list['items'][:3]:
                print(f"   • {quote['quote_number']} - {quote['customer_name']} - ¥{quote['total_amount']:.2f}")
    else:
        print(f"⚠️  查询失败")

    # ==================== 完成 ====================
    print("\n" + "=" * 80)
    print("✅ 完整报价流程测试成功！")
    print("=" * 80)

    print(f"\n📌 测试结果总结:")
    print(f"   图纸ID: {drawing_id}")
    print(f"   报价单ID: {quote_id}")
    print(f"   报价单号: {quote_number}")
    print(f"   单价: ¥{quote_data['total_price']:.4f}")
    print(f"   总金额: ¥{quote_data['total_price'] * quote_calc['lot_size']:,.2f}")

    print(f"\n📁 生成的文件:")
    if os.path.exists(f"test_quote_{quote_number}.xlsx"):
        print(f"   • test_quote_{quote_number}.xlsx")
    if os.path.exists(f"test_quote_{quote_number}.pdf"):
        print(f"   • test_quote_{quote_number}.pdf")

    print(f"\n🌐 相关链接:")
    print(f"   查看报价详情: {BASE_URL}/api/quotes/{quote_id}")
    print(f"   API文档: {BASE_URL}/docs")

    return True


def main():
    """主函数"""
    try:
        print("\n🔍 检查后端服务...")
        response = requests.get(f"{BASE_URL}/health", timeout=3)
        if response.status_code == 200:
            print("✅ 后端服务运行正常\n")
        else:
            print("❌ 后端服务异常\n")
            return

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务!")
        print("请确保后端正在运行: python main.py")
        sys.exit(1)

    success = test_complete_quote_flow()

    if success:
        print("\n✨ 所有测试通过！系统运行正常！")
    else:
        print("\n❌ 测试失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
