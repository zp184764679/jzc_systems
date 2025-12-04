# -*- coding: utf-8 -*-
"""
填充物料知识库脚本
添加常见机加工行业物料
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from services.material_knowledge import get_knowledge_service

# 常见机加工物料数据
MACHINING_MATERIALS = [
    # ========== 刀具 ==========
    # 车削刀具
    {
        "standard_name": "车刀",
        "category": "刀具/车削刀具",
        "major_category": "刀具",
        "minor_category": "车削刀具",
        "synonyms": "车削刀具,外圆车刀,内孔车刀,端面车刀",
        "keywords": "车刀,车削,外圆,内孔,端面,切削",
        "description": "用于车削加工的刀具，可加工外圆、内孔、端面等",
        "usage_scenario": "车床加工,外圆加工,内孔加工",
        "match_priority": 90
    },
    {
        "standard_name": "车刀片",
        "category": "刀具/车削刀具",
        "major_category": "刀具",
        "minor_category": "车削刀具",
        "synonyms": "刀片,可转位刀片,车削刀片,硬质合金刀片",
        "keywords": "刀片,可转位,硬质合金,涂层,CNMG,TNMG,DNMG",
        "description": "可转位车削刀片，硬质合金材质",
        "usage_scenario": "车削加工,精加工,粗加工",
        "match_priority": 85
    },

    # 铣削刀具
    {
        "standard_name": "铣刀",
        "category": "刀具/铣削刀具",
        "major_category": "刀具",
        "minor_category": "铣削刀具",
        "synonyms": "铣削刀具,立铣刀,面铣刀,键槽铣刀,T型铣刀",
        "keywords": "铣刀,铣削,立铣,面铣,键槽,球头,平底",
        "description": "用于铣削加工的刀具，包括立铣刀、面铣刀等",
        "usage_scenario": "铣床加工,加工中心,平面铣削,轮廓铣削",
        "match_priority": 90
    },
    {
        "standard_name": "立铣刀",
        "category": "刀具/铣削刀具",
        "major_category": "刀具",
        "minor_category": "铣削刀具",
        "synonyms": "端铣刀,平底铣刀,球头铣刀",
        "keywords": "立铣,端铣,平底,球头,2刃,4刃,硬质合金",
        "description": "立式铣削刀具，可加工平面、台阶、槽等",
        "usage_scenario": "立式铣削,槽加工,型腔加工",
        "match_priority": 85
    },
    {
        "standard_name": "面铣刀",
        "category": "刀具/铣削刀具",
        "major_category": "刀具",
        "minor_category": "铣削刀具",
        "synonyms": "盘铣刀,平面铣刀",
        "keywords": "面铣,盘铣,平面,大直径,刀片式",
        "description": "大直径铣削刀具，用于加工平面",
        "usage_scenario": "平面加工,大面积铣削",
        "match_priority": 85
    },

    # 钻削刀具
    {
        "standard_name": "钻头",
        "category": "刀具/钻削刀具",
        "major_category": "刀具",
        "minor_category": "钻削刀具",
        "synonyms": "钻削刀具,麻花钻,中心钻,扁钻",
        "keywords": "钻头,钻孔,麻花钻,中心钻,直柄,锥柄",
        "description": "用于钻孔加工的刀具",
        "usage_scenario": "钻孔,钻床,加工中心",
        "match_priority": 90
    },
    {
        "standard_name": "麻花钻",
        "category": "刀具/钻削刀具",
        "major_category": "刀具",
        "minor_category": "钻削刀具",
        "synonyms": "标准钻头,直柄钻头,锥柄钻头",
        "keywords": "麻花,钻头,HSS,高速钢,含钴,直柄,锥柄",
        "description": "最常用的钻孔刀具，有直柄和锥柄两种",
        "usage_scenario": "通孔钻削,盲孔钻削",
        "match_priority": 85
    },

    # 丝锥铰刀镗刀
    {
        "standard_name": "丝锥",
        "category": "刀具/丝锥铰刀镗刀",
        "major_category": "刀具",
        "minor_category": "丝锥铰刀镗刀",
        "synonyms": "攻丝刀,螺纹刀具,机用丝锥,手用丝锥",
        "keywords": "丝锥,攻丝,螺纹,M3,M4,M5,M6,M8,M10,M12",
        "description": "用于加工内螺纹的刀具",
        "usage_scenario": "内螺纹加工,攻丝",
        "match_priority": 90
    },
    {
        "standard_name": "铰刀",
        "category": "刀具/丝锥铰刀镗刀",
        "major_category": "刀具",
        "minor_category": "丝锥铰刀镗刀",
        "synonyms": "精孔刀具,手铰刀,机铰刀",
        "keywords": "铰刀,铰孔,精孔,H7,H8,直柄,锥柄",
        "description": "用于精加工孔的刀具，提高孔的精度和表面质量",
        "usage_scenario": "孔精加工,配合孔加工",
        "match_priority": 85
    },
    {
        "standard_name": "镗刀",
        "category": "刀具/丝锥铰刀镗刀",
        "major_category": "刀具",
        "minor_category": "丝锥铰刀镗刀",
        "synonyms": "镗孔刀,精镗刀,粗镗刀",
        "keywords": "镗刀,镗孔,精镗,粗镗,内孔",
        "description": "用于镗孔加工的刀具，可调节直径",
        "usage_scenario": "大孔加工,精密孔加工",
        "match_priority": 85
    },

    # ========== 测量工具 ==========
    {
        "standard_name": "游标卡尺",
        "category": "测量工具/卡尺",
        "major_category": "测量工具",
        "minor_category": "卡尺",
        "synonyms": "卡尺,数显卡尺,带表卡尺",
        "keywords": "卡尺,游标,数显,0-150,0-200,0-300,测量",
        "description": "常用的长度测量工具，精度0.02mm",
        "usage_scenario": "长度测量,外径测量,内径测量,深度测量",
        "match_priority": 90
    },
    {
        "standard_name": "千分尺",
        "category": "测量工具/千分尺",
        "major_category": "测量工具",
        "minor_category": "千分尺",
        "synonyms": "螺旋测微器,外径千分尺,内径千分尺",
        "keywords": "千分尺,测微器,0-25,25-50,50-75,0.01mm",
        "description": "精密测量工具，精度0.01mm",
        "usage_scenario": "精密测量,外径测量",
        "match_priority": 85
    },
    {
        "standard_name": "高度尺",
        "category": "测量工具/高度尺",
        "major_category": "测量工具",
        "minor_category": "高度尺",
        "synonyms": "高度规,数显高度尺,带表高度尺",
        "keywords": "高度尺,高度规,划线,测高,0-300,0-500",
        "description": "用于测量高度和划线的工具",
        "usage_scenario": "高度测量,平面度检测,划线",
        "match_priority": 85
    },
    {
        "standard_name": "塞规",
        "category": "测量工具/塞规环规",
        "major_category": "测量工具",
        "minor_category": "塞规环规",
        "synonyms": "圆柱塞规,光面塞规,通止规",
        "keywords": "塞规,通规,止规,孔检,内孔,H7,H8",
        "description": "用于检测内孔尺寸的量规",
        "usage_scenario": "内孔检测,配合检测",
        "match_priority": 80
    },
    {
        "standard_name": "环规",
        "category": "测量工具/塞规环规",
        "major_category": "测量工具",
        "minor_category": "塞规环规",
        "synonyms": "圆环规,光面环规,轴用环规",
        "keywords": "环规,通规,止规,轴检,外圆,g6,h6",
        "description": "用于检测外圆尺寸的量规",
        "usage_scenario": "外圆检测,配合检测",
        "match_priority": 80
    },

    # ========== 机床附件 ==========
    {
        "standard_name": "刀柄",
        "category": "机床附件/刀柄夹头",
        "major_category": "机床附件",
        "minor_category": "刀柄夹头",
        "synonyms": "刀杆,BT刀柄,NT刀柄,HSK刀柄,ER刀柄",
        "keywords": "刀柄,BT30,BT40,BT50,NT40,HSK63,ER32",
        "description": "连接刀具与机床主轴的工具",
        "usage_scenario": "加工中心,数控铣床",
        "match_priority": 85
    },
    {
        "standard_name": "夹头",
        "category": "机床附件/刀柄夹头",
        "major_category": "机床附件",
        "minor_category": "刀柄夹头",
        "synonyms": "弹簧夹头,ER夹头,筒夹",
        "keywords": "夹头,ER11,ER16,ER20,ER25,ER32,ER40,筒夹",
        "description": "用于夹持刀具的弹性夹紧装置",
        "usage_scenario": "刀具夹持,高速加工",
        "match_priority": 85
    },
    {
        "standard_name": "卡盘",
        "category": "机床附件/卡盘",
        "major_category": "机床附件",
        "minor_category": "卡盘",
        "synonyms": "三爪卡盘,四爪卡盘,液压卡盘",
        "keywords": "卡盘,三爪,四爪,液压,自定心,手动",
        "description": "车床用工件夹持装置",
        "usage_scenario": "车床加工,工件装夹",
        "match_priority": 85
    },
    {
        "standard_name": "顶尖",
        "category": "机床附件/顶尖",
        "major_category": "机床附件",
        "minor_category": "顶尖",
        "synonyms": "回转顶尖,固定顶尖,活顶尖",
        "keywords": "顶尖,回转,固定,莫氏,MT2,MT3,MT4",
        "description": "车床用轴类工件支承装置",
        "usage_scenario": "车床加工,轴类支承",
        "match_priority": 80
    },

    # ========== 五金劳保 ==========
    {
        "standard_name": "螺栓",
        "category": "五金劳保/紧固件",
        "major_category": "五金劳保",
        "minor_category": "紧固件",
        "synonyms": "螺丝,六角螺栓,内六角螺栓",
        "keywords": "螺栓,螺丝,M3,M4,M5,M6,M8,M10,M12,六角,内六角",
        "description": "机械紧固用标准件",
        "usage_scenario": "机械装配,紧固连接",
        "match_priority": 85
    },
    {
        "standard_name": "螺母",
        "category": "五金劳保/紧固件",
        "major_category": "五金劳保",
        "minor_category": "紧固件",
        "synonyms": "螺帽,六角螺母,法兰螺母,锁紧螺母",
        "keywords": "螺母,螺帽,六角,法兰,锁紧,M3,M4,M5,M6,M8",
        "description": "与螺栓配合使用的紧固件",
        "usage_scenario": "机械装配,螺栓连接",
        "match_priority": 85
    },
    {
        "standard_name": "垫圈",
        "category": "五金劳保/紧固件",
        "major_category": "五金劳保",
        "minor_category": "紧固件",
        "synonyms": "平垫,弹簧垫圈,弹垫",
        "keywords": "垫圈,平垫,弹垫,弹簧,M3,M4,M5,M6,M8",
        "description": "紧固连接中的辅助件",
        "usage_scenario": "螺栓连接,防松,增大接触面",
        "match_priority": 80
    },
    {
        "standard_name": "手套",
        "category": "五金劳保/劳保防护",
        "major_category": "五金劳保",
        "minor_category": "劳保防护",
        "synonyms": "劳保手套,防护手套,工作手套,线手套,皮手套",
        "keywords": "手套,劳保,防护,线手套,皮手套,防滑",
        "description": "劳动防护用手套",
        "usage_scenario": "机械作业,搬运,防护",
        "match_priority": 80
    },

    # ========== 化工辅料 ==========
    {
        "standard_name": "切削液",
        "category": "化工辅料/切削液",
        "major_category": "化工辅料",
        "minor_category": "切削液",
        "synonyms": "冷却液,乳化液,切削油",
        "keywords": "切削液,冷却液,乳化液,水溶性,油性",
        "description": "金属切削加工中的冷却润滑液",
        "usage_scenario": "车削,铣削,磨削,冷却,润滑",
        "match_priority": 85
    },
    {
        "standard_name": "润滑油",
        "category": "化工辅料/润滑油脂",
        "major_category": "化工辅料",
        "minor_category": "润滑油脂",
        "synonyms": "机油,液压油,导轨油",
        "keywords": "润滑油,机油,液压油,导轨油,32#,46#,68#",
        "description": "机床及设备润滑用油",
        "usage_scenario": "机床润滑,液压系统,导轨润滑",
        "match_priority": 85
    },

    # ========== 磨具磨料 ==========
    {
        "standard_name": "砂轮",
        "category": "磨具磨料/砂轮",
        "major_category": "磨具磨料",
        "minor_category": "砂轮",
        "synonyms": "磨轮,平面砂轮,外圆砂轮",
        "keywords": "砂轮,磨轮,白刚玉,棕刚玉,磨削",
        "description": "磨削加工用磨具",
        "usage_scenario": "平面磨削,外圆磨削,工具刃磨",
        "match_priority": 85
    },
    {
        "standard_name": "砂纸",
        "category": "磨具磨料/砂纸",
        "major_category": "磨具磨料",
        "minor_category": "砂纸",
        "synonyms": "砂布,水砂纸,干砂纸",
        "keywords": "砂纸,砂布,水磨,干磨,60目,80目,120目,240目",
        "description": "手工打磨用磨料",
        "usage_scenario": "表面打磨,抛光,去毛刺",
        "match_priority": 80
    },

    # ========== 机械零部件 ==========
    {
        "standard_name": "轴承",
        "category": "机械零部件/轴承",
        "major_category": "机械零部件",
        "minor_category": "轴承",
        "synonyms": "滚动轴承,深沟球轴承,圆锥滚子轴承",
        "keywords": "轴承,6000,6200,6300,深沟球,圆锥,滚子",
        "description": "机械传动中的支承部件",
        "usage_scenario": "旋转支承,减少摩擦",
        "match_priority": 85
    },
    {
        "standard_name": "齿轮",
        "category": "机械零部件/齿轮",
        "major_category": "机械零部件",
        "minor_category": "齿轮",
        "synonyms": "直齿轮,斜齿轮,伞齿轮",
        "keywords": "齿轮,直齿,斜齿,伞齿,模数,齿数",
        "description": "机械传动用齿轮",
        "usage_scenario": "动力传动,变速",
        "match_priority": 80
    },
    {
        "standard_name": "皮带",
        "category": "机械零部件/传动带",
        "major_category": "机械零部件",
        "minor_category": "传动带",
        "synonyms": "传动带,V带,三角带,同步带",
        "keywords": "皮带,V带,三角带,同步带,传动",
        "description": "机械传动用皮带",
        "usage_scenario": "动力传动,皮带传动",
        "match_priority": 80
    },
]


def main():
    """主函数"""
    with app.app_context():
        print("=" * 60)
        print("开始填充物料知识库")
        print("=" * 60)

        knowledge_service = get_knowledge_service()

        # 批量添加物料
        count = knowledge_service.batch_add_materials(MACHINING_MATERIALS)

        print("=" * 60)
        print(f"✅ 完成！成功添加 {count}/{len(MACHINING_MATERIALS)} 条物料记录")
        print("=" * 60)


if __name__ == "__main__":
    main()
