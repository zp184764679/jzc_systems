import logging
import sys
import os
from datetime import datetime

# 添加 shared 模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.http_client import get_with_retry, post_with_retry, RETRYABLE_EXCEPTIONS
from config import Config

# 配置库存操作日志 - 用于跟踪跨系统事务
logger = logging.getLogger('scm_inventory')
logger.setLevel(logging.INFO)

# 确保日志处理器存在
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] [SHM-SCM] %(levelname)s: %(message)s'
    ))
    logger.addHandler(handler)


def deduct_inventory(product_code, qty, shipment_no):
    """
    调用SCM系统扣减库存

    警告：此操作无法自动回滚！
    如果 SHM 后续操作失败，需要手动在 SCM 中恢复库存。

    Args:
        product_code: 产品编码
        qty: 扣减数量
        shipment_no: 出货单号

    Returns:
        dict: SCM系统返回结果
    """
    timestamp = datetime.now().isoformat()

    # 记录扣减请求 - 重要：用于故障排查和数据恢复
    logger.warning(
        f"[库存扣减开始] shipment_no={shipment_no}, "
        f"product_code={product_code}, qty={qty}, timestamp={timestamp}"
    )

    try:
        # P2-18: 使用带重试的 HTTP 客户端
        response = post_with_retry(
            f"{Config.SCM_API_BASE_URL}/api/inventory/out",
            json={
                "product_text": product_code,
                "qty": float(qty),  # SCM API expects 'qty' not 'qty_delta'
                "order_no": shipment_no,
                "remark": f"出货单 {shipment_no} 发货扣减",
                "allow_negative": False  # 不允许负库存
            },
            max_retries=3,
            timeout=15
        )
        response.raise_for_status()
        result = response.json()
        success = result.get('ok', False)

        if success:
            # 记录成功的扣减 - 用于审计追踪
            logger.info(
                f"[库存扣减成功] shipment_no={shipment_no}, "
                f"product_code={product_code}, qty={qty}, "
                f"scm_response={result.get('data')}"
            )
        else:
            # 记录扣减失败
            logger.error(
                f"[库存扣减失败-业务错误] shipment_no={shipment_no}, "
                f"product_code={product_code}, qty={qty}, "
                f"error={result.get('error')}"
            )

        return {
            'success': success,
            'data': result.get('data'),
            'error': result.get('error')
        }
    except RETRYABLE_EXCEPTIONS as e:
        # P2-18: 记录连接失败（所有重试均失败后）
        logger.error(
            f"[库存扣减失败-连接错误] shipment_no={shipment_no}, "
            f"product_code={product_code}, qty={qty}, "
            f"error={str(e)} (已重试3次)"
        )
        return {
            'success': False,
            'error': f'SCM系统连接失败: {str(e)}'
        }
    except Exception as e:
        # 其他异常
        logger.error(
            f"[库存扣减失败-未知错误] shipment_no={shipment_no}, "
            f"product_code={product_code}, qty={qty}, "
            f"error={str(e)}"
        )
        return {
            'success': False,
            'error': f'SCM系统调用异常: {str(e)}'
        }


def log_inventory_rollback_needed(shipment_no, items, reason):
    """
    记录需要手动回滚库存的警告

    当 SHM 操作在库存扣减后失败时调用此函数，
    以便管理员知道需要手动恢复哪些库存。

    Args:
        shipment_no: 出货单号
        items: 已扣减的明细列表 [{'product_code': ..., 'qty': ...}, ...]
        reason: 失败原因
    """
    logger.critical(
        f"[需要手动回滚库存] shipment_no={shipment_no}, "
        f"reason={reason}, "
        f"items_to_restore={items}, "
        f"timestamp={datetime.now().isoformat()}"
    )
    # TODO: 未来可以在这里发送告警通知（邮件/钉钉等）


def check_inventory(product_code):
    """
    查询SCM系统库存

    Args:
        product_code: 产品编码

    Returns:
        dict: 库存信息
    """
    try:
        # P2-18: 使用带重试的 HTTP 客户端
        response = get_with_retry(
            f"{Config.SCM_API_BASE_URL}/api/inventory",
            params={"product_text": product_code},
            max_retries=3,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except RETRYABLE_EXCEPTIONS as e:
        return {
            'success': False,
            'error': f'SCM系统连接失败: {str(e)} (已重试)'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'SCM系统调用异常: {str(e)}'
        }
