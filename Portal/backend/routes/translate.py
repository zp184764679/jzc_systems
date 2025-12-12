# -*- coding: utf-8 -*-
"""翻译助手 API 路由"""

import os
import subprocess
import tempfile
from flask import Blueprint, request, jsonify

# 从环境变量设置代理（如果未设置则不使用代理）
http_proxy = os.getenv('HTTP_PROXY', os.getenv('http_proxy', ''))
https_proxy = os.getenv('HTTPS_PROXY', os.getenv('https_proxy', ''))
if http_proxy:
    os.environ['HTTP_PROXY'] = http_proxy
if https_proxy:
    os.environ['HTTPS_PROXY'] = https_proxy

translate_bp = Blueprint('translate', __name__, url_prefix='/api/translate')


@translate_bp.route('/text', methods=['POST'])
def translate_text():
    """翻译文本"""
    data = request.json
    content = data.get('content', '').strip()
    target_lang = data.get('target', '中文')
    context = data.get('context', '')
    is_reply = data.get('is_reply', False)

    if not content:
        return jsonify({'error': '内容为空'}), 400

    if is_reply and context:
        prompt = f'''根据以下邮件往来的语境，将我的中文回复翻译成{target_lang}。
要求：
1. 保持邮件格式和礼貌用语
2. 专业准确，符合商务邮件规范
3. 只输出翻译结果，不要任何解释

对方邮件原文：
{context}

我的中文回复：
{content}'''
    else:
        prompt = f'''将以下内容翻译成{target_lang}。
要求：
1. 保持原文格式
2. 专业准确
3. 只输出翻译结果，不要任何解释

原文：
{content}'''

    pf = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(prompt)
            pf = f.name

        # 安全修复：避免 shell=True，改用 PowerShell 读取文件内容传递给 claude
        # 使用列表参数构建命令，避免命令注入
        result = subprocess.run(
            ['powershell', '-Command', f'Get-Content -Raw -Path "{pf}" | claude -p - --model claude-opus-4-5-20251101'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=180,
            shell=False  # 安全：不使用 shell
        )
        os.unlink(pf)
        pf = None

        if result.stdout.strip():
            return jsonify({'result': result.stdout.strip()})
        else:
            return jsonify({'error': '翻译失败，请稍后重试'}), 500

    except subprocess.TimeoutExpired:
        if pf and os.path.exists(pf):
            os.unlink(pf)
        return jsonify({'error': '翻译超时，请重试'}), 504
    except Exception:
        if pf and os.path.exists(pf):
            os.unlink(pf)
        return jsonify({'error': '翻译服务暂时不可用'}), 500


@translate_bp.route('/detect', methods=['POST'])
def detect_language():
    """检测文本语言"""
    text = request.json.get('text', '')

    # 简单的语言检测逻辑
    has_japanese = any('\u3040' <= c <= '\u30ff' for c in text)  # 平假名和片假名
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)   # 中文字符

    if has_japanese:
        lang = '日本語'
    elif has_chinese and not has_japanese:
        lang = '中文'
    else:
        lang = 'English'

    return jsonify({'lang': lang})
