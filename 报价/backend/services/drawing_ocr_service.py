# services/drawing_ocr_service.py
"""
图纸OCR识别服务
基于Ollama Vision (Qwen3-VL)
"""
import os
import base64
import logging
import requests
import numpy as np
from typing import Dict, Optional
from config.settings import settings

logger = logging.getLogger(__name__)


class DrawingOCRService:
    """图纸OCR识别服务 - 多引擎支持（向上兼容）"""

    def __init__(self):
        self.ollama_base = settings.OLLAMA_BASE_URL
        self.ollama_vision_model = settings.OLLAMA_VISION_MODEL
        self.ollama_available = self._check_ollama_available()

        if self.ollama_available:
            logger.info(f"✅ Ollama Vision OCR已启用 (模型: {self.ollama_vision_model})")
        else:
            logger.error(f"❌ Ollama Vision不可用！请确保Ollama服务正在运行，且已安装模型: {self.ollama_vision_model}")

    def _init_fallback_ocr(self):
        """初始化备用OCR引擎 - PaddleOCR优先"""
        # 方案1: 优先使用PaddleOCR (百度OCR，更强大的中文识别)
        try:
            from paddleocr import PaddleOCR

            # 使用CPU模式 (避免GPU依赖问题)
            self.ocr_engine = PaddleOCR(
                lang='ch',
                use_gpu=False,  # CPU模式
                use_angle_cls=True,  # 启用文字方向检测
                use_dilation=True  # 启用膨胀操作提高识别率
            )
            self.ocr_type = 'paddleocr'
            logger.info(f"✅ PaddleOCR初始化成功 (CPU模式) - 百度OCR引擎已启用")
            return
        except ImportError:
            logger.info("ℹ️  PaddleOCR未安装，尝试RapidOCR...")
        except Exception as e:
            logger.warning(f"⚠️  PaddleOCR初始化失败: {e}，回退到RapidOCR")

        # 方案2: 回退到RapidOCR (快速、轻量级)
        try:
            from rapidocr_onnxruntime import RapidOCR
            self.ocr_engine = RapidOCR()
            self.ocr_type = 'rapidocr'
            logger.info("✅ RapidOCR初始化成功 (ONNX Runtime)")
        except ImportError:
            logger.warning("⚠️  RapidOCR未安装")
            self.ocr_engine = None
        except Exception as e:
            logger.error(f"❌ RapidOCR初始化失败: {e}")
            self.ocr_engine = None

    def _check_ollama_available(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            response = requests.get(f"{self.ollama_base}/api/tags", timeout=3)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                has_model = any('qwen3-vl' in m or self.ollama_vision_model in m for m in models)
                if has_model:
                    logger.info(f"✅ Ollama Vision模型已就绪: {self.ollama_vision_model}")
                    return True
                else:
                    logger.warning(f"⚠️  Ollama服务运行中，但未找到模型: {self.ollama_vision_model}")
                    logger.warning(f"   可用模型: {', '.join(models)}")
            return False
        except Exception as e:
            logger.debug(f"Ollama健康检查失败: {e}")
            return False

    def _detect_layout_regions(self, image_path: str) -> Dict:
        """
        检测工程图纸的布局区域（Layout Analysis）

        识别关键区域：
        1. 标题栏（Title Block）- 通常在右下角，包含图号、材质、名称
        2. 尺寸标注区域（Dimension Annotations）- 包含外径、长度等尺寸
        3. 主视图区域（Main View）- 零件主体

        Args:
            image_path: 图纸图片路径

        Returns:
            {
                "title_block": {"x": int, "y": int, "w": int, "h": int},
                "dimension_areas": [{"x": int, "y": int, "w": int, "h": int}, ...],
                "main_view": {"x": int, "y": int, "w": int, "h": int}
            }
        """
        try:
            import cv2
            from PIL import Image

            logger.info("🔍 开始布局分析（Layout Analysis）...")

            # 读取图像
            pil_img = Image.open(image_path)
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            h, w = gray.shape

            # 1. 检测标题栏（Title Block）- 通常在右下角1/4区域
            title_block = None
            try:
                # 取右下角区域
                title_roi = gray[int(h*0.7):, int(w*0.6):]

                # 边缘检测找矩形框
                edges = cv2.Canny(title_roi, 50, 150)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                # 找最大的矩形区域（标题栏通常是最大的矩形框）
                max_area = 0
                best_rect = None
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area > max_area and area > (title_roi.shape[0] * title_roi.shape[1] * 0.1):
                        x, y, rect_w, rect_h = cv2.boundingRect(cnt)
                        # 标题栏通常是横向矩形（宽>高）
                        if rect_w > rect_h * 1.5:
                            max_area = area
                            best_rect = (x + int(w*0.6), y + int(h*0.7), rect_w, rect_h)

                if best_rect:
                    title_block = {"x": best_rect[0], "y": best_rect[1], "w": best_rect[2], "h": best_rect[3]}
                    logger.info(f"✓ 检测到标题栏: x={title_block['x']}, y={title_block['y']}, w={title_block['w']}, h={title_block['h']}")
                else:
                    # 如果没找到，默认右下角1/6区域
                    title_block = {"x": int(w*0.7), "y": int(h*0.8), "w": int(w*0.3), "h": int(h*0.2)}
                    logger.info(f"⚠️  未检测到标题栏框线，使用默认区域")
            except Exception as e:
                logger.warning(f"⚠️  标题栏检测失败: {e}，使用默认区域")
                title_block = {"x": int(w*0.7), "y": int(h*0.8), "w": int(w*0.3), "h": int(h*0.2)}

            # 2. 检测尺寸标注区域（Dimension Annotations）- 识别箭头和Φ符号
            dimension_areas = []
            try:
                # 二值化
                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                # 使用形态学操作检测水平和垂直线（尺寸线通常是直线）
                horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
                vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

                horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
                vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)

                # 合并水平和垂直线
                dimension_mask = cv2.add(horizontal_lines, vertical_lines)

                # 找连通区域
                contours, _ = cv2.findContours(dimension_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area > 100:  # 过滤小噪点
                        x, y, rect_w, rect_h = cv2.boundingRect(cnt)
                        # 扩展区域以包含标注文字
                        padding = 20
                        x = max(0, x - padding)
                        y = max(0, y - padding)
                        rect_w = min(w - x, rect_w + 2*padding)
                        rect_h = min(h - y, rect_h + 2*padding)
                        dimension_areas.append({"x": x, "y": y, "w": rect_w, "h": rect_h})

                logger.info(f"✓ 检测到 {len(dimension_areas)} 个尺寸标注区域")
            except Exception as e:
                logger.warning(f"⚠️  尺寸标注区域检测失败: {e}")

            # 3. 主视图区域（排除标题栏后的主要区域）
            main_view = {"x": 0, "y": 0, "w": w, "h": int(h*0.75)}
            logger.info(f"✓ 主视图区域: w={main_view['w']}, h={main_view['h']}")

            layout = {
                "title_block": title_block,
                "dimension_areas": dimension_areas[:10],  # 限制最多10个区域
                "main_view": main_view,
                "image_size": {"width": w, "height": h}
            }

            logger.info(f"✅ 布局分析完成: 标题栏={title_block is not None}, 尺寸区域={len(dimension_areas)}")
            return layout

        except Exception as e:
            logger.error(f"❌ 布局分析失败: {e}")
            return {}

    def _enhance_drawing_image(self, image_path: str, for_ocr: bool = False) -> str:
        """
        增强工程图纸图像质量（专业预处理）

        Args:
            image_path: 原始图片路径
            for_ocr: 是否为传统OCR优化（True=高对比度二值化，False=保留灰度用于Vision模型）

        Returns:
            增强后的图片路径
        """
        try:
            import cv2
            from PIL import Image

            # 读取图像（处理中文路径）
            try:
                # 使用numpy和PIL读取，避免中文路径问题
                pil_img = Image.open(image_path)
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except Exception as e:
                logger.warning(f"⚠️  无法读取图像: {image_path}, 错误: {e}")
                return image_path

            if img is None or img.size == 0:
                logger.warning(f"⚠️  图像为空: {image_path}")
                return image_path

            logger.info(f"🔧 开始图像预处理增强（for_ocr={for_ocr}）...")

            # 1. 转换为灰度图
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img

            # 2. 去噪（保留细节的去噪）
            denoised = cv2.fastNlMeansDenoising(gray, h=10)
            logger.info("✓ 去噪完成")

            # 3. CLAHE对比度增强（机械图纸通常对比度不足）
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            logger.info("✓ CLAHE对比度增强完成")

            if for_ocr:
                # 传统OCR需要高对比度二值化
                # 4. 自适应阈值二值化（处理光照不均）
                binary = cv2.adaptiveThreshold(
                    enhanced,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11,  # 邻域大小
                    2    # 常数C
                )
                logger.info("✓ 自适应二值化完成（OCR优化）")

                # 5. 形态学操作（去除噪点，连接断裂文字）
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
                logger.info("✓ 形态学处理完成")

                final_img = processed
            else:
                # Vision模型保留灰度信息，只做锐化
                # 4. 锐化（增强边缘，提升文字和线条清晰度）
                kernel_sharpen = np.array([
                    [-1, -1, -1],
                    [-1,  9, -1],
                    [-1, -1, -1]
                ])
                sharpened = cv2.filter2D(enhanced, -1, kernel_sharpen)
                logger.info("✓ 图像锐化完成（Vision优化）")

                final_img = sharpened

            # 保存增强后的图像（处理中文路径）
            import os
            base, ext = os.path.splitext(image_path)
            enhanced_path = f"{base}_enhanced{ext}"

            try:
                # 使用PIL保存，避免中文路径问题
                final_img_rgb = cv2.cvtColor(final_img, cv2.COLOR_GRAY2RGB) if len(final_img.shape) == 2 else cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB)
                pil_result = Image.fromarray(final_img_rgb)
                pil_result.save(enhanced_path)
                logger.info(f"✅ 图像预处理完成，保存至: {enhanced_path}")
                return enhanced_path
            except Exception as save_error:
                logger.error(f"❌ 保存增强图像失败: {save_error}")
                return image_path

        except ImportError:
            logger.warning("⚠️  OpenCV未安装，跳过图像增强 (pip install opencv-python)")
            return image_path
        except Exception as e:
            logger.error(f"❌ 图像增强失败: {str(e)}")
            return image_path

    def extract_drawing_info(self, file_path: str) -> Dict:
        """
        从图纸文件中提取信息

        Args:
            file_path: 图纸文件路径 (支持图片和PDF)

        Returns:
            {
                "success": bool,
                "drawing_number": str,
                "customer_name": str,
                "product_name": str,
                "material": str,
                "outer_diameter": str,
                "length": str,
                "tolerance": str,
                "surface_roughness": str,
                "dimensions": dict,
                "processes": list,
                "confidence": float,
                "raw_text": str
            }
        """
        temp_image_path = None
        try:
            # 直接使用本地Ollama Vision（不使用回退机制）
            # 检查是否为PDF文件
            if file_path.lower().endswith('.pdf'):
                logger.info(f"📄 检测到PDF文件，正在转换为图片...")
                temp_image_path = self._convert_pdf_to_image(file_path)
                if not temp_image_path:
                    return {
                        "success": False,
                        "error": "PDF转图片失败"
                    }
                file_path = temp_image_path
                logger.info(f"✅ PDF已转换为图片: {temp_image_path}")

            # 使用Ollama Vision识别（不降级）
            if not self.ollama_available:
                return {
                    "success": False,
                    "error": "Ollama Vision服务不可用"
                }

            logger.info("🤖 使用本地Ollama Vision进行图纸识别...")
            # 为Vision模型增强图像（保留灰度，锐化边缘）
            enhanced_path = self._enhance_drawing_image(file_path, for_ocr=False)

            # 布局分析（Layout Analysis）- 检测关键区域
            layout_info = self._detect_layout_regions(enhanced_path)

            # 使用布局信息增强识别
            vision_result = self._extract_with_ollama_vision(enhanced_path, layout_info=layout_info)

            if vision_result:
                return self._format_vision_result(vision_result)
            else:
                logger.error("❌ Ollama Vision识别失败")
                return {
                    "success": False,
                    "error": "Ollama Vision识别失败，请检查图纸质量或模型状态"
                }

        except Exception as e:
            logger.error(f"❌ OCR识别失败: {str(e)}")
            return {
                "success": False,
                "error": f"识别失败: {str(e)}"
            }
        finally:
            # 清理临时图片文件
            if temp_image_path and os.path.exists(temp_image_path):
                try:
                    os.remove(temp_image_path)
                    logger.info(f"🗑️  已清理临时文件: {temp_image_path}")
                except Exception as e:
                    logger.warning(f"⚠️  清理临时文件失败: {str(e)}")

    def _extract_with_ollama_vision(self, image_path: str, layout_info: Dict = None) -> Dict:
        """
        使用Ollama Vision (Qwen3-VL)识别图纸

        Args:
            image_path: 图纸图片路径
            layout_info: 布局分析信息（可选），包含标题栏和尺寸标注区域

        Returns:
            图纸信息字典
        """
        try:
            # 压缩图片以提高处理速度
            from PIL import Image
            import io

            img = Image.open(image_path)

            # 如果图片太大，调整大小（保持宽高比）
            max_size = 2048
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"📐 图片已调整大小: {img.size}")

            # 转换为RGB（处理所有非RGB格式）
            if img.mode != 'RGB':
                logger.info(f"📐 转换图片格式: {img.mode} → RGB")
                if img.mode in ('RGBA', 'LA'):
                    # 带透明通道的，需要白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode == 'P':
                    # 调色板模式
                    img = img.convert('RGBA')
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode in ('L', 'I', 'F'):
                    # 灰度图或其他单通道图像，直接转RGB
                    img = img.convert('RGB')
                else:
                    # 其他格式直接转换
                    img = img.convert('RGB')

            # 保存为JPEG并编码base64（JPEG比PNG小很多）
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

            logger.info(f"📊 图片base64大小: {len(image_data) / 1024:.1f} KB")

            # 构建提示词 - 工程图纸专业版（带布局分析增强）
            layout_hint = ""
            if layout_info and layout_info.get('title_block'):
                tb = layout_info['title_block']
                img_size = layout_info.get('image_size', {})
                if img_size:
                    # 计算相对位置百分比
                    x_percent = (tb['x'] / img_size['width']) * 100 if img_size.get('width') else 0
                    y_percent = (tb['y'] / img_size['height']) * 100 if img_size.get('height') else 0
                    layout_hint = f"\n\n**布局分析提示**：\n- 系统已检测到标题栏位于图纸右下角（约{x_percent:.0f}%横向，{y_percent:.0f}%纵向位置）\n- 图号、材质、产品名称应该在这个区域内\n- 请重点关注右下角的矩形框内的文字信息"

            dim_hint = ""
            if layout_info and layout_info.get('dimension_areas'):
                dim_count = len(layout_info['dimension_areas'])
                dim_hint = f"\n- 系统检测到{dim_count}个尺寸标注区域，请在这些区域寻找Φ和长度数值"

            prompt = f"""你是一个专业的机加工图纸分析专家。请仔细分析这张工程图纸，按照以下步骤提取信息：

**识别重点**：
1. 基本信息（标题栏区域 - 通常在右下角）：
   - 图号：如"CPN01802"、"8001-0003095"
   - 客户名称：公司名称或客户代码
   - 产品名称：零件名称
   - 材质：如SUS303、SUS304、45钢、6061铝合金

2. 尺寸信息（主视图周围的标注）：
   - 外径：寻找"Φ"符号，如"Φ7.8"、"Φ10"
   - 长度：主要长度尺寸，如"240.4"、"150"
   - 重量：如有标注

3. 技术要求（通常在图纸左侧或下方的技术要求栏）：
   - 公差等级：如"±0.05"、"IT7"、"h6"、"GB/T1804-f级"
   - 表面粗糙度：如"Ra3.2"、"Ra1.6"、"▽"符号
   - 热处理：如"淬火"、"回火"、"调质"、"HRC30-35"
   - 表面处理：如"镀锌"、"发黑"、"阳极氧化"、"钝化"、"无电解镍"

4. **特殊要求（重要！必须完整提取）**：
   - 通常标注为"技术要求："、"注："、"说明："等
   - 可能包含多条（1、2、3...或a、b、c...）
   - 每条要求都要完整保留，包括：
     * 材质要求
     * 外观要求（毛刺、锐边等）
     * 倒角、圆角要求
     * 未注公差、粗糙度、形位公差的处理标准
     * 检验基准
     * 认证要求（如ROHS）
   - **必须保留原文，按条目换行，完整提取所有内容**{dim_hint}{layout_hint}

**查找提示**：
- 技术要求通常在图纸左侧或下方单独的文字说明栏
- 表面粗糙度用符号▽或Ra表示
- 公差可能在尺寸标注旁边，如"7.8±0.05"
- 热处理和表面处理通常在技术要求栏明确标注
- **特殊要求栏往往有编号（1、2、3...），务必全部提取，不要遗漏**

请以JSON格式返回，**必须包含所有字段**，找不到的用空字符串：

{{
  "drawing_number": "图号",
  "customer_name": "客户名称",
  "product_name": "产品名称",
  "customer_part_number": "客户料号（如8001-0003095）",
  "material": "材质",
  "outer_diameter": "外径（包含Φ符号）",
  "length": "长度",
  "weight": "重量",
  "tolerance": "公差等级",
  "surface_roughness": "表面粗糙度",
  "heat_treatment": "热处理要求",
  "surface_treatment": "表面处理要求",
  "special_requirements": "**完整**的特殊要求（所有条目，按换行符分隔，如：1、材质：SUS303\\n2、外观平滑，不得有毛刺、锐边\\n3、未注倒角为C0.5\\n...）"
}}

**关于special_requirements的重要说明**：
- 这个字段非常重要，必须**完整提取**所有技术要求条目
- 如果有多条，用\\n分隔，保持原文格式
- 包括所有编号（1、2、3...）的要求
- 不要总结，不要省略，原文照抄

只返回JSON，不要任何其他文字。"""

            # 调用Ollama Vision API
            logger.info(f"🤖 开始调用Ollama Vision: {self.ollama_vision_model}")
            logger.info(f"📋 提示词: {prompt[:100]}...")
            logger.info(f"🖼️  图片大小: {len(image_data)} 字符 ({len(image_data)/1024:.1f} KB)")

            api_url = f"{self.ollama_base}/api/generate"
            request_data = {
                "model": self.ollama_vision_model,
                "prompt": prompt,
                "images": [image_data],
                "stream": False
            }

            logger.info(f"🌐 请求URL: {api_url}")
            logger.info(f"📦 请求数据: model={request_data['model']}, stream={request_data['stream']}, images_count=1")

            import time
            start_time = time.time()

            response = requests.post(api_url, json=request_data, timeout=180)

            elapsed = time.time() - start_time
            logger.info(f"⏱️  API调用耗时: {elapsed:.2f}秒")

            if response.status_code != 200:
                logger.error(f"❌ Ollama API错误: HTTP {response.status_code}")
                logger.error(f"响应内容: {response.text[:500]}")
                return {}

            result = response.json()
            logger.info(f"📥 收到响应，keys: {list(result.keys())}")

            response_text = result.get('response', '').strip()

            # 详细调试日志
            if not response_text:
                logger.error(f"❌ Ollama返回空响应")
                logger.error(f"完整结果: {result}")
                logger.error(f"model字段: {result.get('model', 'N/A')}")
                logger.error(f"done字段: {result.get('done', 'N/A')}")
                return {}

            logger.info(f"✅ Qwen3-VL成功响应，长度: {len(response_text)} 字符")
            logger.info(f"📝 响应内容前300字: {response_text[:300]}...")

            # 解析JSON响应
            drawing_data = self._parse_vision_response(response_text)

            if drawing_data:
                logger.info(f"✅ Ollama Vision识别成功")
                return drawing_data
            else:
                logger.warning(f"⚠️  无法解析Ollama Vision响应")
                return {}

        except Exception as e:
            logger.error(f"❌ Ollama Vision识别失败: {str(e)}")
            return {}

    def _parse_vision_response(self, response_text: str) -> Dict:
        """解析Vision模型的JSON响应"""
        import json
        import re
        try:
            # 移除markdown代码块标记
            if "```" in response_text:
                parts = response_text.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    # 尝试解析这个部分
                    try:
                        data = json.loads(part)
                        if isinstance(data, dict):
                            return data
                    except:
                        continue

            # 直接尝试解析
            data = json.loads(response_text)

            if not isinstance(data, dict):
                return {}

            # 验证并清理数据
            cleaned_data = {}

            # 字符串字段
            string_fields = [
                'drawing_number', 'customer_name', 'product_name', 'customer_part_number',
                'material', 'outer_diameter', 'length', 'tolerance', 'surface_roughness',
                'weight', 'special_requirements'
            ]
            for field in string_fields:
                if field in data:
                    value = str(data[field]).strip()
                    if value and value != 'null' and value != 'None' and value != '':
                        cleaned_data[field] = value

            # 字典字段
            if 'dimensions' in data and isinstance(data['dimensions'], dict):
                cleaned_data['dimensions'] = data['dimensions']

            # 列表字段
            if 'processes' in data and isinstance(data['processes'], list):
                cleaned_data['processes'] = [str(p).strip() for p in data['processes'] if p]

            # ========== 智能后处理：从完整响应文本中提取缺失字段 ==========
            logger.info("🔍 开始智能后处理，检查缺失字段...")

            # 如果外径为空，尝试从完整文本中提取
            if not cleaned_data.get('outer_diameter'):
                logger.info("⚠️  外径字段为空，尝试从完整文本提取...")
                # 匹配 Φ 符号后的数字（支持小数）
                diameter_patterns = [
                    r'[ΦφФ]\s*(\d+\.?\d*)',  # Φ7.8, φ10
                    r'直径[：:]*\s*[ΦφФ]?\s*(\d+\.?\d*)',  # 直径:10, 直径Φ7.8
                    r'外径[：:]*\s*[ΦφФ]?\s*(\d+\.?\d*)',  # 外径:10
                    r'"outer_diameter"[：:]*\s*"?[ΦφФ]?\s*(\d+\.?\d*)"?',  # JSON中的外径
                ]
                for pattern in diameter_patterns:
                    matches = re.findall(pattern, response_text)
                    if matches:
                        # 取第一个匹配的数字
                        diameter_value = matches[0]
                        cleaned_data['outer_diameter'] = f"Φ{diameter_value}"
                        logger.info(f"✅ 智能提取外径: {cleaned_data['outer_diameter']}")
                        break
                else:
                    logger.warning("⚠️  未能从文本中提取到外径信息")

            # 如果长度为空，尝试提取
            if not cleaned_data.get('length'):
                logger.info("⚠️  长度字段为空，尝试从完整文本提取...")
                length_patterns = [
                    r'长度[：:]*\s*(\d+\.?\d*)',  # 长度:240.4
                    r'"length"[：:]*\s*"?(\d+\.?\d*)"?',  # JSON中的长度
                ]
                for pattern in length_patterns:
                    matches = re.findall(pattern, response_text)
                    if matches:
                        cleaned_data['length'] = matches[0]
                        logger.info(f"✅ 智能提取长度: {cleaned_data['length']}")
                        break

            logger.info(f"✅ 智能后处理完成，最终字段数: {len(cleaned_data)}")
            return cleaned_data

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            # 即使JSON解析失败，也尝试用正则提取关键信息
            return self._extract_from_text_fallback(response_text)
        except Exception as e:
            logger.error(f"响应解析失败: {e}")
            return {}

    def _extract_from_text_fallback(self, text: str) -> Dict:
        """
        当JSON解析失败时，从纯文本中提取信息的fallback方法

        Args:
            text: Vision模型返回的纯文本响应

        Returns:
            提取到的字段字典
        """
        import re
        logger.warning("⚠️  JSON解析失败，尝试从纯文本提取...")
        extracted = {}

        # 提取图号
        drawing_patterns = [
            r'图号[：:\s]*([A-Z0-9\-]+)',
            r'drawing[_\s]*number[：:\s]*([A-Z0-9\-]+)',
            r'CPN\d+',
            r'\d{4,}-\d+',
        ]
        for pattern in drawing_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['drawing_number'] = match.group(1) if '(' in pattern else match.group(0)
                break

        # 提取材质
        material_patterns = [
            r'材质[：:\s]*(SUS\d+|[A-Z0-9]+钢|铝合金|黄铜|紫铜)',
            r'material[：:\s]*([A-Z0-9]+)',
        ]
        for pattern in material_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['material'] = match.group(1)
                break

        # 提取产品名称
        product_patterns = [
            r'产品[名称]*[：:\s]*([\u4e00-\u9fa5A-Za-z0-9]+)',
            r'product[_\s]*name[：:\s]*([\u4e00-\u9fa5A-Za-z0-9]+)',
        ]
        for pattern in product_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['product_name'] = match.group(1)
                break

        # 提取外径
        diameter_patterns = [
            r'[ΦφФ]\s*(\d+\.?\d*)',
            r'外径[：:\s]*[ΦφФ]?\s*(\d+\.?\d*)',
        ]
        for pattern in diameter_patterns:
            match = re.search(pattern, text)
            if match:
                extracted['outer_diameter'] = f"Φ{match.group(1)}"
                break

        # 提取长度
        length_patterns = [
            r'长度[：:\s]*(\d+\.?\d*)',
            r'length[：:\s]*(\d+\.?\d*)',
        ]
        for pattern in length_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['length'] = match.group(1)
                break

        logger.info(f"📝 Fallback提取结果: {extracted}")
        return extracted

    def _format_vision_result(self, vision_data: Dict) -> Dict:
        """
        将Vision模型结果转换为标准OCR结果格式

        Args:
            vision_data: Vision模型返回的图纸数据字典

        Returns:
            标准格式的OCR结果
        """
        return {
            "success": True,
            "drawing_number": vision_data.get('drawing_number', ''),
            "customer_name": vision_data.get('customer_name', ''),
            "product_name": vision_data.get('product_name', ''),
            "customer_part_number": vision_data.get('customer_part_number', ''),
            "material": vision_data.get('material', ''),
            "outer_diameter": vision_data.get('outer_diameter', ''),
            "length": vision_data.get('length', ''),
            "tolerance": vision_data.get('tolerance', ''),
            "surface_roughness": vision_data.get('surface_roughness', ''),
            "weight": vision_data.get('weight', ''),
            "dimensions": vision_data.get('dimensions', {}),
            "processes": vision_data.get('processes', []),
            "special_requirements": vision_data.get('special_requirements', ''),
            "confidence": 0.95,  # Vision模型置信度通常很高
            "raw_data": vision_data,
            "ocr_method": "ollama_vision"
        }

    def _extract_with_traditional_ocr(self, image_path: str) -> Dict:
        """使用传统OCR识别（RapidOCR或PaddleOCR）"""
        all_text = []
        full_text = ""

        try:
            # RapidOCR识别
            if self.ocr_type == 'rapidocr':
                result, elapse = self.ocr_engine(image_path)

                # 安全地记录耗时（elapse可能是list或float）
                if elapse is not None:
                    try:
                        # 如果是list，取平均值
                        if isinstance(elapse, (list, tuple)):
                            elapse_time = sum(elapse) / len(elapse) if elapse else 0
                        else:
                            elapse_time = float(elapse)
                        logger.info(f"⏱️  RapidOCR识别耗时: {elapse_time:.2f}秒")
                    except:
                        logger.info(f"⏱️  RapidOCR识别完成")

                if not result:
                    return {"success": False, "error": "未识别到文本"}

                # 提取文本
                for item in result:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        all_text.append(str(item[1]))

                full_text = "\n".join(all_text)

            # PaddleOCR识别
            elif self.ocr_type == 'paddleocr':
                result = self.ocr_engine.ocr(image_path)

                if not result or len(result) == 0:
                    return {"success": False, "error": "未识别到文本"}

                # 提取文本
                all_text = []
                ocr_result = result[0]

                for line in ocr_result:
                    if isinstance(line, (list, tuple)) and len(line) >= 2:
                        text_data = line[1]
                        if isinstance(text_data, (list, tuple)):
                            all_text.append(str(text_data[0]))

                full_text = "\n".join(all_text)

            else:
                return {"success": False, "error": "OCR引擎未初始化"}

            # 安全地记录识别结果
            try:
                logger.info(f"📝 OCR识别到 {len(all_text)} 行文本")
            except Exception as log_error:
                logger.warning(f"日志记录失败: {type(all_text)}, {log_error}")

            # 智能解析图纸信息
            drawing_info = self._parse_drawing_text(full_text)
            drawing_info["success"] = True
            drawing_info["raw_data"] = {"full_text": full_text}
            drawing_info["ocr_method"] = self.ocr_type

            return drawing_info

        except Exception as e:
            import traceback
            error_msg = str(e)
            error_trace = traceback.format_exc()
            logger.error(f"❌ 传统OCR识别失败: {error_msg}")
            logger.error(f"详细错误:\n{error_trace}")
            return {"success": False, "error": error_msg}

    def _parse_drawing_text(self, text: str) -> Dict:
        """智能解析图纸文本"""
        import re

        info = {
            "drawing_number": "",
            "customer_name": "",
            "product_name": "",
            "material": "",
            "outer_diameter": "",
            "length": "",
            "tolerance": "",
            "surface_roughness": "",
            "special_requirements": "",
        }

        # 提取图号
        patterns = [
            r'图号[:\s：]*([A-Z0-9\-\.]+)',
            r'Drawing\s*No[:\s：]*([A-Z0-9\-\.]+)',
            r'物料代码[:\s：]*([A-Z0-9\-\.]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and len(match.group(1)) >= 3:
                info["drawing_number"] = match.group(1)
                break

        # 提取材质
        material_patterns = [
            r'材[质料][:\s：]*(SUS\d+|[0-9]+[不锈钢]|铝合金|钢|铜)',
            r'Material[:\s：]*([A-Z0-9]+)',
        ]
        for pattern in material_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info["material"] = match.group(1)
                break

        # 提取尺寸
        diameter_match = re.search(r'φ\s*([0-9\.]+)', text)
        if diameter_match:
            info["outer_diameter"] = f"φ{diameter_match.group(1)}"

        length_match = re.search(r'长[度]?[:\s：]*([0-9\.]+)', text)
        if length_match:
            info["length"] = length_match.group(1)

        # 提取特殊技术要求
        # 查找技术要求部分（通常以"技术要求"、"注"、"说明"等开头）
        tech_req_patterns = [
            r'技术要求[：:\s]*(.+?)(?=\n\n|\Z)',  # 技术要求后的内容，直到遇到空行或结尾
            r'注[：:\s]*(.+?)(?=\n\n|\Z)',  # 注：后的内容
            r'说明[：:\s]*(.+?)(?=\n\n|\Z)',  # 说明：后的内容
        ]

        for pattern in tech_req_patterns:
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                req_text = match.group(1).strip()
                # 清理提取的文本，移除多余的空白
                lines = [line.strip() for line in req_text.split('\n') if line.strip()]
                if lines:
                    info["special_requirements"] = '\n'.join(lines)
                    logger.info(f"✅ 提取到{len(lines)}条特殊技术要求")
                    break

        # 如果上面的模式没匹配到，尝试查找带编号的技术要求（1、2、3...）
        if not info["special_requirements"]:
            numbered_lines = []
            for line in text.split('\n'):
                line = line.strip()
                # 匹配以数字+顿号或点号开头的行
                if re.match(r'^\d+[、．.]', line):
                    numbered_lines.append(line)

            if numbered_lines:
                info["special_requirements"] = '\n'.join(numbered_lines)
                logger.info(f"✅ 提取到{len(numbered_lines)}条编号技术要求")

        return info

    def _convert_pdf_to_image(self, pdf_path: str) -> Optional[str]:
        """
        将PDF文件的第一页转换为图片

        Args:
            pdf_path: PDF文件路径

        Returns:
            临时图片文件路径，失败返回None
        """
        try:
            # 方案1: 尝试使用PyMuPDF (fitz) - 轻量级、快速
            try:
                import fitz  # PyMuPDF

                # 打开PDF
                doc = fitz.open(pdf_path)
                if len(doc) == 0:
                    logger.error("❌ PDF文件为空")
                    return None

                # 获取第一页
                page = doc[0]

                # 设置缩放因子 - 降低到2.0以提速 (2.0 = 144 DPI，足够OCR)
                zoom = 2.0
                mat = fitz.Matrix(zoom, zoom)

                # 渲染为图片
                pix = page.get_pixmap(matrix=mat)

                # 生成临时文件路径
                temp_dir = os.path.dirname(pdf_path)
                temp_filename = f"temp_ocr_{os.path.basename(pdf_path)}.png"
                temp_path = os.path.join(temp_dir, temp_filename)

                # 保存为PNG
                pix.save(temp_path)
                doc.close()

                logger.info(f"✅ 使用PyMuPDF转换PDF成功: {temp_path}")
                return temp_path

            except ImportError:
                logger.info("ℹ️  PyMuPDF未安装，尝试pdf2image...")

                # 方案2: 回退到pdf2image
                try:
                    from pdf2image import convert_from_path

                    # 只转换第一页
                    images = convert_from_path(
                        pdf_path,
                        first_page=1,
                        last_page=1,
                        dpi=200  # 200 DPI提供较好的OCR质量
                    )

                    if not images or len(images) == 0:
                        logger.error("❌ PDF转换失败，未生成图片")
                        return None

                    # 生成临时文件路径
                    temp_dir = os.path.dirname(pdf_path)
                    temp_filename = f"temp_ocr_{os.path.basename(pdf_path)}.png"
                    temp_path = os.path.join(temp_dir, temp_filename)

                    # 保存第一页
                    images[0].save(temp_path, 'PNG')

                    logger.info(f"✅ 使用pdf2image转换PDF成功: {temp_path}")
                    return temp_path

                except ImportError:
                    logger.error("❌ 未安装PDF转换库 (PyMuPDF 或 pdf2image)")
                    logger.error("💡 请安装: pip install PyMuPDF 或 pip install pdf2image")
                    return None
                except Exception as e:
                    logger.error(f"❌ pdf2image转换失败: {str(e)}")
                    return None

        except Exception as e:
            logger.error(f"❌ PDF转图片失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return None


# 全局单例
_ocr_service = None


def get_ocr_service() -> DrawingOCRService:
    """获取OCR服务单例"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = DrawingOCRService()
    return _ocr_service
