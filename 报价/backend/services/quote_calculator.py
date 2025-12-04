# services/quote_calculator.py
"""
报价计算引擎
基于创怡兴tab的Excel公式
"""
import math
import logging
from typing import Dict, List, Optional
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


class QuoteCalculator:
    """报价计算器"""

    def __init__(self):
        # 默认参数（可配置）
        self.default_management_rate = 0.045  # 管理费率 4.5%
        self.default_profit_rate = 0.15       # 利润率 15%
        self.default_defect_rate = 0.03061    # 总不良率 3.061%
        self.default_material_mgmt_rate = 0.03  # 材管率 3%

    def calculate_material_cost(
        self,
        outer_diameter: float,  # 外径 mm
        material_length: float,  # 材料长度 mm
        parts_per_material: int,  # 取数（一根材料能出几个零件）
        density: float,  # 密度 g/cm³
        price_per_kg: float,  # 材料单价 元/kg
        defect_rate: Optional[float] = None,  # 不良率
        material_mgmt_rate: Optional[float] = None  # 材管率
    ) -> Dict:
        """
        计算材料成本

        公式：
        重量(E) = π × (外径²/4) × 材料长度 ÷ 取数 × 比重
        材料费(B) = 重量(E) × 材料单价 × (1 + 总不良率) × (1 + 材管率)

        Args:
            outer_diameter: 外径 (mm)
            material_length: 材料长度 (mm)
            parts_per_material: 取数
            density: 密度 (g/cm³)
            price_per_kg: 材料单价 (元/kg)
            defect_rate: 不良率
            material_mgmt_rate: 材管率

        Returns:
            {
                "weight_per_piece": 单件重量(g),
                "material_cost_per_piece": 单件材料费(元),
                "details": 计算明细
            }
        """
        if defect_rate is None:
            defect_rate = self.default_defect_rate
        if material_mgmt_rate is None:
            material_mgmt_rate = self.default_material_mgmt_rate

        try:
            # 计算重量 (g)
            # π × (外径²/4) × 材料长度 ÷ 取数 × 比重
            # 单位转换: mm³ -> cm³ (除以1000)
            volume_cm3 = (
                math.pi * (outer_diameter ** 2 / 4) * material_length / parts_per_material / 1000
            )
            weight_g = volume_cm3 * density

            # 计算材料费
            weight_kg = weight_g / 1000
            base_material_cost = weight_kg * price_per_kg
            material_cost = base_material_cost * (1 + defect_rate) * (1 + material_mgmt_rate)

            logger.info(f"材料成本计算: 重量={weight_g:.2f}g, 单价={price_per_kg}元/kg, 成本={material_cost:.4f}元")

            return {
                "weight_per_piece": round(weight_g, 4),
                "material_cost_per_piece": round(material_cost, 4),
                "details": {
                    "volume_cm3": round(volume_cm3, 4),
                    "weight_kg": round(weight_kg, 6),
                    "base_cost": round(base_material_cost, 4),
                    "defect_rate": defect_rate,
                    "material_mgmt_rate": material_mgmt_rate
                }
            }

        except Exception as e:
            logger.error(f"材料成本计算失败: {e}")
            raise ValueError(f"材料成本计算失败: {e}")

    def calculate_process_cost(
        self,
        processes: List[Dict],  # 工艺列表
        lot_size: int = 2000,    # LOT大小（批量）
    ) -> Dict:
        """
        计算加工成本

        公式：
        工序加工费 = [(加工个数 ÷ 日产 + 段取时间) × 工事费/日] ÷ LOT

        Args:
            processes: 工艺列表，每项包含:
                - process_name: 工艺名称
                - daily_output: 日产量（件）
                - setup_time: 段取时间（小时）
                - hourly_rate: 工时费率（元/小时）
                - defect_rate: 不良率
            lot_size: LOT大小

        Returns:
            {
                "total_process_cost": 总加工成本(元),
                "process_details": 各工序明细,
                "total_time": 总加工时间(小时)
            }
        """
        try:
            total_cost = 0
            process_details = []
            total_time = 0

            for idx, process in enumerate(processes, 1):
                process_name = process.get('process_name', f'工序{idx}')
                daily_output = process.get('daily_output', 1000)
                setup_time = process.get('setup_time', 0.125)  # 小时
                hourly_rate = process.get('hourly_rate', 55)   # 元/小时
                defect_rate = process.get('defect_rate', 0)

                # 考虑不良率后的加工个数
                adjusted_lot = lot_size * (1 + defect_rate)

                # 加工天数 = 加工个数 ÷ 日产
                if daily_output > 0:
                    processing_days = adjusted_lot / daily_output
                else:
                    processing_days = 0

                # 总时间（天） = 加工天数 + 段取时间（转换为天）
                # 假设每天工作8小时
                total_days = processing_days + (setup_time / 8)

                # 工序成本 = 总时间(天) × 日工时费 ÷ LOT
                # 日工时费 = 小时费率 × 8小时
                daily_cost = hourly_rate * 8
                process_cost = (total_days * daily_cost) / lot_size

                total_cost += process_cost
                total_time += processing_days * 8 + setup_time

                process_details.append({
                    "sequence": idx,
                    "process_name": process_name,
                    "daily_output": daily_output,
                    "processing_days": round(processing_days, 4),
                    "setup_time_hours": setup_time,
                    "hourly_rate": hourly_rate,
                    "process_cost": round(process_cost, 4),
                    "defect_rate": defect_rate
                })

                logger.info(f"工序{idx} {process_name}: 成本={process_cost:.4f}元")

            logger.info(f"加工成本合计: {total_cost:.4f}元")

            return {
                "total_process_cost": round(total_cost, 4),
                "process_details": process_details,
                "total_time_hours": round(total_time, 2)
            }

        except Exception as e:
            logger.error(f"加工成本计算失败: {e}")
            raise ValueError(f"加工成本计算失败: {e}")

    def calculate_other_costs(
        self,
        packaging_cost: float = 0.158,  # 梱包材料
        consumables_cost: float = 0.006,  # 消耗品
        plating_cost: float = 0,  # 电镀费
        other_items: Optional[List[Dict]] = None
    ) -> Dict:
        """
        计算其他费用

        Args:
            packaging_cost: 包装材料费
            consumables_cost: 消耗品费
            plating_cost: 电镀费
            other_items: 其他费用项目

        Returns:
            {
                "total_other_cost": 总其他费用,
                "items": 费用明细
            }
        """
        items = [
            {"name": "梱包材料", "cost": packaging_cost},
            {"name": "消耗品", "cost": consumables_cost},
        ]

        if plating_cost > 0:
            items.append({"name": "电镀费", "cost": plating_cost})

        if other_items:
            items.extend(other_items)

        total = sum(item['cost'] for item in items)

        return {
            "total_other_cost": round(total, 4),
            "items": items
        }

    def calculate_quote(
        self,
        material_cost: float,
        process_cost: float,
        other_cost: float = 0,
        management_rate: Optional[float] = None,
        profit_rate: Optional[float] = None
    ) -> Dict:
        """
        计算总报价

        公式：
        A = 小计单价 = B(材料费) + C(加工费) + D(管理费) + F(其他费用)
        D = 管理费 = A × 管理费率 (需要迭代计算)
        M = 利润 = A × 利润率
        N = 总单价 = A + M = B + C + D + F + M

        Args:
            material_cost: 材料成本
            process_cost: 加工成本
            other_cost: 其他费用
            management_rate: 管理费率
            profit_rate: 利润率

        Returns:
            完整报价明细
        """
        if management_rate is None:
            management_rate = self.default_management_rate
        if profit_rate is None:
            profit_rate = self.default_profit_rate

        try:
            # 计算小计单价 A = (B + C + F) / (1 - 管理费率)
            # 因为 D = A × 管理费率，所以 A = B + C + F + D = B + C + F + A × 管理费率
            # 解得：A × (1 - 管理费率) = B + C + F
            base_cost = material_cost + process_cost + other_cost
            subtotal = base_cost / (1 - management_rate)

            # 管理费
            management_cost = subtotal * management_rate

            # 利润
            profit = subtotal * profit_rate

            # 总单价
            total_price = subtotal + profit

            logger.info(f"报价计算完成: 材料={material_cost:.2f}, 加工={process_cost:.2f}, "
                       f"管理={management_cost:.2f}, 利润={profit:.2f}, 总价={total_price:.2f}")

            return {
                "material_cost": round(material_cost, 4),
                "process_cost": round(process_cost, 4),
                "other_cost": round(other_cost, 4),
                "management_cost": round(management_cost, 4),
                "subtotal": round(subtotal, 4),
                "profit": round(profit, 4),
                "total_price": round(total_price, 4),
                "rates": {
                    "management_rate": management_rate,
                    "profit_rate": profit_rate
                }
            }

        except Exception as e:
            logger.error(f"总报价计算失败: {e}")
            raise ValueError(f"总报价计算失败: {e}")

    def calculate_full_quote(
        self,
        drawing_info: Dict,
        material_info: Dict,
        processes: List[Dict],
        lot_size: int = 2000,
        **kwargs
    ) -> Dict:
        """
        一键计算完整报价

        Args:
            drawing_info: 图纸信息 (外径、长度等)
            material_info: 材料信息 (密度、单价等)
            processes: 工艺列表
            lot_size: 批量
            **kwargs: 其他参数

        Returns:
            完整报价结果
        """
        try:
            # 1. 解析图纸信息
            outer_diameter = self._parse_dimension(drawing_info.get('outer_diameter', '6'))
            length = self._parse_dimension(drawing_info.get('length', '100'))

            # 2. 计算材料成本
            material_result = self.calculate_material_cost(
                outer_diameter=outer_diameter,
                material_length=length,
                parts_per_material=kwargs.get('parts_per_material', 1),
                density=material_info.get('density', 7.93),
                price_per_kg=material_info.get('price_per_kg', 35.0),
                defect_rate=kwargs.get('defect_rate'),
                material_mgmt_rate=kwargs.get('material_mgmt_rate')
            )

            # 3. 计算加工成本
            process_result = self.calculate_process_cost(
                processes=processes,
                lot_size=lot_size
            )

            # 4. 计算其他费用
            other_result = self.calculate_other_costs(
                packaging_cost=kwargs.get('packaging_cost', 0.158),
                consumables_cost=kwargs.get('consumables_cost', 0.006),
                plating_cost=kwargs.get('plating_cost', 0),
                other_items=kwargs.get('other_items')
            )

            # 5. 计算总报价
            quote_result = self.calculate_quote(
                material_cost=material_result['material_cost_per_piece'],
                process_cost=process_result['total_process_cost'],
                other_cost=other_result['total_other_cost'],
                management_rate=kwargs.get('management_rate'),
                profit_rate=kwargs.get('profit_rate')
            )

            # 6. 组合结果
            return {
                "success": True,
                "quote": quote_result,
                "material": material_result,
                "process": process_result,
                "other": other_result,
                "lot_size": lot_size,
                "drawing_info": {
                    "outer_diameter": outer_diameter,
                    "length": length,
                    "drawing_number": drawing_info.get('drawing_number', ''),
                    "material": drawing_info.get('material', '')
                }
            }

        except Exception as e:
            logger.error(f"完整报价计算失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _parse_dimension(self, dimension_str: str) -> float:
        """
        解析尺寸字符串

        例如: "φ6.05" -> 6.05, "240.4" -> 240.4, "101.80.10" -> 101.8010
        """
        import re

        # 移除特殊字符
        cleaned = re.sub(r'[φΦ±]', '', str(dimension_str))
        cleaned = cleaned.strip()

        # 移除所有非数字、小数点、负号的字符
        cleaned = re.sub(r'[^\d.\-]', '', cleaned)

        # 处理多个小数点：只保留第一个
        parts = cleaned.split('.')
        if len(parts) > 2:
            # 重新组装：第一部分 + '.' + 其余部分拼接（去掉小数点）
            cleaned = parts[0] + '.' + ''.join(parts[1:])

        # 提取数字（匹配整数或小数）
        match = re.search(r'-?\d+\.?\d*', cleaned)
        if match:
            try:
                return float(match.group())
            except ValueError:
                logger.warning(f"无法转换为浮点数: {dimension_str} -> {match.group()}，使用默认值1.0")
                return 1.0
        else:
            raise ValueError(f"无法解析尺寸: {dimension_str}")


# 全局单例
_calculator = None


def get_calculator() -> QuoteCalculator:
    """获取计算器单例"""
    global _calculator
    if _calculator is None:
        _calculator = QuoteCalculator()
    return _calculator
