# constants/categories.py
# -*- coding: utf-8 -*-

# 品类层级结构：大类 → 子类列表
CATEGORY_HIERARCHY = {
    "刀具": [
        "车削刀具",
        "铣削刀具", 
        "钻削刀具",
        "丝锥铰刀镗刀"
    ],
    "测量工具": [
        "卡尺",
        "千分尺",
        "高度尺",
        "塞规环规",
        "量块",
        "粗糙度仪"
    ],
    "机床附件": [
        "夹具治具",
        "刀柄夹头",
        "卡盘",
        "顶尖",
        "拉钉",
        "V形块"
    ],
    "五金劳保": [
        "紧固件",
        "工具类",
        "劳保防护"
    ],
    "包装印刷": [
        "包装箱",
        "缓冲材料",
        "标签不干胶",
        "说明书"
    ],
    "化工辅料": [
        "切削液",
        "防锈剂",
        "脱模剂",
        "清洗剂",
        "润滑油脂"
    ],
    "电器气动": [
        "继电器",
        "接触器",
        "传感器",
        "电机",
        "气缸",
        "气管接头"
    ],
    "磨具磨料": [
        "砂轮",
        "砂纸",
        "油石",
        "百叶轮",
        "砂带"
    ],
}

# 为了向后兼容，保留扁平列表（从层级结构生成）
CATEGORIES = []
for major, subs in CATEGORY_HIERARCHY.items():
    for sub in subs:
        CATEGORIES.append(f"{major}/{sub}")

# 大类列表（供应商注册时选择）
MAJOR_CATEGORIES = list(CATEGORY_HIERARCHY.keys())

# 子类列表（可选，用于详细匹配）
MINOR_CATEGORIES = []
for subs in CATEGORY_HIERARCHY.values():
    MINOR_CATEGORIES.extend(subs)

# 辅助函数
def get_major_category(full_category: str) -> str:
    """从"大类/子类"提取大类"""
    if not full_category:
        return ""
    if "/" in full_category:
        return full_category.split("/")[0].strip()
    return full_category.strip()

def get_minor_category(full_category: str) -> str:
    """从"大类/子类"提取子类"""
    if not full_category:
        return ""
    if "/" in full_category:
        parts = full_category.split("/")
        return parts[1].strip() if len(parts) > 1 else ""
    return ""

def is_valid_category(full_category: str) -> bool:
    """验证品类是否在允许列表中"""
    return full_category in CATEGORIES

def is_valid_major_category(major_category: str) -> bool:
    """验证大类是否有效"""
    return major_category in MAJOR_CATEGORIES