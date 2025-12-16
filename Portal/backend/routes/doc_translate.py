# -*- coding: utf-8 -*-
"""文档翻译工具 API - 购买仕样书等PDF文件翻译"""

import os
import subprocess
import tempfile
import uuid
import base64
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO

# 从环境变量设置代理（如果未设置则不使用代理）
http_proxy = os.getenv('HTTP_PROXY', os.getenv('http_proxy', ''))
https_proxy = os.getenv('HTTPS_PROXY', os.getenv('https_proxy', ''))
if http_proxy:
    os.environ['HTTP_PROXY'] = http_proxy
if https_proxy:
    os.environ['HTTPS_PROXY'] = https_proxy

doc_translate_bp = Blueprint('doc_translate', __name__, url_prefix='/api/doc-translate')

# 存储翻译任务状态
TASKS = {}
# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'translated_docs')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_pdf_pages_as_images(pdf_path):
    """将PDF每页提取为图片"""
    doc = fitz.open(pdf_path)
    images = []
    for i, page in enumerate(doc):
        # 2倍缩放获取高清图片
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        images.append({
            'page': i + 1,
            'data': img_data,
            'width': pix.width,
            'height': pix.height
        })
    doc.close()
    return images


def translate_image_with_claude(image_data, page_num, target_lang='中文'):
    """使用Claude翻译图片中的文字"""
    # 安全修复：验证 target_lang 只能是预定义的语言
    allowed_langs = {'中文', '英文', '日文', 'English', 'Chinese', 'Japanese'}
    if target_lang not in allowed_langs:
        target_lang = '中文'  # 默认为中文

    img_path = None
    prompt_path = None

    try:
        # 将图片保存为临时文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(image_data)
            img_path = f.name

        prompt = f'''这是一份日本购买仕样书（采购规格书）的第{page_num}页。

请将图片中的所有日文内容翻译成{target_lang}，包括：
1. 标题、表头
2. 正文内容、说明文字
3. 表格中的文字
4. 注释、备注
5. 图表中的标注

翻译要求：
- 保持专业术语准确（如：めっき=电镀、外観=外观、寸法=尺寸）
- 保持原文的结构和逻辑
- 对于检验标准、判定基准等重要内容要准确翻译
- 如果有等级划分（如Lv.1、Lv.2等），保留原标记并翻译说明

直接输出翻译内容，不需要任何解释或前言。'''

        # 将 prompt 写入临时文件，避免命令注入
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(prompt)
            prompt_path = f.name

        # 安全修复：避免 shell=True，使用 PowerShell 列表参数
        # 从文件读取 prompt 内容，避免命令行参数注入
        result = subprocess.run(
            ['powershell', '-Command',
             f'$prompt = Get-Content -Raw -Path "{prompt_path}"; claude -p $prompt "{img_path}"'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300,  # 5分钟超时
            shell=False  # 安全：不使用 shell
        )

        # 清理临时文件
        if os.path.exists(img_path):
            os.unlink(img_path)
            img_path = None
        if os.path.exists(prompt_path):
            os.unlink(prompt_path)
            prompt_path = None

        if result.stdout.strip():
            return result.stdout.strip()
        else:
            return f"[第{page_num}页翻译失败]"

    except subprocess.TimeoutExpired:
        return f"[第{page_num}页翻译超时]"
    except Exception:
        return f"[第{page_num}页翻译错误]"
    finally:
        # 确保清理临时文件
        if img_path and os.path.exists(img_path):
            os.unlink(img_path)
        if prompt_path and os.path.exists(prompt_path):
            os.unlink(prompt_path)


def create_translated_pdf(images, translations, output_path):
    """创建带翻译的PDF文件"""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.units import mm

    # 注册中文字体
    try:
        pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
        pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
    except Exception:
        pass  # 字体注册失败时使用默认字体

    # 创建PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )

    # 样式
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        'PageTitle',
        parent=styles['Heading2'],
        fontName='SimHei',
        fontSize=14,
        textColor='#1a5490',
        spaceAfter=10
    )
    style_trans = ParagraphStyle(
        'Translation',
        parent=styles['Normal'],
        fontName='SimSun',
        fontSize=10,
        leading=16,
        spaceAfter=20
    )

    story = []
    page_width = A4[0] - 30*mm

    for i, (img_info, translation) in enumerate(zip(images, translations)):
        # 页面标题
        story.append(Paragraph(f"第 {img_info['page']} 页", style_title))

        # 原图
        img_stream = BytesIO(img_info['data'])
        img = RLImage(img_stream)

        # 计算图片尺寸，适应页面宽度
        aspect = img_info['height'] / img_info['width']
        display_w = min(page_width, 180*mm)
        display_h = display_w * aspect

        # 如果太高，按高度限制
        max_h = 120*mm
        if display_h > max_h:
            display_h = max_h
            display_w = display_h / aspect

        img.drawWidth = display_w
        img.drawHeight = display_h
        story.append(img)
        story.append(Spacer(1, 10))

        # 翻译内容
        story.append(Paragraph("<b>【中文翻译】</b>", style_title))
        # 处理翻译文本中的换行
        trans_text = translation.replace('\n', '<br/>')
        story.append(Paragraph(trans_text, style_trans))

        # 分页（最后一页不需要）
        if i < len(images) - 1:
            story.append(PageBreak())

    doc.build(story)
    return output_path


@doc_translate_bp.route('/upload', methods=['POST'])
def upload_and_translate():
    """上传PDF文件并开始翻译"""
    if 'file' not in request.files:
        return jsonify({'error': '请选择文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '文件名为空'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': '只支持PDF文件'}), 400

    target_lang = request.form.get('target', '中文')

    # 保存上传的文件
    task_id = str(uuid.uuid4())[:8]
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, file.filename)
    file.save(pdf_path)

    # 初始化任务状态
    TASKS[task_id] = {
        'status': 'processing',
        'filename': file.filename,
        'progress': 0,
        'total_pages': 0,
        'current_page': 0,
        'created_at': datetime.now().isoformat(),
        'output_path': None,
        'error': None
    }

    try:
        # 提取PDF页面
        images = extract_pdf_pages_as_images(pdf_path)
        total_pages = len(images)
        TASKS[task_id]['total_pages'] = total_pages

        # 翻译每一页
        translations = []
        for i, img_info in enumerate(images):
            TASKS[task_id]['current_page'] = i + 1
            TASKS[task_id]['progress'] = int((i / total_pages) * 100)

            translation = translate_image_with_claude(
                img_info['data'],
                img_info['page'],
                target_lang
            )
            translations.append(translation)

        # 生成翻译后的PDF
        output_filename = f"{os.path.splitext(file.filename)[0]}_中文版_{task_id}.pdf"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        create_translated_pdf(images, translations, output_path)

        TASKS[task_id]['status'] = 'completed'
        TASKS[task_id]['progress'] = 100
        TASKS[task_id]['output_path'] = output_path
        TASKS[task_id]['output_filename'] = output_filename

        # 清理临时文件
        os.unlink(pdf_path)
        os.rmdir(temp_dir)

        return jsonify({
            'task_id': task_id,
            'status': 'completed',
            'filename': output_filename,
            'download_url': f'/api/doc-translate/download/{task_id}'
        })

    except Exception as e:
        TASKS[task_id]['status'] = 'failed'
        TASKS[task_id]['error'] = str(e)
        return jsonify({'error': str(e)}), 500


@doc_translate_bp.route('/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取翻译任务状态"""
    if task_id not in TASKS:
        return jsonify({'error': '任务不存在'}), 404

    task = TASKS[task_id]
    return jsonify({
        'task_id': task_id,
        'status': task['status'],
        'progress': task['progress'],
        'total_pages': task['total_pages'],
        'current_page': task['current_page'],
        'filename': task['filename'],
        'error': task.get('error'),
        'download_url': f'/api/doc-translate/download/{task_id}' if task['status'] == 'completed' else None
    })


@doc_translate_bp.route('/download/<task_id>', methods=['GET'])
def download_translated(task_id):
    """下载翻译后的PDF"""
    if task_id not in TASKS:
        return jsonify({'error': '任务不存在'}), 404

    task = TASKS[task_id]
    if task['status'] != 'completed':
        return jsonify({'error': '翻译尚未完成'}), 400

    if not task.get('output_path') or not os.path.exists(task['output_path']):
        return jsonify({'error': '文件不存在'}), 404

    return send_file(
        task['output_path'],
        as_attachment=True,
        download_name=task.get('output_filename', 'translated.pdf')
    )


@doc_translate_bp.route('/list', methods=['GET'])
def list_tasks():
    """列出所有翻译任务"""
    tasks_list = []
    for task_id, task in TASKS.items():
        tasks_list.append({
            'task_id': task_id,
            'filename': task['filename'],
            'status': task['status'],
            'progress': task['progress'],
            'created_at': task['created_at'],
            'download_url': f'/api/doc-translate/download/{task_id}' if task['status'] == 'completed' else None
        })

    # 按创建时间倒序
    tasks_list.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify(tasks_list)
