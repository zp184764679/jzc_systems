#!/usr/bin/env python3
"""
WSL OCR双引擎混合微服务
eDOCr2 (工程图纸专业识别) + Qwen3-VL 8B (视觉语言模型语义理解)

用户配置：只使用2个引擎 (Qwen3 + eDOCr2)，不使用PaddleOCR
"""
from flask import Flask, request, jsonify
import cv2
import numpy as np
from PIL import Image
import requests
import logging
import base64
import json
from typing import Dict, List
import os
import sys
import re

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局引擎
paddle_ocr = None
edocr2_recognizer_gdt = None
edocr2_recognizer_dim = None
edocr2_detector = None
edocr2_tools = None
ollama_base = "http://localhost:11434"


def init_paddle_ocr():
    """初始化PaddleOCR通用文本识别引擎"""
    global paddle_ocr
    try:
        logger.info("🔧 初始化PaddleOCR...")
        from paddleocr import PaddleOCR

        # 初始化PaddleOCR (中英文混合识别)
        paddle_ocr = PaddleOCR(
            use_textline_orientation=True,  # 使用文本行方向分类器 (替代旧的use_angle_cls)
            lang='ch'  # 中英文混合
        )

        logger.info("✅ PaddleOCR初始化成功 - 通用中英文OCR引擎就绪")
        return True

    except Exception as e:
        logger.error(f"❌ PaddleOCR初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        paddle_ocr = None
        return False


def init_edocr2():
    """初始化eDOCr2专业工程图纸OCR引擎"""
    global edocr2_recognizer_gdt, edocr2_recognizer_dim, edocr2_detector, edocr2_tools

    try:
        logger.info("🔧 初始化eDOCr2...")

        # 添加eDOCr2到Python路径
        edocr2_path = '/home/admin/edocr2'
        if edocr2_path not in sys.path:
            sys.path.insert(0, edocr2_path)

        # 导入eDOCr2模块
        from edocr2 import tools as edocr2_tools_module
        from edocr2.keras_ocr.recognition import Recognizer
        from edocr2.keras_ocr.detection import Detector
        import tensorflow as tf

        # 配置TensorFlow GPU内存增长
        gpus = tf.config.list_physical_devices('GPU')
        for gpu in gpus:
            try:
                tf.config.experimental.set_memory_growth(gpu, True)
            except:
                pass

        edocr2_tools = edocr2_tools_module

        # 模型路径
        gdt_model = '/home/admin/edocr2/edocr2/models/recognizer_gdts.keras'
        dim_model = '/home/admin/edocr2/edocr2/models/recognizer_dimensions_2.keras'

        # 检查模型文件是否存在
        if not os.path.exists(gdt_model):
            logger.error(f"❌ GD&T模型文件不存在: {gdt_model}")
            return False
        if not os.path.exists(dim_model):
            logger.error(f"❌ 尺寸模型文件不存在: {dim_model}")
            return False

        # 构建GD&T alphabet（基于test_train.py的定义，精确匹配权重文件）
        import string
        GDT_symbols = '⏤⏥○⌭⌒⌓⏊∠⫽⌯⌖◎↗⌰'  # 14个字符
        FCF_symbols = 'ⒺⒻⓁⓂⓅⓈⓉⓊ'  # 8个字符
        alphabet_gdts = string.digits + ',.⌀ABCD' + GDT_symbols + FCF_symbols  # 10+7+14+8=39个字符，匹配40个输出神经元(39+1 blank)

        # 构建尺寸 alphabet（基于test_train.py的定义，移除'Z'以匹配权重文件）
        Extra = '(),.+-±:/°"⌀='  # 13个字符
        alphabet_dimensions = string.digits + 'AaBCDRGHhMmnxtd' + Extra  # 10+15+13=38个字符，匹配39个输出神经元(38+1 blank)

        logger.info(f"  📌 GD&T alphabet: {len(alphabet_gdts)}个字符（权重需要39个）")
        logger.info(f"  📌 尺寸 alphabet: {len(alphabet_dimensions)}个字符（权重需要38个）")

        # 加载GD&T识别器
        logger.info("  ⏳ 加载GD&T识别器...")
        edocr2_recognizer_gdt = Recognizer(alphabet=alphabet_gdts, weights=None)
        edocr2_recognizer_gdt.model.load_weights(gdt_model)
        logger.info("  ✅ GD&T识别器加载成功")

        # 加载尺寸识别器
        logger.info("  ⏳ 加载尺寸识别器...")
        edocr2_recognizer_dim = Recognizer(alphabet=alphabet_dimensions, weights=None)
        edocr2_recognizer_dim.model.load_weights(dim_model)
        logger.info("  ✅ 尺寸识别器加载成功")

        # 加载检测器
        logger.info("  ⏳ 加载文本检测器...")
        edocr2_detector = Detector()
        logger.info("  ✅ 文本检测器加载成功")

        logger.info("✅ eDOCr2初始化成功 - 专业工程图纸OCR引擎就绪")
        return True

    except Exception as e:
        logger.error(f"❌ eDOCr2初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        edocr2_recognizer_gdt = None
        edocr2_recognizer_dim = None
        edocr2_detector = None
        edocr2_tools = None
        return False


def detect_layout_regions(image_path: str) -> Dict:
    """
    检测工程图纸的布局区域（Layout Analysis）

    识别关键区域:
    1. 标题栏（Title Block）- 通常在右下角
    2. 尺寸标注区域（Dimension Annotations）
    3. 主视图区域（Main View）
    """
    try:
        logger.info("🔍 开始布局分析（Layout Analysis）...")

        pil_img = Image.open(image_path)
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        h, w = gray.shape

        # 1. 检测标题栏 - 右下角区域
        title_roi = gray[int(h*0.7):, int(w*0.6):]
        edges = cv2.Canny(title_roi, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        max_area = 0
        title_block = None
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > max_area and area > (title_roi.shape[0] * title_roi.shape[1] * 0.1):
                x, y, rect_w, rect_h = cv2.boundingRect(cnt)
                if rect_w > rect_h * 1.5:
                    max_area = area
                    title_block = {
                        "x": x + int(w*0.6),
                        "y": y + int(h*0.7),
                        "width": rect_w,
                        "height": rect_h
                    }

        if title_block:
            logger.info(f"  ✓ 检测到标题栏: x={title_block['x']}, y={title_block['y']}")

        # 2. 检测尺寸标注区域
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        dimension_mask = cv2.add(horizontal_lines, vertical_lines)

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

        return {
            "title_block": title_block,
            "dimension_areas": dimension_areas[:10],
            "main_view": {
                "x": int(w * 0.1),
                "y": int(h * 0.1),
                "width": int(w * 0.8),
                "height": int(h * 0.8)
            },
            "image_size": {"width": w, "height": h}
        }
    except Exception as e:
        logger.error(f"❌ 布局分析失败: {e}")
        return {}


def extract_with_edocr2(image_path: str) -> Dict:
    """使用eDOCr2提取工程图纸信息（GD&T符号、尺寸、公差）"""
    try:
        if not edocr2_recognizer_gdt or not edocr2_recognizer_dim or not edocr2_detector or not edocr2_tools:
            logger.warning("⚠️  eDOCr2引擎未初始化")
            return {}

        logger.info("🔧 使用eDOCr2多步骤管道识别工程图纸...")

        # 读取图像
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"❌ 无法读取图像: {image_path}")
            return {}

        # 步骤1: 图像分割 - 识别图框、GD&T区域、表格、尺寸区域
        logger.info("  🔍 步骤1: 图像分割...")
        img_boxes, frame, gdt_boxes, tables, dim_boxes = edocr2_tools.layer_segm.segment_img(
            img,
            autoframe=True,
            frame_thres=0.7,
            GDT_thres=0.02,
            binary_thres=127
        )

        logger.info(f"    ✓ 图框检测: {'成功' if frame else '未检测到'}")
        logger.info(f"    ✓ GD&T区域: {len(gdt_boxes) if gdt_boxes else 0}个")
        logger.info(f"    ✓ 表格区域: {len(tables) if tables else 0}个")
        logger.info(f"    ✓ 尺寸区域: {len(dim_boxes) if dim_boxes else 0}个")

        # 创建处理副本
        process_img = img.copy()

        # 步骤2: OCR表格
        logger.info("  📋 步骤2: 识别表格...")
        table_results = []
        updated_tables = []
        if tables and len(tables) > 0:
            try:
                table_results, updated_tables, process_img = edocr2_tools.ocr_pipelines.ocr_tables(
                    tables, process_img, language='eng'
                )
                logger.info(f"    ✓ 表格识别完成: {len(table_results)}个表格")
            except Exception as e:
                logger.warning(f"    ⚠️ 表格识别失败: {e}")

        # 步骤3: OCR GD&T符号
        logger.info("  📐 步骤3: 识别GD&T符号...")
        gdt_results = []
        updated_gdt_boxes = []
        if gdt_boxes and len(gdt_boxes) > 0:
            try:
                gdt_results, updated_gdt_boxes, process_img = edocr2_tools.ocr_pipelines.ocr_gdt(
                    process_img, gdt_boxes, edocr2_recognizer_gdt
                )
                logger.info(f"    ✓ GD&T识别完成: {len(gdt_results)}个符号")
            except Exception as e:
                logger.warning(f"    ⚠️ GD&T识别失败: {e}")

        # 步骤4: OCR尺寸标注
        logger.info("  📏 步骤4: 识别尺寸标注...")
        dimensions = []
        other_info = []
        dim_tess = []

        # 如果检测到图框，裁剪到图框区域
        if frame:
            process_img = process_img[frame.y : frame.y + frame.h, frame.x : frame.x + frame.w]

        try:
            alphabet_dim = edocr2_tools.ocr_pipelines.read_alphabet(
                '/home/admin/edocr2/edocr2/models/recognizer_dimensions_2.keras'
            )

            dimensions, other_info, process_img, dim_tess = edocr2_tools.ocr_pipelines.ocr_dimensions(
                process_img,
                edocr2_detector,
                edocr2_recognizer_dim,
                alphabet_dim,
                frame,
                dim_boxes,
                cluster_thres=20,
                max_img_size=1048,
                language='eng',
                backg_save=False
            )

            logger.info(f"    ✓ 尺寸识别完成: {len(dimensions)}个尺寸")

        except Exception as e:
            logger.warning(f"    ⚠️ 尺寸识别失败: {e}")

        # 整理结果
        edocr2_data = {
            'table_results': table_results,
            'gdt_results': gdt_results,
            'dimensions': dimensions,
            'other_info': other_info,
            'dim_tess': dim_tess,
            'frame': frame,
            'statistics': {
                'tables_count': len(table_results),
                'gdt_count': len(gdt_results),
                'dimensions_count': len(dimensions),
                'other_info_count': len(other_info)
            }
        }

        logger.info(f"✅ eDOCr2识别完成: 表格={len(table_results)}, GD&T={len(gdt_results)}, 尺寸={len(dimensions)}")

        return edocr2_data

    except Exception as e:
        logger.error(f"❌ eDOCr2识别失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {}


def extract_with_paddle(image_path: str) -> Dict:
    """使用PaddleOCR提取通用文本（补充标题栏、图号等）"""
    try:
        if not paddle_ocr:
            logger.warning("⚠️ PaddleOCR引擎未初始化")
            return {}

        logger.info("📝 使用PaddleOCR识别通用文本...")

        # PaddleOCR识别
        result = paddle_ocr.ocr(image_path, cls=True)

        # 解析PaddleOCR结果
        paddle_data = {
            'text_blocks': [],
            'all_text': [],
            'drawing_numbers': [],
            'materials': []
        }

        if result and len(result) > 0:
            for line in result[0] if result[0] else []:
                if line and len(line) >= 2:
                    bbox, (text, confidence) = line[0], line[1]

                    paddle_data['text_blocks'].append({
                        'bbox': bbox,
                        'text': text,
                        'confidence': confidence
                    })

                    paddle_data['all_text'].append(text)

                    # 识别可能的图号（通常包含数字和字母）
                    if re.search(r'[A-Z0-9]{3,}[-_]?[A-Z0-9]+', text):
                        paddle_data['drawing_numbers'].append(text)

                    # 识别可能的材质（常见材质关键词）
                    material_keywords = ['SUS', 'sus', '不锈钢', 'Steel', 'steel', '铝', 'Aluminum', '铜', 'Copper', '45#', '304', '316']
                    if any(keyword in text for keyword in material_keywords):
                        paddle_data['materials'].append(text)

            logger.info(f"✅ PaddleOCR识别完成: 发现{len(paddle_data['text_blocks'])}个文本块")

        return paddle_data

    except Exception as e:
        logger.error(f"❌ PaddleOCR识别失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {}


def parse_edocr2_dimensions(edocr2_data: Dict) -> Dict:
    """从eDOCr2结果中解析直径、长度等关键尺寸"""
    parsed = {
        'outer_diameter': None,
        'length': None,
        'tolerances': [],
        'surface_roughness': None
    }

    try:
        # 解析尺寸数据
        dimensions = edocr2_data.get('dimensions', [])
        other_info = edocr2_data.get('other_info', [])
        all_text = dimensions + other_info

        diameters = []
        lengths = []

        for item in all_text:
            # item可能是字符串或包含文本的对象
            if isinstance(item, str):
                text = item
            elif isinstance(item, dict):
                text = item.get('text', '')
            elif isinstance(item, (list, tuple)) and len(item) > 0:
                text = str(item[0])
            else:
                text = str(item)

            # 识别直径 (Φ, φ, Ø)
            if any(symbol in text for symbol in ['Φ', 'φ', 'Ø', 'DIA', 'dia']):
                numbers = re.findall(r'\d+\.?\d*', text)
                for num_str in numbers:
                    try:
                        num = float(num_str)
                        if 0.1 < num < 500:  # 合理的直径范围
                            diameters.append(num)
                    except:
                        pass

            # 识别长度 (通常是较大的数值)
            if 'L' in text.upper() or 'LENGTH' in text.upper():
                numbers = re.findall(r'\d+\.?\d*', text)
                for num_str in numbers:
                    try:
                        num = float(num_str)
                        if 1 < num < 2000:  # 合理的长度范围
                            lengths.append(num)
                    except:
                        pass

            # 识别公差
            if '±' in text or '+/-' in text:
                parsed['tolerances'].append(text)

            # 识别表面粗糙度
            if 'Ra' in text or 'Rz' in text:
                parsed['surface_roughness'] = text

        # 选择最大直径
        if diameters:
            parsed['outer_diameter'] = str(max(diameters))
            logger.info(f"  📏 eDOCr2解析到最大直径: {parsed['outer_diameter']}")

        # 选择最大长度
        if lengths:
            parsed['length'] = str(max(lengths))
            logger.info(f"  📏 eDOCr2解析到长度: {parsed['length']}")

        return parsed

    except Exception as e:
        logger.error(f"❌ 解析eDOCr2尺寸失败: {e}")
        return parsed


def call_ollama_vision(image_path: str, layout_info: Dict = None, edocr2_data: Dict = None) -> Dict:
    """调用Ollama Vision进行图纸识别（专注于图号、材质、客户）"""
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # 构建增强提示词 - 包含eDOCr2的发现
        edocr2_hint = ""
        if edocr2_data and edocr2_data.get('statistics'):
            stats = edocr2_data['statistics']
            edocr2_hint = f"""

**eDOCr2已识别信息**:
- 尺寸标注: {stats.get('dimensions_count', 0)}个
- GD&T符号: {stats.get('gdt_count', 0)}个
- 表格: {stats.get('tables_count', 0)}个
这些专业OCR数据将辅助您的识别。"""

        layout_hint = ""
        if layout_info and layout_info.get('title_block'):
            tb = layout_info['title_block']
            img_size = layout_info.get('image_size', {})
            if img_size:
                x_percent = (tb['x'] / img_size['width']) * 100 if img_size.get('width') else 0
                y_percent = (tb['y'] / img_size['height']) * 100 if img_size.get('height') else 0
                layout_hint = f"\n\n**布局分析**: 标题栏位于右下角（{x_percent:.0f}%横向，{y_percent:.0f}%纵向）"

        prompt = f"""You are an expert mechanical engineering drawing analyst. Your task is to THOROUGHLY extract ALL available information from this drawing.

**CRITICAL INSTRUCTION**: Try your BEST to find and extract EVERY field listed below. Do NOT return null unless the information is truly absent.

**PRIMARY FIELDS** (Search carefully in title block, usually RIGHT-BOTTOM corner):
1. **drawing_number**: Drawing/Part number (e.g., "DR-2024-001", "P12345")
2. **material**: Material name (e.g., "SUS303", "45#", "6061 Aluminum", "S45C")
3. **product_name**: Part name/description (Chinese or English)
4. **customer_name**: Customer/Client company name
5. **customer_part_number**: Customer's own part number

**DIMENSION FIELDS** (Look for dimensions, GD&T symbols, annotations):
6. **outer_diameter**: Largest diameter value (marked with Φ/φ/Ø) - NUMBER ONLY (e.g., Φ12.5 → "12.5")
7. **length**: Total length in mm - NUMBER ONLY (e.g., "85mm" → "85")
8. **weight**: Part weight (e.g., "0.5kg", "500g")

**TECHNICAL SPECS** (Check title block, notes, technical requirements section):
9. **tolerance**: Tolerance spec (e.g., "±0.05", "IT7", "H7")
10. **surface_roughness**: Surface finish (e.g., "Ra3.2", "Ra1.6", "▽3.2")
11. **heat_treatment**: Heat treatment req (e.g., "淬火", "Quenching", "HRC45")
12. **surface_treatment**: Surface finish process (e.g., "镀锌", "Zinc plating", "阳极氧化")

**SEARCH STRATEGY**:
- Title block: Usually contains drawing#, material, customer, product name
- Dimension lines: Look for Φ symbols, length measurements
- Notes/Annotations: May contain tolerance, surface roughness, treatments
- Tables: Check any tables in the drawing for specifications
- Chinese text: Many drawings have Chinese labels - extract them too
{edocr2_hint}{layout_hint}

**IMPORTANT**:
- Extract Φ12.5 as "12.5" (number only, no symbol)
- Extract "85mm" as "85" (number only, no unit)
- If you see ANY text that might be relevant, include it
- Empty fields should be null ONLY if truly not found after careful search

Return ONLY valid JSON (no explanation):
{{
    "drawing_number": "value or null",
    "material": "value or null",
    "product_name": "value or null",
    "customer_name": "value or null",
    "customer_part_number": "value or null",
    "outer_diameter": "number or null",
    "length": "number or null",
    "weight": "value or null",
    "tolerance": "value or null",
    "surface_roughness": "value or null",
    "heat_treatment": "value or null",
    "surface_treatment": "value or null"
}}"""

        # 调用Ollama API - 使用Qwen3-VL 8B视觉语言模型
        response = requests.post(
            f"{ollama_base}/api/generate",
            json={
                "model": "qwen3-vl:8b-instruct",
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            },
            timeout=180
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API请求失败: {response.status_code}")

        result = response.json()
        response_text = result.get('response', '')

        logger.info(f"🤖 Qwen3-VL响应: {response_text[:200]}...")

        # 解析JSON
        try:
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = response_text.strip()

            data = json.loads(json_str)

            # 清理数据
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
            confidence = (filled_fields / 5) * 0.9

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


def merge_results(vision_result: Dict, edocr2_data: Dict, paddle_data: Dict) -> Dict:
    """合并eDOCr2、Qwen3-VL双引擎的识别结果"""
    merged = vision_result.copy()

    # 从eDOCr2结果中解析关键尺寸
    parsed_dims = parse_edocr2_dimensions(edocr2_data)

    # 优先级1: 使用eDOCr2的尺寸数据（最精确）
    if parsed_dims['outer_diameter'] and not merged.get('outer_diameter'):
        merged['outer_diameter'] = parsed_dims['outer_diameter']
        logger.info(f"✅ 使用eDOCr2识别的外径: {parsed_dims['outer_diameter']}")

    if parsed_dims['length'] and not merged.get('length'):
        merged['length'] = parsed_dims['length']
        logger.info(f"✅ 使用eDOCr2识别的长度: {parsed_dims['length']}")

    if parsed_dims['tolerances'] and not merged.get('tolerance'):
        merged['tolerance'] = parsed_dims['tolerances'][0]
        logger.info(f"✅ 使用eDOCr2识别的公差: {parsed_dims['tolerances'][0]}")

    if parsed_dims['surface_roughness'] and not merged.get('surface_roughness'):
        merged['surface_roughness'] = parsed_dims['surface_roughness']
        logger.info(f"✅ 使用eDOCr2识别的表面粗糙度: {parsed_dims['surface_roughness']}")

    # 优先级2: 使用PaddleOCR补充图号和材质（如果Qwen3-VL未识别）
    if paddle_data:
        # 补充图号
        if not merged.get('drawing_number') and paddle_data.get('drawing_numbers'):
            # 选择最可能的图号（最长的）
            best_drawing_number = max(paddle_data['drawing_numbers'], key=len, default=None)
            if best_drawing_number:
                merged['drawing_number'] = best_drawing_number
                logger.info(f"✅ 使用PaddleOCR识别的图号: {best_drawing_number}")

        # 补充材质
        if not merged.get('material') and paddle_data.get('materials'):
            best_material = paddle_data['materials'][0]
            merged['material'] = best_material
            logger.info(f"✅ 使用PaddleOCR识别的材质: {best_material}")

        # 添加PaddleOCR统计
        merged['paddle_statistics'] = {
            'text_blocks_count': len(paddle_data.get('text_blocks', [])),
            'drawing_numbers_found': len(paddle_data.get('drawing_numbers', [])),
            'materials_found': len(paddle_data.get('materials', []))
        }

    # 添加eDOCr2统计信息
    if edocr2_data and edocr2_data.get('statistics'):
        merged['edocr2_statistics'] = edocr2_data['statistics']

    # 重新计算置信度（三引擎融合提高置信度）
    filled_fields = sum(1 for k, v in merged.items()
                       if k in ['drawing_number', 'material', 'product_name', 'outer_diameter', 'length'] and v)

    # 三引擎都工作时，置信度更高
    engines_active = sum([
        bool(paddle_data.get('text_blocks')),
        bool(edocr2_data.get('statistics')),
        bool(vision_result.get('success'))
    ])

    base_confidence = (filled_fields / 5) * 0.9
    engine_bonus = (engines_active / 3) * 0.08  # 最多额外8%置信度
    merged['confidence'] = min(base_confidence + engine_bonus, 0.98)

    logger.info(f"🎯 三引擎融合完成: 置信度={merged['confidence']:.2f}, 引擎数={engines_active}/3")

    return merged


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'engines': {
            'paddle_ocr': 'available' if paddle_ocr else 'unavailable',
            'edocr2': 'available' if edocr2_recognizer_gdt and edocr2_recognizer_dim else 'unavailable',
            'ollama': 'available' if check_ollama() else 'unavailable'
        }
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
    提取图纸信息 - 混合OCR方案

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

        logger.info(f"📤 收到混合OCR请求: {file.filename}")

        try:
            # 步骤1: 布局分析
            layout_info = detect_layout_regions(temp_path)

            # 步骤2: 跳过PaddleOCR（按用户要求）
            paddle_data = None
            logger.info("⏭️  跳过PaddleOCR识别步骤（用户配置：仅使用2引擎）")

            # 步骤3: eDOCr2识别（专注于GD&T和尺寸）
            edocr2_data = extract_with_edocr2(temp_path)

            # 步骤4: Qwen3-VL识别（专注于图号、材质、客户）
            vision_result = call_ollama_vision(temp_path, layout_info=layout_info, edocr2_data=edocr2_data)

            # 步骤5: 双引擎结果融合（Qwen3-VL + eDOCr2）
            final_result = merge_results(vision_result, edocr2_data, paddle_data)

            logger.info(f"✅ 双引擎混合OCR处理完成: success={final_result.get('success')}")

            return jsonify(final_result)

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
    logger.info("🚀 启动WSL OCR双引擎混合微服务 (eDOCr2 + Qwen3-VL 8B)...")
    logger.info("📋 用户配置：仅使用2个引擎 - Qwen3-VL + eDOCr2，跳过PaddleOCR")

    # 跳过PaddleOCR初始化（用户不需要）
    paddle_available = False
    logger.info("⏭️  跳过PaddleOCR初始化（按用户要求）")

    # 初始化eDOCr2
    edocr2_available = init_edocr2()

    # 统计可用引擎
    engines_status = []
    if edocr2_available:
        engines_status.append("eDOCr2 (GD&T+尺寸)")
    engines_status.append("Qwen3-VL (语义理解)")

    logger.info(f"✅ 双引擎OCR系统就绪: {' + '.join(engines_status)}")

    if not edocr2_available:
        logger.warning("⚠️  eDOCr2不可用 - 工业符号识别将受限")

    # 监听8003端口
    app.run(host='0.0.0.0', port=8003, debug=False)
