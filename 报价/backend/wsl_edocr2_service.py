#!/usr/bin/env python3
"""
WSL eDOCr2 OCR微服务
使用 eDOCr2 专业工程图纸OCR + Ollama Vision 进行标题栏识别
"""
import os
import sys
import time
import json
import base64
import logging
import tempfile
import numpy as np
import cv2
from flask import Flask, request, jsonify
from PIL import Image
import requests

# 添加 eDOCr2 路径
sys.path.insert(0, '/home/admin/eDOCr2')

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局模型
edocr2_models = None
ollama_base = "http://localhost:11434"

# eDOCr2 模型路径
MODELS_DIR = '/home/admin/eDOCr2/edocr2/models'
GDT_MODEL = os.path.join(MODELS_DIR, 'recognizer_gdts.keras')
DIM_MODEL = os.path.join(MODELS_DIR, 'recognizer_dimensions.keras')


def init_edocr2():
    """初始化 eDOCr2 模型"""
    global edocr2_models

    try:
        logger.info("Loading eDOCr2 models...")
        start_time = time.time()

        from edocr2.keras_ocr.recognition import Recognizer
        from edocr2.keras_ocr.detection import Detector
        from edocr2 import tools

        # 加载 GD&T 识别器
        logger.info(f"  Loading GD&T recognizer from {GDT_MODEL}...")
        recognizer_gdt = Recognizer(alphabet=tools.ocr_pipelines.read_alphabet(GDT_MODEL))
        recognizer_gdt.model.load_weights(GDT_MODEL)

        # 加载尺寸识别器
        logger.info(f"  Loading dimension recognizer from {DIM_MODEL}...")
        alphabet_dim = tools.ocr_pipelines.read_alphabet(DIM_MODEL)
        recognizer_dim = Recognizer(alphabet=alphabet_dim)
        recognizer_dim.model.load_weights(DIM_MODEL)

        # 加载检测器
        logger.info("  Loading text detector...")
        detector = Detector()

        # 模型预热
        logger.info("  Warming up models...")
        dummy_image = np.zeros((1, 1, 3), dtype=np.float32)
        _ = recognizer_gdt.recognize(dummy_image)
        _ = recognizer_dim.recognize(dummy_image)
        dummy_image = np.zeros((32, 32, 3), dtype=np.float32)
        _ = detector.detect([dummy_image])

        edocr2_models = {
            'recognizer_gdt': recognizer_gdt,
            'recognizer_dim': recognizer_dim,
            'alphabet_dim': alphabet_dim,
            'detector': detector,
            'tools': tools
        }

        load_time = time.time() - start_time
        logger.info(f"eDOCr2 models loaded successfully in {load_time:.2f}s")
        return True

    except Exception as e:
        logger.error(f"Failed to load eDOCr2 models: {e}")
        import traceback
        traceback.print_exc()
        return False


def extract_with_edocr2(image_path: str) -> dict:
    """使用 eDOCr2 提取工程图纸信息（尺寸和GD&T）"""
    global edocr2_models

    if not edocr2_models:
        return {'success': False, 'error': 'eDOCr2 models not loaded'}

    try:
        start_time = time.time()
        tools = edocr2_models['tools']

        # 读取图像
        logger.info(f"Processing image: {image_path}")
        img = cv2.imread(image_path)
        if img is None:
            return {'success': False, 'error': 'Failed to read image'}

        # 图层分割
        logger.info("  Step 1: Layer segmentation...")
        _, frame, gdt_boxes, tables, dim_boxes = tools.layer_segm.segment_img(
            img,
            autoframe=True,
            frame_thres=0.85,
            GDT_thres=0.02,
            binary_thres=127
        )

        process_img = img.copy()
        table_results = []

        # 尝试表格OCR（如果tesseract可用）
        try:
            logger.info("  Step 2: Table OCR (title block)...")
            table_results, updated_tables, process_img = tools.ocr_pipelines.ocr_tables(
                tables, process_img, language='chi_sim+eng'
            )
        except Exception as e:
            logger.warning(f"  Table OCR skipped (tesseract not available): {e}")
            # 跳过表格OCR，继续处理

        # GD&T 识别
        logger.info("  Step 3: GD&T recognition...")
        gdt_results = []
        try:
            gdt_results, updated_gdt_boxes, process_img = tools.ocr_pipelines.ocr_gdt(
                process_img, gdt_boxes, recognizer=edocr2_models['recognizer_gdt']
            )
        except Exception as e:
            logger.warning(f"  GD&T OCR failed: {e}")

        # 尺寸识别
        logger.info("  Step 4: Dimension recognition...")
        dimensions = []
        other_info = []
        try:
            if frame:
                process_img_dim = process_img[frame.y:frame.y+frame.h, frame.x:frame.x+frame.w]
            else:
                process_img_dim = process_img

            dimensions, other_info, _, _ = tools.ocr_pipelines.ocr_dimensions(
                process_img_dim,
                edocr2_models['detector'],
                edocr2_models['recognizer_dim'],
                edocr2_models['alphabet_dim'],
                frame, dim_boxes,
                max_img_size=2048,
                cluster_thres=15
            )
        except Exception as e:
            logger.warning(f"  Dimension OCR failed: {e}")

        # 处理输出
        try:
            table_results, gdt_results, dimensions, other_info = tools.output_tools.process_raw_output(
                None, table_results, gdt_results, dimensions, other_info, save=False
            )
        except Exception as e:
            logger.warning(f"  Output processing failed: {e}")

        process_time = time.time() - start_time
        logger.info(f"  eDOCr2 processing completed in {process_time:.2f}s")

        # 解析结果
        parsed = parse_edocr2_results(table_results, gdt_results, dimensions, other_info)
        parsed['edocr2_raw'] = {
            'tables': table_results,
            'gdts': gdt_results,
            'dimensions': dimensions,
            'other_info': other_info
        }
        parsed['process_time'] = process_time

        return parsed

    except Exception as e:
        logger.error(f"eDOCr2 extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def parse_edocr2_results(tables, gdts, dimensions, other_info) -> dict:
    """解析 eDOCr2 结果，提取关键字段"""
    result = {
        'success': True,
        'drawing_number': None,
        'material': None,
        'product_name': None,
        'outer_diameter': None,
        'length': None,
        'tolerance': None,
        'surface_roughness': None,
        'dimensions_detected': [],
        'gdts_detected': []
    }

    try:
        # 从表格中提取标题栏信息
        if tables:
            for table in tables:
                if isinstance(table, dict):
                    text = table.get('text', '').lower()
                    # 检测图号
                    if '图号' in text or 'drawing' in text or 'part no' in text:
                        result['drawing_number'] = extract_value_after(text, ['图号', 'drawing', 'part no'])
                    # 检测材料
                    if '材' in text or 'material' in text:
                        result['material'] = extract_value_after(text, ['材料', '材质', 'material'])
                    # 检测名称
                    if '名称' in text or 'name' in text or 'description' in text:
                        result['product_name'] = extract_value_after(text, ['名称', 'name', 'description'])

        # 从尺寸中提取直径和长度
        if dimensions:
            max_diameter = 0
            max_length = 0
            for dim in dimensions:
                if isinstance(dim, dict):
                    text = dim.get('text', '')
                    value = extract_numeric(text)
                    if value:
                        result['dimensions_detected'].append(text)
                        # 检测直径 (Φ 或 ø)
                        if 'Φ' in text or 'ø' in text or 'φ' in text:
                            if value > max_diameter:
                                max_diameter = value
                        elif value > max_length:
                            max_length = value

            if max_diameter > 0:
                result['outer_diameter'] = str(max_diameter)
            if max_length > 0:
                result['length'] = str(max_length)

        # 从 GD&T 中提取公差信息
        if gdts:
            for gdt in gdts:
                if isinstance(gdt, dict):
                    text = gdt.get('text', '')
                    result['gdts_detected'].append(text)
                    # 检测表面粗糙度
                    if 'Ra' in text or 'Rz' in text:
                        result['surface_roughness'] = text

        # 从其他信息中补充
        if other_info:
            for info in other_info:
                if isinstance(info, dict):
                    text = info.get('text', '')
                    # 检测材料代码
                    if any(m in text.upper() for m in ['SUS', 'AL', '45#', 'S45C', '6061', '7075', 'SS304', 'SS316']):
                        if not result['material']:
                            result['material'] = text

        # 计算置信度
        filled = sum(1 for k in ['drawing_number', 'material', 'product_name', 'outer_diameter', 'length']
                     if result.get(k))
        result['confidence'] = filled / 5

    except Exception as e:
        logger.error(f"Error parsing eDOCr2 results: {e}")

    return result


def extract_value_after(text: str, keywords: list) -> str:
    """从文本中提取关键字后面的值"""
    for kw in keywords:
        if kw in text.lower():
            parts = text.lower().split(kw)
            if len(parts) > 1:
                value = parts[1].strip().strip(':：').strip()
                # 取第一个词或数字
                words = value.split()
                if words:
                    return words[0]
    return None


def extract_numeric(text: str) -> float:
    """从文本中提取数值"""
    import re
    # 移除直径符号
    text = text.replace('Φ', '').replace('ø', '').replace('φ', '').strip()
    # 匹配数字（包括小数）
    match = re.search(r'(\d+\.?\d*)', text)
    if match:
        return float(match.group(1))
    return None


def call_ollama_vision(image_path: str, edocr2_results: dict = None) -> dict:
    """调用 Ollama Vision 进行标题栏补充识别"""
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # 构建提示词
        context = ""
        if edocr2_results and edocr2_results.get('success'):
            detected_dims = edocr2_results.get('dimensions_detected', [])
            detected_gdts = edocr2_results.get('gdts_detected', [])
            if detected_dims:
                context += f"\n检测到的尺寸标注: {', '.join(detected_dims[:10])}"
            if detected_gdts:
                context += f"\n检测到的GD&T标注: {', '.join(detected_gdts[:5])}"

        prompt = f"""分析这张机械工程图纸的标题栏区域（通常在右下角）。

需要提取以下信息：
1. **图号/Drawing Number**: 唯一标识号
2. **材料/Material**: 如SUS303、45#钢、AL6061等
3. **产品名称/Product Name**: 零件名称
4. **最大外径**: 找Φ符号后的最大数值
5. **总长度**: 零件的总长度

{context}

严格按以下JSON格式返回：
{{
    "drawing_number": "值或null",
    "material": "值或null",
    "product_name": "值或null",
    "outer_diameter": "仅数值或null",
    "length": "仅数值或null"
}}"""

        response = requests.post(
            f"{ollama_base}/api/generate",
            json={
                "model": "llama3.2-vision:11b",
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
                "options": {"temperature": 0.1, "top_p": 0.9}
            },
            timeout=180
        )

        if response.status_code != 200:
            return {'success': False, 'error': f'Ollama API error: {response.status_code}'}

        result = response.json()
        response_text = result.get('response', '')

        # 解析JSON
        try:
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = response_text.strip()

            data = json.loads(json_str)
            return {
                'success': True,
                'drawing_number': data.get('drawing_number'),
                'material': data.get('material'),
                'product_name': data.get('product_name'),
                'outer_diameter': data.get('outer_diameter'),
                'length': data.get('length'),
                'source': 'ollama_vision'
            }
        except json.JSONDecodeError:
            return {'success': False, 'error': 'Invalid JSON from Vision model'}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def merge_results(edocr2_result: dict, vision_result: dict) -> dict:
    """合并 eDOCr2 和 Vision 模型的结果"""
    merged = {
        'success': True,
        'drawing_number': None,
        'material': None,
        'product_name': None,
        'outer_diameter': None,
        'length': None,
        'tolerance': None,
        'surface_roughness': None,
        'confidence': 0,
        'sources': []
    }

    # 优先使用 eDOCr2 的尺寸数据
    if edocr2_result.get('success'):
        merged['sources'].append('edocr2')
        for key in ['outer_diameter', 'length', 'tolerance', 'surface_roughness']:
            if edocr2_result.get(key):
                merged[key] = edocr2_result[key]
        if edocr2_result.get('dimensions_detected'):
            merged['dimensions_detected'] = edocr2_result['dimensions_detected']
        if edocr2_result.get('gdts_detected'):
            merged['gdts_detected'] = edocr2_result['gdts_detected']

    # 优先使用 Vision 的标题栏数据
    if vision_result.get('success'):
        merged['sources'].append('ollama_vision')
        for key in ['drawing_number', 'material', 'product_name']:
            if vision_result.get(key) and vision_result[key] != 'null':
                merged[key] = vision_result[key]
        # 如果 eDOCr2 没有检测到尺寸，使用 Vision 的
        if not merged['outer_diameter'] and vision_result.get('outer_diameter'):
            merged['outer_diameter'] = vision_result['outer_diameter']
        if not merged['length'] and vision_result.get('length'):
            merged['length'] = vision_result['length']

    # 计算综合置信度
    filled = sum(1 for k in ['drawing_number', 'material', 'product_name', 'outer_diameter', 'length']
                 if merged.get(k))
    merged['confidence'] = filled / 5

    return merged


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'edocr2_loaded': edocr2_models is not None,
        'ollama_available': check_ollama()
    })


def check_ollama():
    """检查 Ollama 服务"""
    try:
        response = requests.get(f"{ollama_base}/api/tags", timeout=3)
        return response.status_code == 200
    except:
        return False


@app.route('/ocr/extract', methods=['POST'])
def extract_drawing_info():
    """
    提取图纸信息
    请求格式：multipart/form-data
    - file: 图纸文件（PDF或图片）
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '缺少文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400

        # 保存上传文件
        temp_path = f"/tmp/edocr2_temp_{os.getpid()}_{file.filename}"
        file.save(temp_path)

        logger.info(f"Received OCR request: {file.filename}")

        try:
            # Step 1: eDOCr2 处理
            edocr2_result = extract_with_edocr2(temp_path)

            # Step 2: Ollama Vision 补充（标题栏识别）
            vision_result = {}
            if check_ollama():
                vision_result = call_ollama_vision(temp_path, edocr2_result)

            # Step 3: 合并结果
            final_result = merge_results(edocr2_result, vision_result)

            logger.info(f"OCR completed: confidence={final_result.get('confidence', 0):.2f}")

            return jsonify(final_result)

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting WSL eDOCr2 OCR Service...")

    # 初始化 eDOCr2
    if init_edocr2():
        logger.info("eDOCr2 initialized successfully")
    else:
        logger.warning("eDOCr2 initialization failed, falling back to Vision-only mode")

    # 启动服务
    app.run(host='0.0.0.0', port=8003, debug=False)
