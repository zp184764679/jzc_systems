# -*- coding: utf-8 -*-
"""
PaddleOCR 独立脚本
用于被主程序调用，避免 venv 依赖问题
"""
import sys
import json

def ocr_image(image_path):
    """
    使用 PaddleOCR 识别图片中的文字
    """
    try:
        from paddleocr import PaddleOCR

        # 初始化 OCR
        ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)

        # 识别
        result = ocr.ocr(image_path, cls=True)

        if not result or not result[0]:
            return {'success': False, 'error': '未识别到文字'}

        # 提取所有识别的文字
        texts = []
        for line in result[0]:
            if line and len(line) >= 2:
                text = line[1][0]  # 文字内容
                confidence = line[1][1]  # 置信度
                box = line[0]  # 位置框
                # 计算文字的 y 坐标（用于排序）
                y_pos = (box[0][1] + box[2][1]) / 2
                x_pos = (box[0][0] + box[2][0]) / 2
                texts.append({
                    'text': text,
                    'confidence': confidence,
                    'y': y_pos,
                    'x': x_pos
                })

        # 按 y 坐标排序（从上到下），同一行按 x 排序（从左到右）
        texts.sort(key=lambda t: (round(t['y'] / 30), t['x']))

        # 拼接所有文字
        full_text = '\n'.join([t['text'] for t in texts])

        return {
            'success': True,
            'text': full_text,
            'count': len(texts)
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'success': False, 'error': '请提供图片路径'}, ensure_ascii=False))
        sys.exit(1)

    image_path = sys.argv[1]
    result = ocr_image(image_path)
    print(json.dumps(result, ensure_ascii=False))
