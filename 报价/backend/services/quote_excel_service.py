# services/quote_excel_service.py
"""
报价单Excel导出服务
"""
import xlrd
from xlwt import Workbook, XFStyle, Font, Alignment, Borders, Pattern
from xlutils.copy import copy as xl_copy
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class QuoteExcelService:
    """报价单Excel导出服务"""

    def __init__(self):
        self.template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'templates',
            'quote_template.xls'
        )

    def export_quote(
        self,
        quote_data: Dict,
        items: List[Dict],
        output_path: str
    ) -> str:
        """
        导出报价单到Excel

        Args:
            quote_data: 报价单主数据
            items: 报价项目列表
            output_path: 输出文件路径

        Returns:
            生成的文件路径
        """
        try:
            # 读取模板
            template_wb = xlrd.open_workbook(self.template_path, formatting_info=True)
            # 复制工作簿
            new_wb = xl_copy(template_wb)

            # 获取"精之成报价单"工作表
            sheet = new_wb.get_sheet('精之成报价单')

            # 填充头部信息
            self._fill_header(sheet, quote_data)

            # 填充产品明细
            self._fill_items(sheet, items)

            # 保存文件
            new_wb.save(output_path)

            logger.info(f"✅ Excel报价单已生成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"❌ Excel导出失败: {str(e)}")
            raise

    def _fill_header(self, sheet, quote_data: Dict):
        """填充表头信息"""
        try:
            # 客户名称（行5，列0）
            customer_name = quote_data.get('customer_name', '深圳市晨龙精密五金制品有限公司')
            sheet.write(5, 0, f'TO：{customer_name}')

            # 日期（行5，列7）
            date_str = quote_data.get('quote_date', datetime.now().strftime('%Y-%m-%d'))
            sheet.write(5, 7, f'日期：{date_str}')

            # 联系人（行6，列0）
            contact_person = quote_data.get('contact_person', '郭先生')
            sheet.write(6, 0, f'ATTN：{contact_person}')

            # 电话（行6，列7）
            phone = quote_data.get('phone', '')
            sheet.write(6, 7, f'电话：{phone}')

            # 报价单号（行7，列0）
            quote_number = quote_data.get('quote_number', datetime.now().strftime('%y%m%d'))
            sheet.write(7, 0, f'报价单号：{quote_number}')

            # 传真（行7，列7）
            fax = quote_data.get('fax', '')
            sheet.write(7, 7, f'传真：{fax}')

        except Exception as e:
            logger.error(f"❌ 填充表头失败: {str(e)}")
            raise

    def _fill_items(self, sheet, items: List[Dict]):
        """填充产品明细"""
        try:
            # 数据从第10行开始（索引10）
            start_row = 10

            for idx, item in enumerate(items):
                row_idx = start_row + idx

                # 序号（列0）
                sheet.write(row_idx, 0, f'{idx + 1}.0')

                # 部品番号/客户料号（列1）
                part_number = item.get('customer_part_number', item.get('drawing_number', ''))
                sheet.write(row_idx, 1, part_number)

                # 直径（列2）
                outer_diameter = item.get('outer_diameter', '')
                if outer_diameter:
                    try:
                        diameter_value = float(outer_diameter)
                        sheet.write(row_idx, 2, diameter_value)
                    except (ValueError, TypeError):
                        sheet.write(row_idx, 2, outer_diameter)

                # 长度（列3）
                length = item.get('length', '')
                if length:
                    try:
                        length_value = float(length)
                        sheet.write(row_idx, 3, length_value)
                    except (ValueError, TypeError):
                        sheet.write(row_idx, 3, length)

                # 材质（列4）
                material = item.get('material', '')
                sheet.write(row_idx, 4, material)

                # 处理/表面处理（列5）
                surface_treatment = item.get('surface_treatment', '')
                sheet.write(row_idx, 5, surface_treatment)

                # MOQ/批量（列6）
                moq = item.get('lot_size', item.get('quantity', ''))
                if moq:
                    try:
                        moq_value = float(moq)
                        sheet.write(row_idx, 6, moq_value)
                    except (ValueError, TypeError):
                        sheet.write(row_idx, 6, moq)

                # 未税单价（列7）
                unit_price_before_tax = item.get('unit_price_before_tax', '')
                if unit_price_before_tax:
                    try:
                        price = float(unit_price_before_tax)
                        sheet.write(row_idx, 7, price)
                    except (ValueError, TypeError):
                        sheet.write(row_idx, 7, unit_price_before_tax)

                # 含税单价（列8）
                unit_price_with_tax = item.get('unit_price_with_tax', '')
                if not unit_price_with_tax and unit_price_before_tax:
                    # 如果没有含税价，自动计算（13%税率）
                    try:
                        price = float(unit_price_before_tax)
                        unit_price_with_tax = round(price * 1.13, 4)
                    except (ValueError, TypeError):
                        unit_price_with_tax = ''

                if unit_price_with_tax:
                    try:
                        price = float(unit_price_with_tax)
                        sheet.write(row_idx, 8, price)
                    except (ValueError, TypeError):
                        sheet.write(row_idx, 8, unit_price_with_tax)

                # 备注（列9）
                notes = item.get('notes', '')
                if notes:
                    sheet.write(row_idx, 9, notes)

            # 如果产品少于12个，在剩余行写入序号
            total_rows = 12  # 模板有12行产品区域
            for idx in range(len(items), total_rows):
                row_idx = start_row + idx
                sheet.write(row_idx, 0, f'{idx + 1}.0')

        except Exception as e:
            logger.error(f"❌ 填充产品明细失败: {str(e)}")
            raise


# 单例模式
_quote_excel_service = None


def get_quote_excel_service() -> QuoteExcelService:
    """获取报价单Excel服务实例"""
    global _quote_excel_service
    if _quote_excel_service is None:
        _quote_excel_service = QuoteExcelService()
    return _quote_excel_service
