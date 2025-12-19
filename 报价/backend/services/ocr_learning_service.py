# services/ocr_learning_service.py
"""
OCR学习优化服务
实现智能规则验证和Prompt动态优化
"""
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from models.ocr_correction import OCRCorrection
from difflib import SequenceMatcher
import re
import logging

logger = logging.getLogger(__name__)

# 延迟导入向量存储服务，避免循环依赖
_vector_store_service = None

def _get_vector_store():
    """延迟获取向量存储服务"""
    global _vector_store_service
    if _vector_store_service is None:
        try:
            from services.vector_store_service import get_vector_store_service
            _vector_store_service = get_vector_store_service()
        except Exception as e:
            logger.warning(f"⚠️  向量存储服务不可用: {e}")
    return _vector_store_service


class OCRLearningService:
    """OCR智能学习服务"""

    # 智能规则库
    SMART_RULES = {
        # 材料标准化规则
        'material': {
            'patterns': [
                (r'sus\s*303', 'SUS303', re.IGNORECASE),
                (r'sus\s*304', 'SUS304', re.IGNORECASE),
                (r'45\s*#', '45#', re.IGNORECASE),
                (r'45号钢', '45#', re.IGNORECASE),
                (r'6061\s*铝', '6061铝合金', re.IGNORECASE),
                (r's45c', 'S45C', re.IGNORECASE),
                (r'stainless\s*steel', '不锈钢', re.IGNORECASE),
            ],
            'validator': lambda x: x and len(x.strip()) > 0
        },

        # 直径数值规则（清理非数字字符）
        'outer_diameter': {
            'patterns': [
                (r'[φΦØ]\s*(\d+\.?\d*)', r'\1', 0),  # 移除直径符号
                (r'(\d+\.?\d*)\s*mm', r'\1', re.IGNORECASE),  # 移除单位
            ],
            'validator': lambda x: x and re.match(r'^\d+\.?\d*$', str(x))
        },

        # 长度数值规则
        'length': {
            'patterns': [
                (r'(\d+\.?\d*)\s*mm', r'\1', re.IGNORECASE),
                (r'长度?\s*[:：]?\s*(\d+\.?\d*)', r'\1', re.IGNORECASE),
            ],
            'validator': lambda x: x and re.match(r'^\d+\.?\d*$', str(x))
        },

        # 公差规则
        'tolerance': {
            'patterns': [
                (r'[±]\s*(\d+\.?\d*)', r'±\1', 0),
                (r'IT\s*(\d+)', r'IT\1', re.IGNORECASE),
                (r'H\s*(\d+)', r'H\1', re.IGNORECASE),
            ],
            'validator': lambda x: x and (re.match(r'±\d+\.?\d*', str(x)) or re.match(r'IT\d+', str(x), re.IGNORECASE) or re.match(r'H\d+', str(x), re.IGNORECASE))
        },

        # 表面粗糙度规则
        'surface_roughness': {
            'patterns': [
                (r'Ra\s*(\d+\.?\d*)', r'Ra\1', re.IGNORECASE),
                (r'▽\s*(\d+\.?\d*)', r'Ra\1', 0),
            ],
            'validator': lambda x: x and re.match(r'Ra\d+\.?\d*', str(x), re.IGNORECASE)
        },
    }

    def __init__(self, db: Session):
        self.db = db

    def apply_smart_rules(self, ocr_data: Dict) -> Dict:
        """
        应用智能规则对OCR结果进行自动修正

        Args:
            ocr_data: OCR识别的原始数据

        Returns:
            修正后的数据字典
        """
        corrected_data = ocr_data.copy()
        corrections_applied = []

        for field_name, rules in self.SMART_RULES.items():
            if field_name not in corrected_data or not corrected_data[field_name]:
                continue

            original_value = str(corrected_data[field_name])
            corrected_value = original_value

            # 应用正则表达式替换规则
            for pattern, replacement, flags in rules.get('patterns', []):
                corrected_value = re.sub(pattern, replacement, corrected_value, flags=flags)

            # 验证修正后的值
            validator = rules.get('validator')
            if validator and not validator(corrected_value):
                # 验证失败，保持原值
                continue

            # 如果值发生了变化，记录修正
            if corrected_value != original_value:
                corrected_data[field_name] = corrected_value
                corrections_applied.append({
                    'field': field_name,
                    'original': original_value,
                    'corrected': corrected_value,
                    'rule': 'smart_rule'
                })
                logger.info(f"🤖 智能规则修正 [{field_name}]: '{original_value}' → '{corrected_value}'")

        corrected_data['_auto_corrections'] = corrections_applied
        return corrected_data

    def record_correction(
        self,
        drawing_id: int,
        field_name: str,
        ocr_value: Optional[str],
        corrected_value: str
    ) -> OCRCorrection:
        """
        记录人工修正数据

        Args:
            drawing_id: 图纸ID
            field_name: 字段名
            ocr_value: OCR识别的原始值
            corrected_value: 人工修正后的值

        Returns:
            OCRCorrection记录
        """
        # 计算修正类型和相似度
        correction_type, similarity = self._analyze_correction(ocr_value, corrected_value)

        correction = OCRCorrection(
            drawing_id=drawing_id,
            field_name=field_name,
            ocr_value=ocr_value,
            corrected_value=corrected_value,
            correction_type=correction_type,
            similarity_score=similarity
        )

        self.db.add(correction)
        self.db.commit()

        logger.info(f"📝 记录修正: [{field_name}] {ocr_value} → {corrected_value} (类型: {correction_type}, 相似度: {similarity:.2f})")

        # 同步到向量库（方案C）
        try:
            vector_store = _get_vector_store()
            if vector_store:
                vector_store.add_correction(correction)
                logger.info(f"✅ 修正已同步到向量库")
        except Exception as e:
            logger.warning(f"⚠️  向量库同步失败: {e}")

        return correction

    def _analyze_correction(
        self,
        ocr_value: Optional[str],
        corrected_value: str
    ) -> Tuple[str, float]:
        """
        分析修正类型和相似度

        Returns:
            (correction_type, similarity_score)
        """
        if not ocr_value or ocr_value.strip() == '':
            return ('full_error', 0.0)

        # 计算相似度
        similarity = SequenceMatcher(None, str(ocr_value), str(corrected_value)).ratio()

        # 判断修正类型
        if similarity < 0.3:
            return ('full_error', similarity)
        elif similarity < 0.7:
            return ('partial_error', similarity)
        else:
            return ('format_error', similarity)

    def get_correction_stats(
        self,
        field_name: Optional[str] = None,
        limit: int = 100
    ) -> Dict:
        """
        获取修正统计数据

        Args:
            field_name: 可选，指定字段名
            limit: 返回的最大记录数

        Returns:
            统计数据字典
        """
        query = self.db.query(OCRCorrection)

        if field_name:
            query = query.filter(OCRCorrection.field_name == field_name)

        corrections = query.order_by(OCRCorrection.created_at.desc()).limit(limit).all()

        # 统计分析
        total = len(corrections)
        if total == 0:
            return {
                'total': 0,
                'by_field': {},
                'by_type': {},
                'avg_similarity': 0
            }

        by_field = {}
        by_type = {}
        total_similarity = 0

        for correction in corrections:
            # 按字段统计
            if correction.field_name not in by_field:
                by_field[correction.field_name] = 0
            by_field[correction.field_name] += 1

            # 按类型统计
            if correction.correction_type not in by_type:
                by_type[correction.correction_type] = 0
            by_type[correction.correction_type] += 1

            # 累计相似度
            total_similarity += correction.similarity_score or 0

        return {
            'total': total,
            'by_field': by_field,
            'by_type': by_type,
            'avg_similarity': total_similarity / total if total > 0 else 0,
            'recent_corrections': [
                {
                    'field': c.field_name,
                    'ocr_value': c.ocr_value,
                    'corrected_value': c.corrected_value,
                    'type': c.correction_type,
                    'similarity': c.similarity_score,
                    'created_at': c.created_at.isoformat()
                }
                for c in corrections[:20]  # 最近20条
            ]
        }

    def learn_from_corrections(self) -> Dict:
        """
        从修正数据中学习，生成优化建议

        Returns:
            包含学习结果和优化建议的字典
        """
        stats = self.get_correction_stats(limit=500)

        if stats['total'] < 10:
            return {
                'status': 'insufficient_data',
                'message': f'修正数据不足（当前: {stats["total"]}，需要至少10条）',
                'suggestions': []
            }

        suggestions = []

        # 分析高频错误字段
        for field_name, count in stats['by_field'].items():
            if count > stats['total'] * 0.2:  # 占比超过20%
                suggestions.append({
                    'type': 'high_error_field',
                    'field': field_name,
                    'count': count,
                    'suggestion': f'字段 {field_name} 错误率较高，建议优化Prompt中的相关描述'
                })

        # 分析错误类型分布
        full_errors = stats['by_type'].get('full_error', 0)
        if full_errors > stats['total'] * 0.3:  # 完全错误超过30%
            suggestions.append({
                'type': 'high_full_error_rate',
                'count': full_errors,
                'suggestion': 'OCR完全识别错误率较高，建议增强模型的图纸理解能力或调整布局分析'
            })

        # 平均相似度分析
        if stats['avg_similarity'] < 0.5:
            suggestions.append({
                'type': 'low_similarity',
                'avg_similarity': stats['avg_similarity'],
                'suggestion': f'平均相似度较低 ({stats["avg_similarity"]:.2f})，建议全面优化OCR模型'
            })

        return {
            'status': 'success',
            'stats': stats,
            'suggestions': suggestions
        }

    def get_field_patterns(self, field_name: str, min_count: int = 3) -> List[Dict]:
        """
        提取某个字段的常见修正模式

        Args:
            field_name: 字段名
            min_count: 最小出现次数

        Returns:
            模式列表
        """
        corrections = self.db.query(OCRCorrection).filter(
            OCRCorrection.field_name == field_name
        ).all()

        # 统计OCR值到修正值的映射
        pattern_map = {}
        for c in corrections:
            key = (c.ocr_value or '', c.corrected_value or '')
            if key not in pattern_map:
                pattern_map[key] = 0
            pattern_map[key] += 1

        # 过滤出高频模式
        patterns = [
            {
                'ocr_value': ocr_val,
                'corrected_value': corrected_val,
                'count': count
            }
            for (ocr_val, corrected_val), count in pattern_map.items()
            if count >= min_count
        ]

        # 按出现次数降序排序
        patterns.sort(key=lambda x: x['count'], reverse=True)

        return patterns


    def auto_correct_ocr_result(self, ocr_data: Dict, min_count: int = 3) -> Dict:
        """
        自动应用高频修正模式到OCR结果（方案A核心功能）

        原理：
        - 查询历史修正记录
        - 如果某个修正出现超过min_count次，自动应用
        - 返回修正后的数据

        Args:
            ocr_data: OCR识别的原始数据
            min_count: 最小出现次数，默认3次

        Returns:
            修正后的数据字典，包含_auto_corrections列表
        """
        corrected_data = ocr_data.copy()
        auto_corrections = []

        # 获取所有字段的高频修正模式
        field_names = [
            'drawing_number', 'customer_name', 'product_name', 'customer_part_number',
            'material', 'outer_diameter', 'length', 'weight',
            'tolerance', 'surface_roughness', 'heat_treatment', 'surface_treatment'
        ]

        for field_name in field_names:
            original_value = ocr_data.get(field_name)
            if not original_value:
                continue

            # 标准化原始值用于匹配
            original_str = str(original_value).strip().lower()

            # 查询该字段的高频修正模式
            patterns = self.get_field_patterns(field_name, min_count=min_count)

            for pattern in patterns:
                pattern_ocr_value = (pattern.get('ocr_value') or '').strip().lower()

                # 如果OCR值匹配历史模式
                if pattern_ocr_value and pattern_ocr_value == original_str:
                    corrected_value = pattern.get('corrected_value', '')
                    if corrected_value and corrected_value != str(original_value):
                        corrected_data[field_name] = corrected_value
                        auto_corrections.append({
                            'field': field_name,
                            'original': str(original_value),
                            'corrected': corrected_value,
                            'pattern_count': pattern.get('count', 0),
                            'source': 'learned_pattern'
                        })
                        logger.info(f"🤖 自动修正 [{field_name}]: '{original_value}' → '{corrected_value}' (基于{pattern.get('count', 0)}次历史修正)")
                        break  # 每个字段只应用第一个匹配的模式

        # 然后应用智能规则（作为补充）
        smart_corrected = self.apply_smart_rules(corrected_data)

        # 合并智能规则的修正
        if smart_corrected.get('_auto_corrections'):
            auto_corrections.extend(smart_corrected['_auto_corrections'])
            del smart_corrected['_auto_corrections']

        # 方案C：向量检索增强（对未修正的字段尝试向量检索）
        try:
            vector_store = _get_vector_store()
            if vector_store:
                already_corrected_fields = {c['field'] for c in auto_corrections}
                for field_name in field_names:
                    if field_name in already_corrected_fields:
                        continue  # 已经被修正的字段跳过
                    original_value = ocr_data.get(field_name)
                    if not original_value:
                        continue
                    # 向量检索建议
                    suggested = vector_store.get_suggested_correction(
                        field_name=field_name,
                        ocr_value=str(original_value),
                        min_similarity=0.85  # 高阈值，确保准确性
                    )
                    if suggested and suggested != str(original_value):
                        smart_corrected[field_name] = suggested
                        auto_corrections.append({
                            'field': field_name,
                            'original': str(original_value),
                            'corrected': suggested,
                            'source': 'vector_search'
                        })
                        logger.info(f"🔍 向量检索修正 [{field_name}]: '{original_value}' → '{suggested}'")
        except Exception as e:
            logger.warning(f"⚠️  向量检索增强失败: {e}")

        smart_corrected['_auto_corrections'] = auto_corrections
        smart_corrected['_correction_count'] = len(auto_corrections)

        if auto_corrections:
            logger.info(f"✅ 自动修正完成，共修正 {len(auto_corrections)} 个字段")
        else:
            logger.info("✅ 无需自动修正，OCR结果已准确")

        return smart_corrected


def get_ocr_learning_service(db: Session) -> OCRLearningService:
    """获取OCR学习服务实例"""
    return OCRLearningService(db)
