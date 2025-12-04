# utils/code_generator.py
# -*- coding: utf-8 -*-
"""
编码生成工具模块
支持多种业务实体的自动编码生成
"""

from datetime import datetime


class CodeGenerator:
    """编码生成器 - 集中管理所有编码生成逻辑"""

    @staticmethod
    def generate_supplier_code(supplier_id):
        """
        生成供应商编码
        格式: SUP + 6位ID（如：SUP000001）
        
        Args:
            supplier_id (int): 供应商数据库ID
            
        Returns:
            str: 供应商编码，若ID无效则返回None
        """
        if not supplier_id:
            return None
        return f"SUP{supplier_id:06d}"

    @staticmethod
    def generate_user_code(user_id):
        """
        生成用户编码
        格式: USR + 6位ID（如：USR000001）
        
        Args:
            user_id (int): 用户数据库ID
            
        Returns:
            str: 用户编码，若ID无效则返回None
        """
        if not user_id:
            return None
        return f"USR{user_id:06d}"

    @staticmethod
    def generate_order_code():
        """
        生成订单编码
        格式: ORD + 时间戳（如：ORD20240101120000）
        
        Returns:
            str: 订单编码
        """
        return f"ORD{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    @staticmethod
    def generate_pr_code(pr_id):
        """
        生成采购需求（PR）编码
        格式: PR + 8位ID（如：PR00000001）
        
        Args:
            pr_id (int): PR数据库ID
            
        Returns:
            str: PR编码，若ID无效则返回None
        """
        if not pr_id:
            return None
        return f"PR{pr_id:08d}"

    @staticmethod
    def generate_po_code():
        """
        生成采购订单（PO）编码
        格式: PO + 日期 + 时间秒（如：PO202401011200）
        
        Returns:
            str: PO编码
        """
        now = datetime.utcnow()
        return f"PO{now.strftime('%Y%m%d%H%M')}"

    @staticmethod
    def validate_code(code, code_type):
        """
        验证编码格式是否正确
        
        Args:
            code (str): 编码字符串
            code_type (str): 编码类型（supplier/user/pr/order/po）
            
        Returns:
            bool: 格式是否正确
        """
        if not code or not isinstance(code, str):
            return False
        
        patterns = {
            'supplier': r'^SUP\d{6}$',
            'user': r'^USR\d{6}$',
            'pr': r'^PR\d{8}$',
            'order': r'^ORD\d{14}$',
            'po': r'^PO\d{12}$',
        }
        
        if code_type not in patterns:
            return False
        
        import re
        return bool(re.match(patterns[code_type], code))