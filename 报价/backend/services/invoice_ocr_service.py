# services/invoice_ocr_service.py
# -*- coding: utf-8 -*-
"""
发票OCR识别服务
支持PaddleOCR本地识别 + 百度云API备用
"""
import os
import re
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
import base64

logger = logging.getLogger(__name__)


class InvoiceOCRService:
    """发票OCR识别服务"""

    def __init__(self):
        self.ocr_engine = None
        self.ocr_type = None  # 'ollama_vision', 'rapidocr' or 'paddleocr'
        self.use_cloud_api = os.getenv('USE_BAIDU_OCR', 'false').lower() == 'true'

        # Ollama Vision配置
        self.use_ollama_vision = os.getenv('USE_OLLAMA_VISION', 'true').lower() == 'true'
        self.ollama_base = os.getenv('LLM_BASE', 'http://localhost:11434')
        self.ollama_vision_model = os.getenv('LLM_VISION_MODEL', 'qwen3-vl:8b-instruct')
        self.ollama_available = False

        # 检查Ollama Vision是否可用（最高优先级）
        if self.use_ollama_vision and not self.use_cloud_api:
            self.ollama_available = self._check_ollama_available()
            if self.ollama_available:
                self.ocr_type = 'ollama_vision'
                logger.info(f"✅ Ollama Vision OCR已启用 (模型: {self.ollama_vision_model})")

        # 尝试初始化传统OCR引擎（作为Ollama的备用方案）
        if not self.use_cloud_api:
            # 方案1: 尝试RapidOCR (现代化、轻量级、自带模型)
            try:
                from rapidocr_onnxruntime import RapidOCR

                self.ocr_engine = RapidOCR()
                if not self.ollama_available:
                    self.ocr_type = 'rapidocr'
                logger.info(f"✅ RapidOCR初始化成功 (ONNX Runtime)")
            except ImportError:
                logger.info("ℹ️  RapidOCR未安装，尝试PaddleOCR...")

                # 方案2: 回退到PaddleOCR
                try:
                    from paddleocr import PaddleOCR

                    # PaddleOCR 3.x 初始化（自动检测设备）
                    self.ocr_engine = PaddleOCR()
                    if not self.ollama_available:
                        self.ocr_type = 'paddleocr'
                    logger.info(f"✅ PaddleOCR 3.x 初始化成功 (备用引擎)")
                except ImportError:
                    logger.warning("⚠️ OCR引擎未安装，将使用简单文本提取")
                    self.ocr_engine = None
                except Exception as e:
                    logger.error(f"❌ PaddleOCR初始化失败: {str(e)}")
                    self.ocr_engine = None
            except Exception as e:
                logger.error(f"❌ RapidOCR初始化失败: {str(e)}")
                self.ocr_engine = None

    def extract_invoice_info(self, file_path: str) -> Dict:
        """
        从发票文件中提取信息

        Args:
            file_path: 发票文件路径 (支持图片和PDF)

        Returns:
            {
                "success": bool,
                "invoice_number": str,
                "amount": float,
                "date": str,
                "confidence": float,
                "raw_text": str
            }
        """
        temp_image_path = None
        try:
            # 检查是否为PDF文件
            if file_path.lower().endswith('.pdf'):
                logger.info(f"📄 检测到PDF文件，正在转换为图片...")
                temp_image_path = self._convert_pdf_to_image(file_path)
                if not temp_image_path:
                    return {
                        "success": False,
                        "error": "PDF转图片失败",
                        "invoice_number": "",
                        "amount": 0.0,
                        "date": "",
                        "confidence": 0.0,
                        "raw_text": ""
                    }
                # 使用转换后的图片进行OCR
                file_path = temp_image_path
                logger.info(f"✅ PDF已转换为图片: {temp_image_path}")

            # 识别优先级: 云API > Ollama Vision > 传统OCR > Fallback
            logger.info(f"🔍 OCR配置: ollama_available={self.ollama_available}, ocr_type={self.ocr_type}, ocr_engine={self.ocr_engine is not None}")
            if self.use_cloud_api:
                return self._extract_with_baidu_api(file_path)
            elif self.ollama_available and self.ocr_type == 'ollama_vision':
                # 使用Ollama Vision (Qwen3-VL)
                logger.info("🤖 使用Ollama Vision进行发票识别...")
                vision_result = self._extract_with_ollama_vision(file_path)

                logger.info(f"🤖 Vision结果: {vision_result}")
                if vision_result:
                    # 将Vision模型结果转换为标准格式
                    return self._format_vision_result(vision_result)
                else:
                    # Vision失败，降级到传统OCR
                    logger.warning("⚠️  Ollama Vision识别失败，降级到传统OCR")
                    if self.ocr_engine:
                        return self._extract_with_paddleocr(file_path)
                    else:
                        return self._extract_with_fallback(file_path)
            elif self.ocr_engine:
                return self._extract_with_paddleocr(file_path)
            else:
                return self._extract_with_fallback(file_path)
        except Exception as e:
            logger.error(f"❌ OCR识别失败: {str(e)}")
            return {
                "success": False,
                "error": f"识别失败: {str(e)}",
                "invoice_number": "",
                "amount": 0.0,
                "date": "",
                "confidence": 0.0,
                "raw_text": ""
            }
        finally:
            # 清理临时图片文件
            if temp_image_path and os.path.exists(temp_image_path):
                try:
                    os.remove(temp_image_path)
                    logger.info(f"🗑️  已清理临时文件: {temp_image_path}")
                except Exception as e:
                    logger.warning(f"⚠️  清理临时文件失败: {str(e)}")

    def _extract_with_paddleocr(self, file_path: str) -> Dict:
        """使用OCR引擎识别（支持RapidOCR和PaddleOCR 3.x）"""
        try:
            # RapidOCR和PaddleOCR的调用方式不同
            if self.ocr_type == 'rapidocr':
                result, elapse = self.ocr_engine(file_path)
            else:
                # PaddleOCR 3.x 使用 predict() 方法
                result = self.ocr_engine.predict(file_path)

            # 调试：打印result结构
            logger.info(f"🔍 OCR原始结果类型: {type(result)}")
            if result:
                logger.info(f"🔍 OCR结果长度: {len(result)}")
                if len(result) > 0:
                    logger.info(f"🔍 OCR结果[0]类型: {type(result[0])}")

            # 检查result是否为空
            if not result or len(result) == 0:
                logger.warning("⚠️ OCR未识别到任何文本")
                return {
                    "success": False,
                    "error": "未识别到文本",
                    "invoice_number": "",
                    "amount": 0.0,
                    "date": "",
                    "confidence": 0.0,
                    "raw_text": ""
                }

            # 提取识别文本
            all_text = []
            avg_confidence = 0.0

            # PaddleOCR 3.x 格式: [{'rec_texts': [...], 'rec_scores': [...], ...}]
            if isinstance(result[0], dict) and 'rec_texts' in result[0]:
                # PaddleOCR 3.x new API
                page_result = result[0]  # 第一页结果
                texts = page_result.get('rec_texts', [])
                scores = page_result.get('rec_scores', [])

                logger.info(f"🔍 PaddleOCR 3.x: 识别到 {len(texts)} 行文本")

                for idx, (text, score) in enumerate(zip(texts, scores)):
                    try:
                        all_text.append(str(text))
                        avg_confidence += float(score)
                    except Exception as line_error:
                        logger.warning(f"⚠️ 处理第{idx}行出错: {line_error}")
                        continue

                if len(texts) > 0:
                    avg_confidence /= len(texts)

                # 合并所有文本
                full_text = "\n".join(all_text)
                logger.info(f"📝 OCR识别文本({len(all_text)}行):")
                logger.info(f"{'='*60}")
                logger.info(full_text)
                logger.info(f"{'='*60}")

                if not full_text.strip():
                    logger.warning("⚠️ OCR识别结果为空")
                    return {
                        "success": False,
                        "error": "识别结果为空",
                        "invoice_number": "",
                        "amount": 0.0,
                        "date": "",
                        "confidence": 0.0,
                        "raw_text": ""
                    }

                # 智能提取发票信息
                invoice_info = self._parse_invoice_text(full_text)
                invoice_info["success"] = True
                invoice_info["raw_text"] = full_text
                invoice_info["confidence"] = avg_confidence if avg_confidence > 0 else 0.85

                return invoice_info

            # RapidOCR格式: [[bbox, text, score], ...]
            if self.ocr_type == 'rapidocr':
                if result:
                    for idx, item in enumerate(result):
                        try:
                            # RapidOCR返回: [bbox, text, score]
                            if isinstance(item, (list, tuple)) and len(item) >= 3:
                                text = str(item[1])  # 第2个元素是文本
                                score = float(item[2])  # 第3个元素是置信度
                                all_text.append(text)
                                avg_confidence += score
                        except Exception as line_error:
                            logger.warning(f"⚠️ 处理RapidOCR第{idx}行出错: {line_error}")
                            continue
                    if all_text:
                        avg_confidence = avg_confidence / len(all_text)
                        logger.info(f"✅ RapidOCR识别到 {len(all_text)} 行文本，平均置信度: {avg_confidence:.2f}")
            else:
                # PaddleOCR格式
                ocr_result = result[0]

                # 检查是否是OCRResult对象（有json属性）
                if hasattr(ocr_result, 'json'):
                    # 新格式：OCRResult对象
                    result_data = ocr_result.json if isinstance(ocr_result.json, dict) else ocr_result

                    # 从rec_texts字段获取识别文本
                    if 'rec_texts' in result_data:
                        all_text = result_data['rec_texts']
                        logger.info(f"✅ 从OCRResult获取到 {len(all_text)} 行文本")

                        # 获取平均置信度
                        if 'rec_scores' in result_data and result_data['rec_scores']:
                            avg_confidence = sum(result_data['rec_scores']) / len(result_data['rec_scores'])
                            logger.info(f"✅ 平均置信度: {avg_confidence:.2f}")
                    else:
                        logger.warning("⚠️ OCRResult中未找到rec_texts字段")
                else:
                    # 旧格式：兼容老版本的列表格式
                    logger.info("⚠️ 检测到旧版OCR格式，使用兼容模式")
                    for idx, line in enumerate(ocr_result):
                        try:
                            if isinstance(line, (list, tuple)) and len(line) >= 2:
                                text_data = line[1]
                                if isinstance(text_data, (list, tuple)) and len(text_data) >= 1:
                                    text = str(text_data[0])
                                    all_text.append(text)
                        except Exception as line_error:
                            logger.warning(f"⚠️ 处理第{idx}行出错: {line_error}")
                            continue

            # 合并所有文本
            full_text = "\n".join(all_text)
            logger.info(f"📝 OCR识别文本({len(all_text)}行):")
            logger.info(f"{'='*60}")
            logger.info(full_text)  # 打印完整文本，方便调试
            logger.info(f"{'='*60}")

            if not full_text.strip():
                logger.warning("⚠️ OCR识别结果为空")
                return {
                    "success": False,
                    "error": "识别结果为空",
                    "invoice_number": "",
                    "amount": 0.0,
                    "date": "",
                    "confidence": 0.0,
                    "raw_text": ""
                }

            # 智能提取发票信息
            invoice_info = self._parse_invoice_text(full_text)
            invoice_info["success"] = True
            invoice_info["raw_text"] = full_text
            invoice_info["confidence"] = avg_confidence if avg_confidence > 0 else 0.85

            return invoice_info

        except Exception as e:
            logger.error(f"❌ PaddleOCR识别失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "invoice_number": "",
                "amount": 0.0,
                "date": "",
                "confidence": 0.0,
                "raw_text": ""
            }

    def _extract_with_baidu_api(self, file_path: str) -> Dict:
        """使用百度云API识别（需要配置API Key）"""
        try:
            from aip import AipOcr

            app_id = os.getenv('BAIDU_OCR_APP_ID')
            api_key = os.getenv('BAIDU_OCR_API_KEY')
            secret_key = os.getenv('BAIDU_OCR_SECRET_KEY')

            if not all([app_id, api_key, secret_key]):
                raise ValueError("百度OCR API配置不完整")

            client = AipOcr(app_id, api_key, secret_key)

            # 读取图片
            with open(file_path, 'rb') as f:
                image = f.read()

            # 调用增值税发票识别
            result = client.vatInvoice(image)

            if 'words_result' in result:
                words = result['words_result']
                return {
                    "success": True,
                    "invoice_number": words.get('InvoiceNum', ''),
                    "amount": self._parse_amount(words.get('AmountInFiguers', '')),
                    "date": self._parse_date(words.get('InvoiceDate', '')),
                    "confidence": 0.95,
                    "raw_text": str(words)
                }
            else:
                raise ValueError("API返回格式错误")

        except Exception as e:
            logger.error(f"❌ 百度OCR API调用失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "invoice_number": "",
                "amount": 0.0,
                "date": "",
                "confidence": 0.0,
                "raw_text": ""
            }

    def _extract_with_fallback(self, file_path: str) -> Dict:
        """简单文本提取（fallback方案）"""
        logger.warning("⚠️ 使用fallback方案，识别准确率较低")
        return {
            "success": False,
            "error": "OCR引擎未安装",
            "invoice_number": "",
            "amount": 0.0,
            "date": "",
            "confidence": 0.0,
            "raw_text": "请安装 paddlepaddle 和 paddleocr"
        }

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

                # 设置缩放因子以提高图片质量 (3.0 = 216 DPI，更高的DPI提升识别率)
                zoom = 3.0
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
                        dpi=150  # 150 DPI提供较好的OCR质量
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

    def _parse_invoice_text(self, text: str) -> Dict:
        """
        智能解析发票文本，提取关键信息

        支持多种发票格式：
        - 增值税专用发票
        - 增值税普通发票
        - 电子发票
        """
        invoice_info = {
            "invoice_code": "",
            "invoice_number": "",
            "invoice_date": "",
            "amount": 0.0,
            "date": "",  # 保持向后兼容
            "buyer_name": "",
            "buyer_tax_id": "",
            "seller_name": "",
            "seller_tax_id": "",
            "amount_before_tax": 0.0,
            "tax_amount": 0.0,
            "total_amount": 0.0,
            "remark": ""
        }

        lines = text.split('\n')

        # 1. 提取发票代码
        invoice_code = self._extract_invoice_code(text)
        if invoice_code:
            invoice_info["invoice_code"] = invoice_code

        # 2. 提取发票号码
        invoice_number = self._extract_invoice_number(text)
        if invoice_number:
            invoice_info["invoice_number"] = invoice_number

        # 3. 提取日期
        date_str = self._extract_date(text)
        if date_str:
            invoice_info["date"] = date_str
            invoice_info["invoice_date"] = date_str

        # 4. 提取购买方信息
        buyer_name = self._extract_buyer_name(text)
        if buyer_name:
            invoice_info["buyer_name"] = buyer_name

        buyer_tax_id = self._extract_buyer_tax_id(text)
        if buyer_tax_id:
            invoice_info["buyer_tax_id"] = buyer_tax_id

        # 5. 提取销售方信息
        seller_name = self._extract_seller_name(text)
        if seller_name:
            invoice_info["seller_name"] = seller_name

        seller_tax_id = self._extract_seller_tax_id(text)
        if seller_tax_id:
            invoice_info["seller_tax_id"] = seller_tax_id

        # 6. 提取金额信息
        amount_before_tax = self._extract_amount_before_tax(text)
        if amount_before_tax:
            invoice_info["amount_before_tax"] = amount_before_tax

        tax_amount = self._extract_tax_amount(text)
        if tax_amount:
            invoice_info["tax_amount"] = tax_amount

        total_amount = self._extract_amount(text)
        if total_amount:
            invoice_info["amount"] = total_amount
            invoice_info["total_amount"] = total_amount

        # 7. 提取备注
        remark = self._extract_remark(text)
        if remark:
            invoice_info["remark"] = remark

        return invoice_info

    def _extract_invoice_number(self, text: str) -> str:
        """提取发票号码"""
        # 清理空格和换行
        clean_text = text.replace(' ', '').replace('\n', '').replace('\r', '')

        patterns = [
            r'发票号码[:\s：]*([0-9]{8,20})',  # 扩展到20位
            r'No[:\s：]*([0-9]{8,20})',
            r'invoice\s*no[:\s：]*([0-9]{8,20})',
            r'票号[:\s：]*([0-9]{8,20})',
        ]

        # 先在清理后的文本中搜索
        for pattern in patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                number = match.group(1)
                # 验证：发票号通常是8-20位数字
                if 8 <= len(number) <= 20:
                    logger.info(f"✅ 识别到发票号: {number}")
                    return number

        # 如果没找到，在原文本中搜索
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number = match.group(1)
                if 8 <= len(number) <= 20:
                    logger.info(f"✅ 识别到发票号: {number}")
                    return number

        return ""

    def _extract_amount(self, text: str) -> float:
        """提取金额"""
        patterns = [
            r'[合价金]额[:\s：]*(￥|¥|RMB)?\s*([0-9,]+\.?[0-9]*)',
            r'小写[:\s：]*(￥|¥|RMB)?\s*([0-9,]+\.?[0-9]*)',
            r'价税合计[:\s：]*(￥|¥|RMB)?\s*([0-9,]+\.?[0-9]*)',
            r'total[:\s：]*(￥|¥|RMB)?\s*([0-9,]+\.?[0-9]*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(2).replace(',', '').replace(' ', '')
                try:
                    amount = float(amount_str)
                    if amount > 0:
                        logger.info(f"✅ 识别到金额: {amount}")
                        return amount
                except ValueError:
                    continue

        return 0.0

    def _extract_date(self, text: str) -> str:
        """提取日期"""
        patterns = [
            r'开票日期[:\s：]*(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})',
            r'date[:\s：]*(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})',
            r'(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})[日]?',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = match.group(1)
                month = match.group(2).zfill(2)
                day = match.group(3).zfill(2)
                date_str = f"{year}-{month}-{day}"

                # 验证日期有效性
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                    logger.info(f"✅ 识别到日期: {date_str}")
                    return date_str
                except ValueError:
                    continue

        return ""

    def _parse_amount(self, amount_str: str) -> float:
        """解析金额字符串"""
        if not amount_str:
            return 0.0
        try:
            return float(amount_str.replace(',', '').replace(' ', ''))
        except:
            return 0.0

    def _parse_date(self, date_str: str) -> str:
        """解析日期字符串"""
        if not date_str:
            return ""

        # 尝试多种日期格式
        formats = ['%Y%m%d', '%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日']
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        return date_str

    def _extract_invoice_code(self, text: str) -> str:
        """提取发票代码（10或12位数字）"""
        # 先清理文本中的空格和换行，避免数字被分隔
        clean_text = text.replace(' ', '').replace('\n', '').replace('\r', '')

        patterns = [
            r'发票代码[:\s：]*([0-9]{10,12})',
            r'代码[:\s：]*([0-9]{10,12})',
            r'code[:\s：]*([0-9]{10,12})',
            r'发票代号[:\s：]*([0-9]{10,12})',  # 新增
        ]

        # 先在清理后的文本中搜索
        for pattern in patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                code = match.group(1)
                if 10 <= len(code) <= 12:
                    logger.info(f"✅ 识别到发票代码: {code}")
                    return code

        # 如果没找到，尝试在原文本中搜索
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1)
                if 10 <= len(code) <= 12:
                    logger.info(f"✅ 识别到发票代码: {code}")
                    return code
        return ""

    def _extract_buyer_name(self, text: str) -> str:
        """提取购买方名称"""
        patterns = [
            # 匹配"名称："后面的内容，避免"购买方信息"这种标题
            r'购买方[^名]*名称[:\s：\n]+([^\n:：统一社会]{3,50})',
            r'买方[:\s：\n]+名称[:\s：\n]+([^\n:：统一社会]{3,50})',
            # 更宽松的备用匹配
            r'购货单位[:\s：\n]+([^\n:：]{3,50})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                name = match.group(1).strip()
                # 清理可能的多余字符
                name = re.sub(r'\s+', '', name)  # 移除所有空格
                # 排除以下无效结果
                invalid_names = ['信息', '销售方', '购买方', '名称', '统一社会信用代码', '纳税人识别号']
                is_invalid = any(inv in name for inv in invalid_names)
                # 排除纯数字和过短的结果，且名称中应有汉字
                has_chinese = any('\u4e00' <= c <= '\u9fff' for c in name)
                if len(name) >= 3 and not name.isdigit() and not is_invalid and has_chinese:
                    logger.info(f"✅ 识别到购买方名称: {name}")
                    return name
        return ""

    def _extract_buyer_tax_id(self, text: str) -> str:
        """提取购买方税号/统一社会信用代码"""
        patterns = [
            r'购买方.*?税号[:\s：]*([A-Z0-9]{15,20})',
            r'购买方.*?纳税人识别号[:\s：]*([A-Z0-9]{15,20})',
            r'购买方.*?统一社会信用代码[:\s：]*([A-Z0-9]{15,20})',
            r'税号[:\s：]*([A-Z0-9]{15,20})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                tax_id = match.group(1).strip()
                if 15 <= len(tax_id) <= 20:
                    logger.info(f"✅ 识别到购买方税号: {tax_id}")
                    return tax_id
        return ""

    def _extract_seller_name(self, text: str) -> str:
        """提取销售方名称（供应商）"""
        patterns = [
            r'销售方[名称\s]*[:\s：]*([\u4e00-\u9fa5a-zA-Z0-9（）()]+)',
            r'卖方[:\s：]*([\u4e00-\u9fa5a-zA-Z0-9（）()]+)',
            r'供应商[:\s：]*([\u4e00-\u9fa5a-zA-Z0-9（）()]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2:
                    logger.info(f"✅ 识别到销售方名称: {name}")
                    return name
        return ""

    def _extract_seller_tax_id(self, text: str) -> str:
        """提取销售方税号"""
        patterns = [
            r'销售方.*?税号[:\s：]*([A-Z0-9]{15,20})',
            r'销售方.*?纳税人识别号[:\s：]*([A-Z0-9]{15,20})',
            r'销售方.*?统一社会信用代码[:\s：]*([A-Z0-9]{15,20})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                tax_id = match.group(1).strip()
                if 15 <= len(tax_id) <= 20:
                    logger.info(f"✅ 识别到销售方税号: {tax_id}")
                    return tax_id
        return ""

    def _extract_amount_before_tax(self, text: str) -> float:
        """提取不含税金额"""
        patterns = [
            r'金额合计[:\s：]*(￥|¥|RMB)?\s*([0-9,]+\.?[0-9]*)',
            r'不含税金额[:\s：]*(￥|¥|RMB)?\s*([0-9,]+\.?[0-9]*)',
            r'合计金额[:\s：]*(￥|¥|RMB)?\s*([0-9,]+\.?[0-9]*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(2).replace(',', '').replace(' ', '')
                try:
                    amount = float(amount_str)
                    if amount > 0:
                        logger.info(f"✅ 识别到不含税金额: {amount}")
                        return amount
                except ValueError:
                    continue
        return 0.0

    def _extract_tax_amount(self, text: str) -> float:
        """提取税额"""
        # 清理文本，移除可能干扰识别的字符
        clean_text = text.replace(' ', '').replace('\n', '').replace('\r', '')

        patterns = [
            # 税额合计
            r'税额合计[:\s：]*(￥|¥|RMB)?([0-9,]+\.?[0-9]*)',
            # 单纯的"税额" + 金额符号
            r'税额[:\s：]*(￥|¥|RMB)([0-9,]+\.?[0-9]*)',
            # 增值税额
            r'增值税额[:\s：]*(￥|¥|RMB)?([0-9,]+\.?[0-9]*)',
            # 仅"税" + 符号 + 数字（更宽松）
            r'税[:\s：]*(￥|¥)([0-9,]+\.?[0-9]*)',
        ]

        # 先在清理后的文本中搜索
        for pattern in patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                amount_str = match.group(2).replace(',', '').replace(' ', '')
                try:
                    amount = float(amount_str)
                    # 税额应该大于0（0.0可能是识别错误）且合理范围内
                    if 0 < amount < 1000000:  # 税额通常不会超过100万
                        logger.info(f"✅ 识别到税额: {amount}")
                        return amount
                except ValueError:
                    continue

        # 如果没找到，在原文本中搜索
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(2).replace(',', '').replace(' ', '')
                try:
                    amount = float(amount_str)
                    if 0 < amount < 1000000:
                        logger.info(f"✅ 识别到税额: {amount}")
                        return amount
                except ValueError:
                    continue

        logger.warning("⚠️  未能识别税额，返回0.0")
        return 0.0

    def _extract_remark(self, text: str) -> str:
        """提取备注"""
        patterns = [
            r'备注[:\s：]*([\s\S]{1,200}?)(?=\n\n|\n[^\s]|$)',
            r'说明[:\s：]*([\s\S]{1,200}?)(?=\n\n|\n[^\s]|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                remark = match.group(1).strip()
                if len(remark) > 0:
                    logger.info(f"✅ 识别到备注: {remark[:50]}...")
                    return remark
        return ""

    def _check_ollama_available(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            import requests
            response = requests.get(f"{self.ollama_base}/api/tags", timeout=3)
            if response.status_code == 200:
                # 检查模型是否已下载
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                # 检查是否有qwen3-vl模型（可能是qwen3-vl:7b或qwen3-vl:latest等）
                has_model = any('qwen3-vl' in m or self.ollama_vision_model in m for m in models)
                if has_model:
                    logger.info(f"✅ Ollama Vision模型已就绪: {self.ollama_vision_model}")
                    return True
                else:
                    logger.warning(f"⚠️  Ollama服务运行中，但未找到模型: {self.ollama_vision_model}")
                    logger.warning(f"   可用模型: {', '.join(models)}")
                    return False
            return False
        except Exception as e:
            logger.debug(f"Ollama健康检查失败: {e}")
            return False

    def _extract_with_ollama_vision(self, image_path: str) -> Dict:
        """
        使用Ollama Vision (Qwen3-VL)识别发票

        Args:
            image_path: 发票图片路径

        Returns:
            发票字段字典
        """
        try:
            import requests
            import json

            # 读取图片并编码为base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # 构建提示词
            prompt = """请识别这张增值税发票的关键信息，并以JSON格式返回。

请提取以下字段：
- invoice_code: 发票代码（12位数字）
- invoice_number: 发票号码（8-20位数字）
- invoice_date: 开票日期（格式：YYYY-MM-DD）
- buyer_name: 购买方名称（公司全称）
- buyer_tax_id: 购买方纳税人识别号（15-20位）
- seller_name: 销售方名称（公司全称）
- seller_tax_id: 销售方纳税人识别号（15-20位）
- amount_before_tax: 金额/不含税金额（数字）
- tax_amount: 税额（数字）
- total_amount: 价税合计/总金额（数字）
- remark: 备注（可选）

只返回JSON格式，不要其他说明。示例：
{
  "invoice_code": "044001900111",
  "invoice_number": "12345678",
  "invoice_date": "2025-09-16",
  ...
}"""

            # 调用Ollama Vision API
            logger.info(f"🤖 使用Ollama Vision识别发票: {self.ollama_vision_model}")

            logger.info(f"🔍 Ollama base URL: {self.ollama_base}")
            logger.info(f"🔍 Image data size: {len(image_data)} bytes")

            try:
                response = requests.post(
                    f"{self.ollama_base}/api/generate",
                    json={
                        "model": self.ollama_vision_model,
                        "prompt": prompt,
                        "images": [image_data],
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # 低温度，更确定性
                            "num_predict": 1000,
                        }
                    },
                    timeout=120  # 增加超时时间
                )
                logger.info(f"🔍 Ollama response status: {response.status_code}")
            except Exception as req_error:
                logger.error(f"❌ Ollama 请求异常: {str(req_error)}")
                return {}

            if response.status_code != 200:
                logger.error(f"❌ Ollama API错误: {response.status_code}")
                logger.error(f"❌ 响应内容: {response.text[:500]}")
                return {}

            result = response.json()
            response_text = result.get('response', '').strip()

            logger.info(f"🤖 Qwen3-VL响应长度: {len(response_text)}")
            logger.info(f"🤖 Qwen3-VL响应前200字: {response_text[:200]}...")

            # 解析JSON响应
            invoice_data = self._parse_vision_response(response_text)

            if invoice_data:
                logger.info(f"✅ Ollama Vision识别成功")
                return invoice_data
            else:
                logger.warning(f"⚠️  无法解析Ollama Vision响应")
                return {}

        except Exception as e:
            logger.error(f"❌ Ollama Vision识别失败: {str(e)}")
            return {}

    def _parse_vision_response(self, response_text: str) -> Dict:
        """解析Vision模型的JSON响应"""
        try:
            import json

            # 移除markdown代码块标记
            if "```" in response_text:
                # 提取```json ... ```或``` ... ```中的内容
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
            for field in ['invoice_code', 'invoice_number', 'invoice_date',
                          'buyer_name', 'buyer_tax_id', 'seller_name', 'seller_tax_id', 'remark']:
                if field in data:
                    value = str(data[field]).strip()
                    if value and value != 'null' and value != 'None':
                        cleaned_data[field] = value

            # 数值字段
            for field in ['amount_before_tax', 'tax_amount', 'total_amount']:
                if field in data:
                    try:
                        value = float(str(data[field]).replace(',', '').replace('¥', '').replace('￥', '').strip())
                        if value >= 0:
                            cleaned_data[field] = value
                    except (ValueError, TypeError):
                        pass

            return cleaned_data

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return {}
        except Exception as e:
            logger.error(f"响应解析失败: {e}")
            return {}

    def _format_vision_result(self, vision_data: Dict) -> Dict:
        """
        将Vision模型结果转换为标准OCR结果格式

        Args:
            vision_data: Vision模型返回的发票数据字典

        Returns:
            标准格式的OCR结果
        """
        # 提取日期并格式化
        invoice_date = vision_data.get('invoice_date', '')
        if invoice_date and not invoice_date.startswith('20'):
            # 尝试转换日期格式
            try:
                from dateutil import parser
                dt = parser.parse(invoice_date)
                invoice_date = dt.strftime('%Y-%m-%d')
            except:
                pass

        return {
            "success": True,
            "invoice_code": vision_data.get('invoice_code', ''),
            "invoice_number": vision_data.get('invoice_number', ''),
            "invoice_date": invoice_date,
            "buyer_name": vision_data.get('buyer_name', ''),
            "buyer_tax_id": vision_data.get('buyer_tax_id', ''),
            "seller_name": vision_data.get('seller_name', ''),
            "seller_tax_id": vision_data.get('seller_tax_id', ''),
            "amount_before_tax": vision_data.get('amount_before_tax', 0.0),
            "tax_amount": vision_data.get('tax_amount', 0.0),
            "total_amount": vision_data.get('total_amount', 0.0),
            "remark": vision_data.get('remark', ''),
            "confidence": 0.95,  # Vision模型置信度通常很高
            "raw_text": f"Qwen3-VL Vision识别\n{vision_data}",
            "ocr_method": "ollama_vision"
        }


# 全局单例
_ocr_service = None

def get_ocr_service() -> InvoiceOCRService:
    """获取OCR服务单例"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = InvoiceOCRService()
    return _ocr_service

