# utils/history_logger.py
# -*- coding: utf-8 -*-
"""
操作历史记录帮助函数

用于在各业务模块中方便地记录操作历史。
"""

from flask import request


def get_operator_info():
    """
    从当前请求中获取操作人信息

    Returns:
        {
            "operator_id": 操作人ID,
            "operator_name": 操作人姓名,
            "operator_role": 操作人角色,
            "ip_address": IP地址
        }
    """
    return {
        "operator_id": getattr(request, 'current_user_id', None),
        "operator_name": getattr(request, 'current_user_name', None),
        "operator_role": getattr(request, 'current_user_role', None),
        "ip_address": request.remote_addr if request else None
    }


def log_pr_operation(
    action: str,
    pr,
    old_status: str = None,
    new_status: str = None,
    extra_data: dict = None,
    description: str = None
):
    """
    记录PR相关操作

    Args:
        action: 操作类型 (create, submit, approve, reject, etc.)
        pr: PR对象
        old_status: 旧状态
        new_status: 新状态
        extra_data: 附加数据
        description: 操作描述
    """
    try:
        from models.operation_history import OperationHistory

        operator = get_operator_info()

        old_value = None
        new_value = None

        if old_status or new_status:
            if old_status:
                old_value = {"status": old_status}
            if new_status:
                new_value = {"status": new_status}

        OperationHistory.log(
            system="caigou",
            module="pr",
            action=action,
            target_type="PR",
            target_id=pr.id,
            target_name=pr.pr_number,
            operator_id=operator["operator_id"],
            operator_name=operator["operator_name"],
            operator_role=operator["operator_role"],
            ip_address=operator["ip_address"],
            old_value=old_value,
            new_value=new_value,
            description=description,
            extra_data=extra_data,
            commit=False  # 让调用者控制事务
        )
    except Exception as e:
        print(f"记录操作历史失败: {str(e)}")


def log_rfq_operation(
    action: str,
    rfq,
    old_status: str = None,
    new_status: str = None,
    extra_data: dict = None,
    description: str = None
):
    """
    记录RFQ相关操作
    """
    try:
        from models.operation_history import OperationHistory

        operator = get_operator_info()

        old_value = None
        new_value = None

        if old_status or new_status:
            if old_status:
                old_value = {"status": old_status}
            if new_status:
                new_value = {"status": new_status}

        OperationHistory.log(
            system="caigou",
            module="rfq",
            action=action,
            target_type="RFQ",
            target_id=rfq.id if hasattr(rfq, 'id') else None,
            target_name=rfq.rfq_number if hasattr(rfq, 'rfq_number') else None,
            operator_id=operator["operator_id"],
            operator_name=operator["operator_name"],
            operator_role=operator["operator_role"],
            ip_address=operator["ip_address"],
            old_value=old_value,
            new_value=new_value,
            description=description,
            extra_data=extra_data,
            commit=False
        )
    except Exception as e:
        print(f"记录操作历史失败: {str(e)}")


def log_supplier_operation(
    action: str,
    supplier,
    old_data: dict = None,
    new_data: dict = None,
    extra_data: dict = None,
    description: str = None
):
    """
    记录供应商相关操作
    """
    try:
        from models.operation_history import OperationHistory

        operator = get_operator_info()

        OperationHistory.log(
            system="caigou",
            module="supplier",
            action=action,
            target_type="Supplier",
            target_id=supplier.id if hasattr(supplier, 'id') else None,
            target_name=supplier.name if hasattr(supplier, 'name') else None,
            operator_id=operator["operator_id"],
            operator_name=operator["operator_name"],
            operator_role=operator["operator_role"],
            ip_address=operator["ip_address"],
            old_value=old_data,
            new_value=new_data,
            description=description,
            extra_data=extra_data,
            commit=False
        )
    except Exception as e:
        print(f"记录操作历史失败: {str(e)}")


def log_generic_operation(
    system: str,
    module: str,
    action: str,
    target_type: str = None,
    target_id=None,
    target_name: str = None,
    old_value=None,
    new_value=None,
    extra_data: dict = None,
    description: str = None
):
    """
    通用操作记录函数
    """
    try:
        from models.operation_history import OperationHistory

        operator = get_operator_info()

        OperationHistory.log(
            system=system,
            module=module,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            operator_id=operator["operator_id"],
            operator_name=operator["operator_name"],
            operator_role=operator["operator_role"],
            ip_address=operator["ip_address"],
            old_value=old_value,
            new_value=new_value,
            description=description,
            extra_data=extra_data,
            commit=False
        )
    except Exception as e:
        print(f"记录操作历史失败: {str(e)}")
