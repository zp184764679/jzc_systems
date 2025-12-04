#!/usr/bin/env python3
"""
WSL OCR微服务
使用PaddleOCR + 布局分析 + Ollama Vision
"""
from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
import cv2
import numpy as np
from PIL import Image
import requests
import logging
import base64
import json
from typing import Dict
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局OCR引擎
ocr_engine = None
ollama_base = "http://localhost:11434"


def init_paddle_ocr():
    """初始化PaddleOCR"""
    global ocr_engine
    # 暂时禁用PaddleOCR, 仅使用Llama 3.2 Vision 11B进行OCR识别
    ocr_engine = None
    logger.info("✅ 使用 Llama 3.2 Vision 11B 专业OCR模型")


def detect_layout_regions(image_path: str) -> Dict:
    """
    检测工程图纸的布局区域（Layout Analysis）

    识别关键区域：
    1. 标题栏（Title Block）- 通常在右下角，包含图号、材质、名称
    2. 尺寸标注区域（Dimension Annotations）- 包含外径、长度等尺寸
    3. 主视图区域（Main View）- 零件主体
    """
    try:
        logger.info("🔍 开始布局分析（Layout Analysis）...")

        # 读取图像
        pil_img = Image.open(image_path)
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        h, w = gray.shape

        # 1. 检测标题栏 - 右下角区域
        title_roi = gray[int(h*0.7):, int(w*0.6):]
        edges = cv2.Canny(title_roi, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 找到最大的矩形区域（标题栏）
        max_area = 0
        title_block = None
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > max_area and area > (title_roi.shape[0] * title_roi.shape[1] * 0.1):
                x, y, rect_w, rect_h = cv2.boundingRect(cnt)
                if rect_w > rect_h * 1.5:  # 水平矩形
                    max_area = area
                    title_block = {
                        "x": x + int(w*0.6),
                        "y": y + int(h*0.7),
                        "width": rect_w,
                        "height": rect_h
                    }

        if title_block:
            logger.info(f"  ✓ 检测到标题栏: x={title_block['x']}, y={title_block['y']}, w={title_block['width']}, h={title_block['height']}")

        # 2. 检测尺寸标注区域 - 使用形态学操作检测直线
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        dimension_mask = cv2.add(horizontal_lines, vertical_lines)

        # 找到尺寸标注的区域
        dim_contours, _ = cv2.findContours(dimension_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        dimension_areas = []
        for cnt in dim_contours:
            area = cv2.contourArea(cnt)
            if area > 100:
                x, y, rect_w, rect_h = cv2.boundingRect(cnt)
                dimension_areas.append({
                    "x": x, "y": y, "width": rect_w, "height": rect_h
                })

        logger.info(f"  ✓ 检测到{len(dimension_areas)}个尺寸标注区域")

        # 3. 主视图区域（图纸中心区域）
        main_view = {
            "x": int(w * 0.1),
            "y": int(h * 0.1),
            "width": int(w * 0.8),
            "height": int(h * 0.8)
        }

        return {
            "title_block": title_block,
            "dimension_areas": dimension_areas[:10],  # 最多10个
            "main_view": main_view,
            "image_size": {"width": w, "height": h}
        }
    except Exception as e:
        logger.error(f"❌ 布局分析失败: {e}")
        return {}


def call_ollama_vision(image_path: str, layout_info: Dict = None) -> Dict:
    """调用Ollama Vision进行图纸识别"""
    try:
        # 读取图像并转换为base64
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # 构建提示词 - 工程图纸专业版（带布局分析增强）
        layout_hint = ""
        if layout_info and layout_info.get('title_block'):
            tb = layout_info['title_block']
            img_size = layout_info.get('image_size', {})
            if img_size:
                x_percent = (tb['x'] / img_size['width']) * 100 if img_size.get('width') else 0
                y_percent = (tb['y'] / img_size['height']) * 100 if img_size.get('height') else 0
                layout_hint = f"\n\n**布局分析提示**：\n- 系统已检测到标题栏位于图纸右下角（约{x_percent:.0f}%横向，{y_percent:.0f}%纵向位置）\n- 图号、材质、产品名称应该在这个区域内\n- 请重点关注右下角的矩形框内的文字信息"

        dim_hint = ""
        if layout_info and layout_info.get('dimension_areas'):
            dim_count = len(layout_info['dimension_areas'])
            dim_hint = f"\n- 系统检测到{dim_count}个尺寸标注区域，请在这些区域寻找Φ和长度数值"

        prompt = f"""You are an expert in analyzing mechanical engineering drawings and technical blueprints. Analyze this engineering drawing and extract the following critical information with high precision.

**REQUIRED FIELDS** (Each is critical):
1. **drawing_number**: The unique drawing number, typically found in the title block (right-bottom corner)
2. **material**: Material specification (e.g., SUS303, 45# Steel, Aluminum 6061, etc.)
3. **product_name**: Part name or description
4. **outer_diameter**: Maximum diameter value, marked with "Φ" symbol (e.g., "Φ7.8" means 7.8)
5. **length**: Total length of the part in mm

**OPTIONAL FIELDS**:
- customer_part_number: Customer's part number
- customer_name: Customer company name
- tolerance: Tolerance specification (e.g., "±0.05")
- surface_roughness: Surface finish requirement (e.g., "Ra3.2")
- weight: Part weight

**IMPORTANT GUIDELINES**:
- Title block is usually located in the RIGHT-BOTTOM corner of the drawing
- Drawing number, material, and product name are typically inside the title block
- "Φ" symbol indicates DIAMETER - extract the number after it (e.g., Φ12.5 → return "12.5")
- Length is usually marked with dimension lines and arrows
- If multiple diameter values exist, choose the LARGEST one as outer_diameter
- Return ONLY numeric values for outer_diameter and length (no units, no "Φ" symbol)
{dim_hint}{layout_hint}

Return ONLY valid JSON in this exact format:
{{
    "drawing_number": "value or null",
    "material": "value or null",
    "product_name": "value or null",
    "outer_diameter": "numeric value or null",
    "length": "numeric value or null",
    "customer_part_number": "value or null",
    "customer_name": "value or null",
    "tolerance": "value or null",
    "surface_roughness": "value or null",
    "weight": "value or null"
}}"""

        # 调用Ollama API - 使用Llama 3.2 Vision 11B专业OCR模型
        response = requests.post(
            f"{ollama_base}/api/generate",
            json={
                "model": "llama3.2-vision:11b",
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "temperature": 0.1,  # 降低温度以提高准确性
                    "top_p": 0.9
                }
            },
            timeout=180  # Llama 11B可能需要更多时间
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API请求失败: {response.status_code}")

        result = response.json()
        response_text = result.get('response', '')

        logger.info(f"🤖 Ollama Vision响应: {response_text[:200]}...")

        # 解析JSON响应
        try:
            # 提取JSON（可能在```json```代码块中）
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = response_text.strip()

            data = json.loads(json_str)

            # 清理和标准化数据
            cleaned_data = {
                'drawing_number': str(data.get('drawing_number', '')).strip() or None,
                'material': str(data.get('material', '')).strip() or None,
                'product_name': str(data.get('product_name', '')).strip() or None,
                'outer_diameter': str(data.get('outer_diameter', '')).strip() or None,
                'length': str(data.get('length', '')).strip() or None,
                'customer_part_number': str(data.get('customer_part_number', '')).strip() or None,
                'customer_name': str(data.get('customer_name', '')).strip() or None,
                'tolerance': str(data.get('tolerance', '')).strip() or None,
                'surface_roughness': str(data.get('surface_roughness', '')).strip() or None,
                'weight': str(data.get('weight', '')).strip() or None
            }

            # 计算置信度
            filled_fields = sum(1 for v in cleaned_data.values() if v)
            confidence = (filled_fields / 5) * 0.9  # 基于5个必填字段

            return {
                'success': True,
                **cleaned_data,
                'confidence': confidence,
                'raw_data': data
            }

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析失败: {e}")
            return {
                'success': False,
                'error': f'Vision模型返回了无效的JSON格式: {str(e)}'
            }

    except Exception as e:
        logger.error(f"❌ Ollama Vision调用失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'ocr_engine': 'paddleocr' if ocr_engine else 'unavailable',
        'ollama_available': check_ollama()
    })


def check_ollama():
    """检查Ollama服务是否可用"""
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

        # 保存上传的文件
        temp_path = f"/tmp/ocr_temp_{os.getpid()}_{file.filename}"
        file.save(temp_path)

        logger.info(f"📤 收到OCR请求: {file.filename}")

        try:
            # 步骤1: 布局分析
            layout_info = detect_layout_regions(temp_path)

            # 步骤2: 调用Ollama Vision识别
            result = call_ollama_vision(temp_path, layout_info=layout_info)

            logger.info(f"✅ OCR处理完成: success={result.get('success')}")

            return jsonify(result)

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        logger.error(f"❌ OCR处理失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    logger.info("🚀 启动WSL OCR微服务...")
    init_paddle_ocr()

    # 监听8003端口
    app.run(host='0.0.0.0', port=8003, debug=False)
