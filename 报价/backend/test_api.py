# test_api.py
"""
完整的API测试脚本
测试图纸上传、OCR识别、材料查询、工艺查询等功能
"""
import requests
import os
import sys

# API基础URL
BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("\n" + "="*60)
    print("1. 测试健康检查")
    print("="*60)

    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

    assert response.status_code == 200
    print("✅ 健康检查通过")


def test_materials():
    """测试材料库API"""
    print("\n" + "="*60)
    print("2. 测试材料库API")
    print("="*60)

    # 获取材料列表
    response = requests.get(f"{BASE_URL}/api/materials")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"材料总数: {data['total']}")
    print(f"返回数量: {len(data['items'])}")

    if data['items']:
        print(f"\n前3种材料:")
        for material in data['items'][:3]:
            print(f"  - {material['material_code']}: {material['material_name']} "
                  f"(密度: {material['density']} g/cm³, 价格: ¥{material['price_per_kg']}/kg)")

    # 获取材料类别
    response = requests.get(f"{BASE_URL}/api/materials/categories")
    categories = response.json()['categories']
    print(f"\n材料类别: {', '.join(categories)}")

    # 搜索材料
    response = requests.get(f"{BASE_URL}/api/materials?search=SUS303")
    data = response.json()
    if data['items']:
        sus303 = data['items'][0]
        print(f"\n查询SUS303:")
        print(f"  名称: {sus303['material_name']}")
        print(f"  密度: {sus303['density']} g/cm³")
        print(f"  硬度: {sus303['hardness']}")
        print(f"  价格: ¥{sus303['price_per_kg']}/kg")

    print("✅ 材料库API测试通过")


def test_processes():
    """测试工艺库API"""
    print("\n" + "="*60)
    print("3. 测试工艺库API")
    print("="*60)

    # 获取工艺列表
    response = requests.get(f"{BASE_URL}/api/processes")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"工艺总数: {data['total']}")

    if data['items']:
        print(f"\n前5种工艺:")
        for process in data['items'][:5]:
            print(f"  - {process['process_code']}: {process['process_name']} "
                  f"(类别: {process['category']}, 工时费率: ¥{process['hourly_rate']}/小时)")

    # 获取工艺类别
    response = requests.get(f"{BASE_URL}/api/processes/categories")
    categories = response.json()['categories']
    print(f"\n工艺类别: {', '.join(categories)}")

    # 工艺推荐
    response = requests.get(f"{BASE_URL}/api/processes/recommend/SUS303")
    data = response.json()
    print(f"\n针对SUS303材质的推荐工艺:")
    for process in data['recommended_processes']:
        print(f"  - {process['name']} (费率: ¥{process['hourly_rate']}/小时)")

    print("✅ 工艺库API测试通过")


def test_drawing_upload():
    """测试图纸上传和OCR识别"""
    print("\n" + "="*60)
    print("4. 测试图纸上传和OCR识别")
    print("="*60)

    # 查找测试PDF文件
    test_pdf = r"C:\Users\Admin\Desktop\报价\8001-0003095捻钞辊轴CPN01802-不锈钢材质.pdf"

    if not os.path.exists(test_pdf):
        print(f"⚠️  测试文件不存在: {test_pdf}")
        print("跳过图纸上传测试")
        return None

    print(f"📄 上传图纸: {os.path.basename(test_pdf)}")

    # 上传图纸
    with open(test_pdf, 'rb') as f:
        files = {'file': (os.path.basename(test_pdf), f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/api/drawings/upload", files=files)

    print(f"状态码: {response.status_code}")

    if response.status_code == 201:
        drawing = response.json()
        drawing_id = drawing['id']
        print(f"✅ 图纸上传成功, ID: {drawing_id}")
        print(f"   图号: {drawing['drawing_number']}")
        print(f"   文件大小: {drawing['file_size']} bytes")
        print(f"   OCR状态: {drawing['ocr_status']}")

        # 触发OCR识别
        print(f"\n🤖 触发OCR识别...")
        response = requests.post(f"{BASE_URL}/api/drawings/{drawing_id}/ocr")

        if response.status_code == 200:
            ocr_result = response.json()

            if ocr_result['success']:
                print(f"✅ OCR识别成功!")
                print(f"\n识别结果:")
                print(f"  图号: {ocr_result.get('drawing_number', 'N/A')}")
                print(f"  客户: {ocr_result.get('customer_name', 'N/A')}")
                print(f"  产品名称: {ocr_result.get('product_name', 'N/A')}")
                print(f"  客户料号: {ocr_result.get('customer_part_number', 'N/A')}")
                print(f"  材质: {ocr_result.get('material', 'N/A')}")
                print(f"  外径: {ocr_result.get('outer_diameter', 'N/A')}")
                print(f"  长度: {ocr_result.get('length', 'N/A')}")
                print(f"  公差: {ocr_result.get('tolerance', 'N/A')}")
                print(f"  表面粗糙度: {ocr_result.get('surface_roughness', 'N/A')}")

                if ocr_result.get('processes'):
                    print(f"  推荐工艺: {', '.join(ocr_result['processes'])}")

                if ocr_result.get('special_requirements'):
                    print(f"  特殊要求: {ocr_result['special_requirements']}")

                print(f"\n  置信度: {ocr_result.get('confidence', 0):.2%}")
            else:
                print(f"❌ OCR识别失败: {ocr_result.get('error')}")
        else:
            print(f"❌ OCR请求失败: {response.status_code}")

        # 获取图纸详情
        print(f"\n📋 获取图纸详情...")
        response = requests.get(f"{BASE_URL}/api/drawings/{drawing_id}")
        if response.status_code == 200:
            drawing = response.json()
            print(f"✅ 图纸详情获取成功")
            print(f"   OCR状态: {drawing['ocr_status']}")

        print("✅ 图纸上传和OCR测试完成")
        return drawing_id
    else:
        print(f"❌ 图纸上传失败: {response.json()}")
        return None


def test_drawing_list():
    """测试图纸列表"""
    print("\n" + "="*60)
    print("5. 测试图纸列表")
    print("="*60)

    response = requests.get(f"{BASE_URL}/api/drawings")
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"图纸总数: {data['total']}")

        if data['items']:
            print(f"\n图纸列表:")
            for drawing in data['items']:
                print(f"  - ID: {drawing['id']}, 图号: {drawing['drawing_number']}, "
                      f"客户: {drawing.get('customer_name', 'N/A')}, "
                      f"OCR状态: {drawing['ocr_status']}")

        print("✅ 图纸列表测试通过")


def main():
    """主测试函数"""
    print("🚀 开始API测试")
    print(f"API地址: {BASE_URL}")

    try:
        # 1. 健康检查
        test_health()

        # 2. 材料库测试
        test_materials()

        # 3. 工艺库测试
        test_processes()

        # 4. 图纸上传和OCR测试
        drawing_id = test_drawing_upload()

        # 5. 图纸列表测试
        test_drawing_list()

        print("\n" + "="*60)
        print("✅ 所有测试完成!")
        print("="*60)

        if drawing_id:
            print(f"\n💡 提示:")
            print(f"   - 查看API文档: {BASE_URL}/docs")
            print(f"   - 查看图纸详情: {BASE_URL}/api/drawings/{drawing_id}")

    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败! 请确保后端服务正在运行:")
        print("   cd backend")
        print("   python main.py")
        sys.exit(1)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
