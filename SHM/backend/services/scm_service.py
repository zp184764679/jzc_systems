import requests
from config import Config


def deduct_inventory(product_code, qty, shipment_no):
    """
    调用SCM系统扣减库存

    Args:
        product_code: 产品编码
        qty: 扣减数量
        shipment_no: 出货单号

    Returns:
        dict: SCM系统返回结果
    """
    try:
        response = requests.post(
            f"{Config.SCM_API_BASE_URL}/api/inventory/out",
            json={
                "product_text": product_code,
                "qty": float(qty),  # SCM API expects 'qty' not 'qty_delta'
                "order_no": shipment_no,
                "remark": f"出货单 {shipment_no} 发货扣减",
                "allow_negative": False  # 不允许负库存
            },
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        # SCM returns {"ok": true/false, ...}
        return {
            'success': result.get('ok', False),
            'data': result.get('data'),
            'error': result.get('error')
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'SCM系统连接失败: {str(e)}'
        }


def check_inventory(product_code):
    """
    查询SCM系统库存

    Args:
        product_code: 产品编码

    Returns:
        dict: 库存信息
    """
    try:
        response = requests.get(
            f"{Config.SCM_API_BASE_URL}/api/inventory",
            params={"product_text": product_code},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'SCM系统连接失败: {str(e)}'
        }
