#!/usr/bin/env python3
"""
WSL Vision OCR 微服务
使用 Ollama Vision (Llama 3.2 Vision 11B) 识别工程图纸
"""
import os
import json
import base64
import logging
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OLLAMA_BASE = "http://localhost:11434"
VISION_MODEL = "qwen3-vl:8b-instruct"  # 使用实际安装的模型


def check_ollama():
    """检查 Ollama 服务"""
    try:
        response = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        return response.status_code == 200
    except:
        return False


def call_ollama_vision(image_path: str) -> dict:
    """调用 Ollama Vision 识别图纸"""
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        prompt = """分析这张机械工程图纸，提取以下信息：

**必填字段**：
1. **图号 (drawing_number)**: 唯一标识号，通常在标题栏（右下角）
2. **材料 (material)**: 如 SUS303, 45#, AL6061 等
3. **产品名称 (product_name)**: 零件名称
4. **最大外径 (outer_diameter)**: Φ符号后的最大直径数值（仅数字）
5. **总长度 (length)**: 零件总长度（仅数字）

**可选字段**：
- customer_part_number: 客户零件号
- customer_name: 客户名称
- tolerance: 公差要求
- surface_roughness: 表面粗糙度

**注意**：
- 标题栏通常在图纸右下角
- Φ表示直径，提取数值即可（如Φ12.5返回"12.5"）
- 多个直径取最大值
- 返回纯数值，不含单位

严格按以下JSON格式返回：
{
    "drawing_number": "值或null",
    "material": "值或null",
    "product_name": "值或null",
    "outer_diameter": "仅数值或null",
    "length": "仅数值或null",
    "customer_part_number": "值或null",
    "customer_name": "值或null",
    "tolerance": "值或null",
    "surface_roughness": "值或null"
}"""

        logger.info("Calling Ollama Vision API...")
        response = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={
                "model": VISION_MODEL,
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
        logger.info(f"Vision response: {response_text[:200]}...")

        # 解析 JSON
        try:
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = response_text.strip()

            data = json.loads(json_str)

            # 清理数据
            cleaned = {
                'success': True,
                'drawing_number': str(data.get('drawing_number', '')).strip() if data.get('drawing_number') else None,
                'material': str(data.get('material', '')).strip() if data.get('material') else None,
                'product_name': str(data.get('product_name', '')).strip() if data.get('product_name') else None,
                'outer_diameter': str(data.get('outer_diameter', '')).strip() if data.get('outer_diameter') else None,
                'length': str(data.get('length', '')).strip() if data.get('length') else None,
                'customer_part_number': str(data.get('customer_part_number', '')).strip() if data.get('customer_part_number') else None,
                'customer_name': str(data.get('customer_name', '')).strip() if data.get('customer_name') else None,
                'tolerance': str(data.get('tolerance', '')).strip() if data.get('tolerance') else None,
                'surface_roughness': str(data.get('surface_roughness', '')).strip() if data.get('surface_roughness') else None,
            }

            # 移除 "null" 字符串
            for k, v in cleaned.items():
                if v == 'null' or v == 'None':
                    cleaned[k] = None

            # 计算置信度
            filled = sum(1 for k in ['drawing_number', 'material', 'product_name', 'outer_diameter', 'length']
                        if cleaned.get(k))
            cleaned['confidence'] = filled / 5
            cleaned['source'] = 'ollama_vision'

            return cleaned

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {'success': False, 'error': f'Invalid JSON from Vision: {str(e)}'}

    except Exception as e:
        logger.error(f"Vision OCR failed: {e}")
        return {'success': False, 'error': str(e)}


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'ollama_available': check_ollama(),
        'model': VISION_MODEL
    })


@app.route('/ocr/extract', methods=['POST'])
def extract_drawing_info():
    """提取图纸信息"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '缺少文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400

        # 保存临时文件
        temp_path = f"/tmp/vision_ocr_{os.getpid()}_{file.filename}"
        file.save(temp_path)

        logger.info(f"Received OCR request: {file.filename}")

        try:
            result = call_ollama_vision(temp_path)
            logger.info(f"OCR completed: confidence={result.get('confidence', 0):.2f}")
            return jsonify(result)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting WSL Vision OCR Service...")
    if check_ollama():
        logger.info("Ollama service available")
    else:
        logger.warning("Ollama service not available!")

    app.run(host='0.0.0.0', port=8083, debug=False)
