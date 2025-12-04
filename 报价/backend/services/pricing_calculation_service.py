# services/pricing_calculation_service.py
"""
报价计算服务 - 基于创怡兴报价公式
实现完整的制造成本计算逻辑
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from models.quote import Quote, QuoteProcess
from models.process_cost import ProcessCost
from decimal import Decimal
import math
import logging

logger = logging.getLogger(__name__)


class PricingCalculationService:
    """报价计算服务 - 创怡兴公式实现"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_material_cost(self, quote_data: Dict) -> Dict:
        """
        计算材料费 (B.材料費)

        公式：重量 E = PI × (外径)²/4 × 材料长度 ÷ 取数 × 比重
        材料费 B = 重量 E × 材料单价 × 总不良率 × 材管率 ÷ 1000

        Returns:
            包含 part_weight, pieces_per_bar, material_cost 的字典
        """
        try:
            # 提取参数
            outer_diameter = float(quote_data.get('outer_diameter', 0))  # mm
            material_length = float(quote_data.get('material_length', 2500))  # mm
            product_length = float(quote_data.get('product_length', 0))  # mm
            cut_width = float(quote_data.get('cut_width', 2.5))  # mm
            remaining_material = float(quote_data.get('remaining_material', 160))  # mm
            material_density = float(quote_data.get('material_density', 0.0079))  # g/cm³
            material_price_per_kg = float(quote_data.get('material_price_per_kg', 26))  # 元/kg
            total_defect_rate = float(quote_data.get('total_defect_rate', 0.0306))  # 总不良率
            material_management_rate = float(quote_data.get('material_management_rate', 1.03))  # 材管率

            # 计算取数（每根材料可切数量）
            # 取数 = Int[(材料长度 - 残材) / (产品长度 + 切口)]
            if product_length > 0:
                pieces_per_bar = int((material_length - remaining_material) / (product_length + cut_width))
            else:
                pieces_per_bar = 1

            if pieces_per_bar <= 0:
                pieces_per_bar = 1

            # 计算零件重量 E（g）
            # 重量 E = PI × (外径)²/4 × 材料长度 ÷ 取数 × 比重
            part_weight = (
                math.pi *
                (outer_diameter ** 2) / 4 *
                material_length / pieces_per_bar *
                material_density
            )

            # 计算材料费 B
            # B = 重量 E × 材料单价 × 总不良率 × 材管率 ÷ 1000
            material_cost = (
                part_weight *
                material_price_per_kg *
                total_defect_rate *
                material_management_rate /
                1000
            )

            logger.info(f"✅ 材料费计算完成: B = {material_cost:.4f} 元")
            logger.info(f"   零件重量: {part_weight:.2f}g, 取数: {pieces_per_bar}")

            return {
                'part_weight': round(part_weight, 2),
                'pieces_per_bar': pieces_per_bar,
                'material_cost': round(material_cost, 4)
            }

        except Exception as e:
            logger.error(f"❌ 材料费计算失败: {e}")
            return {
                'part_weight': 0,
                'pieces_per_bar': 1,
                'material_cost': 0
            }

    def calculate_process_cost(
        self,
        lot_size: int,
        processes: List[Dict],
        total_defect_rate: float = 0.0306
    ) -> tuple[float, List[Dict]]:
        """
        计算加工费 (C.加工費)

        公式：加工小費 = ((加工個数 ÷ 日産 + 段取時間) × 工事費／日) ÷ LOT
        其中：加工個数 = LOT × (1 + 不良率)

        Args:
            lot_size: 批量
            processes: 工序列表，每个工序包含：
                - process_name: 工序名称
                - defect_rate: 不良率
                - daily_production: 日産
                - setup_time: 段取时间（天）
                - engineering_cost_per_day: 工事费/日
                - unit_price: （可选）单价，用于电镀等按件计费
                - box_processing_time: （可选）箱处理时间（小时）
                - hourly_rate: （可选）工事费/时
                - box_quantity: （可选）箱入数

        Returns:
            (总加工费, 详细工序成本列表)
        """
        total_process_cost = 0.0
        process_details = []

        logger.info(f"📋 开始计算加工费: LOT={lot_size}, 总不良率={total_defect_rate}")

        for idx, process in enumerate(processes, 1):
            try:
                process_name = process.get('process_name', f'工序{idx}')
                defect_rate = float(process.get('defect_rate', 0))

                # 计算加工個数（含不良）
                # 加工個数 = LOT × (1 + 不良率)
                processing_quantity = lot_size * (1 + defect_rate)

                # 判断计费方式
                if process.get('unit_price'):
                    # 按件计费（如电镀费）
                    unit_price = float(process['unit_price'])
                    process_cost = unit_price * processing_quantity / lot_size
                    process_details.append({
                        'process_name': process_name,
                        'defect_rate': defect_rate,
                        'processing_quantity': processing_quantity,
                        'unit_price': unit_price,
                        'process_cost': round(process_cost, 4),
                        'calculation_method': 'unit_price'
                    })
                    logger.info(f"  [{idx}] {process_name}: 单价={unit_price} × {processing_quantity}/{lot_size} = {process_cost:.4f}")

                elif process.get('box_processing_time'):
                    # 按时间计费（如包装费）
                    box_time = float(process['box_processing_time'])  # 小时
                    hourly_rate = float(process.get('hourly_rate', 8))  # 元/小时
                    box_quantity = int(process.get('box_quantity', 2000))  # 箱入数
                    # 包装费 = 箱处理时间 × 工事费/时 ÷ 箱入数
                    process_cost = box_time * hourly_rate / box_quantity
                    process_details.append({
                        'process_name': process_name,
                        'box_processing_time': box_time,
                        'hourly_rate': hourly_rate,
                        'box_quantity': box_quantity,
                        'process_cost': round(process_cost, 4),
                        'calculation_method': 'hourly'
                    })
                    logger.info(f"  [{idx}] {process_name}: ({box_time}小时 × {hourly_rate}元/时) ÷ {box_quantity}件 = {process_cost:.4f}")

                else:
                    # 标准工序计费
                    daily_production = float(process.get('daily_production', 2000))
                    setup_time = float(process.get('setup_time', 0))
                    engineering_cost_per_day = float(process.get('engineering_cost_per_day', 300))

                    # 计算加工日数
                    # 加工日数 = 加工個数 ÷ 日産
                    processing_days = processing_quantity / daily_production if daily_production > 0 else 0

                    # 计算工序成本
                    # 加工小費 = ((加工日数 + 段取时间) × 工事费/日) ÷ LOT
                    process_cost = ((processing_days + setup_time) * engineering_cost_per_day) / lot_size

                    process_details.append({
                        'process_name': process_name,
                        'defect_rate': defect_rate,
                        'processing_quantity': processing_quantity,
                        'daily_production': daily_production,
                        'processing_days': round(processing_days, 6),
                        'setup_time': setup_time,
                        'engineering_cost_per_day': engineering_cost_per_day,
                        'lot_size': lot_size,
                        'process_cost': round(process_cost, 4),
                        'calculation_method': 'standard'
                    })
                    logger.info(f"  [{idx}] {process_name}: (({processing_days:.4f}天 + {setup_time}天) × {engineering_cost_per_day}元/天) ÷ {lot_size} = {process_cost:.4f}")

                total_process_cost += process_cost

            except Exception as e:
                logger.error(f"❌ 工序 {process_name} 计算失败: {e}")
                continue

        logger.info(f"✅ 加工费计算完成: C = {total_process_cost:.4f} 元 (共{len(process_details)}道工序)")

        return round(total_process_cost, 4), process_details

    def calculate_management_cost(
        self,
        process_cost: float,
        general_management_rate: float = 0.10,
        transportation_cost: float = 0.0
    ) -> Dict:
        """
        计算管理费 (D.管理費)

        公式：D.管理费 = 一般管理费(C × 管理费率) + H.运送费

        Args:
            process_cost: C.加工费
            general_management_rate: 一般管理费率（默认10%）
            transportation_cost: H.运送费

        Returns:
            包含 general_management_fee, management_cost 的字典
        """
        # 一般管理费 = C × 管理费率
        general_management_fee = process_cost * general_management_rate

        # D.管理费 = 一般管理费 + 运送费
        management_cost = general_management_fee + transportation_cost

        logger.info(f"✅ 管理费计算完成: D = {management_cost:.4f} 元")
        logger.info(f"   一般管理费: {general_management_fee:.4f}, 运送费: {transportation_cost:.4f}")

        return {
            'general_management_fee': round(general_management_fee, 4),
            'transportation_cost': round(transportation_cost, 4),
            'management_cost': round(management_cost, 4)
        }

    def calculate_other_cost(
        self,
        packaging_material_cost: float = 0.0,
        consumables_cost: float = 0.0
    ) -> float:
        """
        计算其他费用 (F.其他費用)

        公式：F.其他费用 = 梱包材料费 + 消耗品费用

        Args:
            packaging_material_cost: 梱包材料费
            consumables_cost: 消耗品费用

        Returns:
            其他费用总计
        """
        other_cost = packaging_material_cost + consumables_cost

        logger.info(f"✅ 其他费用计算完成: F = {other_cost:.4f} 元")
        logger.info(f"   梱包材料费: {packaging_material_cost:.4f}, 消耗品费: {consumables_cost:.4f}")

        return round(other_cost, 4)

    def calculate_full_quote(self, quote_data: Dict) -> Dict:
        """
        执行完整的报价计算

        根据创怡兴报价公式计算所有成本项和最终单价：
        - B.材料费
        - C.加工费
        - D.管理费
        - F.其他费用
        - A.小计単価 = B + C + D + F
        - M.利润 = A × 利润率
        - N.零件単价总计 = B + C + D + F + M

        Args:
            quote_data: 包含所有必要参数的字典

        Returns:
            完整的计算结果字典
        """
        logger.info("=" * 80)
        logger.info("🚀 开始完整报价计算 - 创怡兴公式")
        logger.info("=" * 80)

        # 1. 计算材料费 (B)
        material_result = self.calculate_material_cost(quote_data)
        material_cost = material_result['material_cost']

        # 2. 计算加工费 (C)
        lot_size = int(quote_data.get('lot_size', 2000))
        processes = quote_data.get('processes', [])
        total_defect_rate = float(quote_data.get('total_defect_rate', 0.0306))
        process_cost, process_details = self.calculate_process_cost(
            lot_size, processes, total_defect_rate
        )

        # 3. 计算管理费 (D)
        general_management_rate = float(quote_data.get('general_management_rate', 0.10))
        transportation_cost = float(quote_data.get('transportation_cost', 0.0))
        management_result = self.calculate_management_cost(
            process_cost, general_management_rate, transportation_cost
        )
        management_cost = management_result['management_cost']

        # 4. 计算其他费用 (F)
        packaging_material_cost = float(quote_data.get('packaging_material_cost', 0.0))
        consumables_cost = float(quote_data.get('consumables_cost', 0.0))
        other_cost = self.calculate_other_cost(packaging_material_cost, consumables_cost)

        # 5. 计算小计単价 (A)
        subtotal_cost = material_cost + process_cost + management_cost + other_cost

        # 6. 计算利润 (M)
        profit_rate = float(quote_data.get('profit_rate', 0.15))
        profit_amount = subtotal_cost * profit_rate

        # 7. 计算零件単价总计 (N)
        unit_price = material_cost + process_cost + management_cost + other_cost + profit_amount
        # N = B + C + D + F + M

        # 8. 计算总价
        total_amount = unit_price * lot_size

        logger.info("=" * 80)
        logger.info("📊 报价计算汇总")
        logger.info("=" * 80)
        logger.info(f"B. 材料费:        {material_cost:.4f} 元")
        logger.info(f"C. 加工费:        {process_cost:.4f} 元 ({len(process_details)}道工序)")
        logger.info(f"D. 管理费:        {management_cost:.4f} 元")
        logger.info(f"F. 其他费用:      {other_cost:.4f} 元")
        logger.info(f"─" * 80)
        logger.info(f"A. 小计单价:      {subtotal_cost:.4f} 元 (B+C+D+F)")
        logger.info(f"M. 利润({profit_rate*100}%):    {profit_amount:.4f} 元")
        logger.info(f"═" * 80)
        logger.info(f"N. 零件单价总计:  {unit_price:.4f} 元")
        logger.info(f"批量(LOT):       {lot_size} 件")
        logger.info(f"总价:            {total_amount:.2f} 元")
        logger.info("=" * 80)

        return {
            # 材料费
            'material_cost': material_cost,
            'part_weight': material_result['part_weight'],
            'pieces_per_bar': material_result['pieces_per_bar'],

            # 加工费
            'process_cost': process_cost,
            'process_details': process_details,

            # 管理费
            'management_cost': management_cost,
            'general_management_fee': management_result['general_management_fee'],
            'transportation_cost': transportation_cost,

            # 其他费用
            'other_cost': other_cost,
            'packaging_material_cost': packaging_material_cost,
            'consumables_cost': consumables_cost,

            # 成本汇总
            'subtotal_cost': round(subtotal_cost, 4),
            'profit_rate': profit_rate,
            'profit_amount': round(profit_amount, 4),
            'unit_price': round(unit_price, 4),
            'lot_size': lot_size,
            'total_amount': round(total_amount, 2),

            # 计算成功标志
            'success': True
        }


def get_pricing_service(db: Session) -> PricingCalculationService:
    """获取报价计算服务实例"""
    return PricingCalculationService(db)
