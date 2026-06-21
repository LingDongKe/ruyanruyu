from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import re

app = Flask(__name__)
CORS(app)

# ============================================
# 配置
# ============================================
EXCEL_PATH = 'data/字音数据.xlsx'
CACHE = {
    'data': [],
    'loaded': False,
    'stats': {}
}


# ============================================
# 加载数据
# ============================================
def load_data():
    """从Excel加载数据到内存"""
    if CACHE['loaded'] and CACHE['data']:
        return CACHE['data']

    try:
        if not os.path.exists(EXCEL_PATH):
            print(f'❌ 文件不存在: {EXCEL_PATH}')
            return []

        df = pd.read_excel(EXCEL_PATH)

        # 自动识别列名
        col_map = {}
        for col in df.columns:
            col_str = str(col).strip()
            if '汉' in col_str or '字' in col_str or 'char' in col_str.lower():
                col_map['char'] = col
            elif '读' in col_str or '音' in col_str or '拼音' in col_str or 'pinyin' in col_str.lower():
                col_map['pinyin'] = col
            elif '释' in col_str or '义' in col_str or '意思' in col_str or 'meaning' in col_str.lower():
                col_map['meaning'] = col

        if 'char' not in col_map or 'pinyin' not in col_map:
            print(f'❌ 未找到"汉字"或"读音"列。当前列名: {list(df.columns)}')
            return []

        data = []
        for _, row in df.iterrows():
            char_val = str(row[col_map['char']]).strip()
            pinyin_val = str(row[col_map['pinyin']]).strip()
            meaning_val = str(row[col_map.get('meaning', '')]).strip() if col_map.get('meaning') else ''

            if char_val and pinyin_val and char_val != 'nan' and pinyin_val != 'nan':
                entry = {
                    '汉字': char_val,
                    '读音': pinyin_val,
                    '释义': meaning_val if meaning_val and meaning_val != 'nan' else ''
                }
                data.append(entry)

        CACHE['data'] = data
        CACHE['loaded'] = True
        CACHE['stats'] = calculate_stats(data)
        print(f'✅ 成功加载 {len(data)} 条数据')
        return data

    except Exception as e:
        print(f'❌ 加载数据失败: {e}')
        return []


def calculate_stats(data):
    """计算统计数据"""
    if not data:
        return {'total': 0, 'chars': 0, 'polyphone': 0}

    char_counts = {}
    for item in data:
        char_counts[item['汉字']] = char_counts.get(item['汉字'], 0) + 1

    polyphone_count = sum(1 for count in char_counts.values() if count > 1)

    return {
        'total': len(data),
        'chars': len(char_counts),
        'polyphone': polyphone_count
    }


# ============================================
# 核心搜索功能
# ============================================
def search_by_char(query):
    """查询汉字 - 支持单个或多个汉字"""
    if not query or not query.strip():
        return [], {}

    query = query.strip()
    data = load_data()

    if not data:
        return [], {}

    # 智能拆分：支持逗号、空格、连续输入
    if ',' in query or '，' in query or ' ' in query:
        query = query.replace('，', ',')
        chars = [c.strip() for c in re.split('[,，\\s]+', query) if c.strip()]
    else:
        chars = list(query)
        chars = [c for c in chars if c.strip()]

    # 去重但保留顺序
    seen = set()
    unique_chars = []
    for c in chars:
        if c not in seen:
            seen.add(c)
            unique_chars.append(c)

    # 为每个字查询
    results = {}
    for char in unique_chars:
        matches = [item for item in data if item['汉字'] == char]
        if matches:
            matches.sort(key=lambda x: x['读音'])
            results[char] = matches

    # 返回顺序列表和结果字典
    return unique_chars, results


def search_by_meaning(keyword):
    """反查释义 - 支持多个关键词"""
    if not keyword or not keyword.strip():
        return [], {}

    keyword = keyword.strip()
    data = load_data()

    if not data:
        return [], {}

    # 拆分多个关键词
    if ',' in keyword or '，' in keyword or ' ' in keyword:
        keyword = keyword.replace('，', ',')
        keywords = [k.strip() for k in re.split('[,，\\s]+', keyword) if k.strip()]
    else:
        keywords = [keyword]

    # 对每个关键词查询
    results = {}
    for kw in keywords:
        matches = []
        for item in data:
            if item['释义'] and kw in item['释义']:
                matches.append(item)
        if matches:
            matches.sort(key=lambda x: x['汉字'])
            results[kw] = matches

    # 返回顺序列表和结果字典
    return keywords, results


# ============================================
# API 接口
# ============================================
@app.route('/api/search')
def search():
    """统一搜索接口"""
    query = request.args.get('q', '').strip()
    mode = request.args.get('mode', 'char')

    if not query:
        return jsonify({
            'success': False,
            'message': '请输入搜索内容',
            'data': {},
            'order': [],
            'total_count': 0,
            'char_count': 0
        })

    if mode == 'char':
        order, results = search_by_char(query)
        mode_name = '查询汉字'
    elif mode == 'meaning':
        order, results = search_by_meaning(query)
        mode_name = '反查释义'
    else:
        return jsonify({
            'success': False,
            'message': '无效的搜索模式',
            'data': {},
            'order': [],
            'total_count': 0,
            'char_count': 0
        })

    total_count = sum(len(items) for items in results.values())

    return jsonify({
        'success': True,
        'mode': mode,
        'mode_name': mode_name,
        'query': query,
        'total_count': total_count,
        'char_count': len(results),
        'order': order,  # 保持搜索顺序
        'data': results
    })


@app.route('/api/stats')
def stats():
    """获取统计信息"""
    load_data()
    return jsonify({
        'success': True,
        'stats': CACHE['stats']
    })


@app.route('/api/reload')
def reload_data():
    """重新加载数据"""
    global CACHE
    CACHE['loaded'] = False
    CACHE['data'] = []
    load_data()
    return jsonify({
        'success': True,
        'message': '数据已重新加载',
        'stats': CACHE['stats']
    })


# ============================================
# 页面路由
# ============================================
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


# ============================================
# 启动服务
# ============================================
if __name__ == '__main__':
    print('=' * 60)
    print('📖 汝言汝语 - 字音查询系统')
    print('=' * 60)
    print(f'📂 Excel 路径: {EXCEL_PATH}')
    print('🌐 访问地址: http://127.0.0.1:5000')
    print('=' * 60)

    load_data()
    print(f'📊 统计: {CACHE["stats"]}')
    print('=' * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)