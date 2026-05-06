from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import json
import os

app = Flask(__name__, static_folder='.')
CORS(app)

EXCEL_FILE = '工作内容数据.xlsx'
JSON_FILE = 'data.json'

def load_excel_to_json():
    try:
        df = pd.read_excel(EXCEL_FILE)
        
        difficulty_map = {
            '高难度（核心关键）': 'high',
            '中难度（重要常规）': 'medium', 
            '低难度（基础事务）': 'low',
            '中难度（重要常规）\t': 'medium'
        }
        
        difficulty_reverse = {
            'high': '高难度（核心关键）',
            'medium': '中难度（重要常规）',
            'low': '低难度（基础事务）'
        }
        
        persons = {}
        all_tasks = []
        
        for _, row in df.iterrows():
            person = row['现责任人']
            if pd.isna(person) or person == '':
                person = '未分配'
            
            difficulty = str(row['难度系数']).strip() if pd.notna(row['难度系数']) else '低难度（基础事务）'
            difficulty_level = difficulty_map.get(difficulty, 'low')
            
            task = {
                'level1': row['一级分类'],
                'level2': row['二级分类'],
                'level3': row['三级分类'],
                'description': str(row['工作描述']) if pd.notna(row['工作描述']) else '',
                'remark': str(row['备注']) if pd.notna(row['备注']) else '',
                'adjustable': str(row['可调整项目']) if pd.notna(row['可调整项目']) else '',
                'difficulty': difficulty_level,
                'difficulty_name': difficulty,
                'current_person': person
            }
            all_tasks.append(task)
            
            if person not in persons:
                persons[person] = []
            persons[person].append(task)
        
        result = {
            'persons': [],
            'all_tasks': all_tasks,
            'difficulty_options': [
                {'value': 'high', 'label': '高难度（核心关键）'},
                {'value': 'medium', 'label': '中难度（重要常规）'},
                {'value': 'low', 'label': '低难度（基础事务）'}
            ]
        }
        
        for person, tasks in persons.items():
            result['persons'].append({
                'name': person,
                'count': len(tasks),
                'tasks': tasks
            })
        
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    except Exception as e:
        return {'error': str(e)}

@app.route('/')
def index():
    return send_file('工作分配展板.html')

@app.route('/工作分配展板.html')
def html_page():
    return send_file('工作分配展板.html')

@app.route('/api/load', methods=['GET'])
def load_data():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    
    if os.path.exists(EXCEL_FILE):
        return jsonify(load_excel_to_json())
    
    return jsonify({'error': '数据文件不存在'}), 404

@app.route('/api/save', methods=['POST'])
def save_data():
    try:
        data = request.json
        task_name = data.get('taskName')
        new_person = data.get('newPerson')
        
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            for person in result['persons']:
                for task in person['tasks']:
                    if task['level3'] == task_name:
                        task['current_person'] = new_person
            
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            return jsonify({'success': True, 'message': f'已将 "{task_name}" 分配给 {new_person}'})
        
        return jsonify({'success': False, 'message': '数据文件不存在'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save_difficulty', methods=['POST'])
def save_difficulty():
    try:
        data = request.json
        task_name = data.get('taskName')
        new_difficulty = data.get('newDifficulty')
        
        difficulty_map = {
            'high': '高难度（核心关键）',
            'medium': '中难度（重要常规）',
            'low': '低难度（基础事务）'
        }
        
        difficulty_label = difficulty_map.get(new_difficulty, '低难度（基础事务）')
        
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            for person in result['persons']:
                for task in person['tasks']:
                    if task['level3'] == task_name:
                        task['difficulty'] = new_difficulty
                        task['difficulty_name'] = difficulty_label
            
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            return jsonify({'success': True, 'message': f'已将 "{task_name}" 难度改为 {difficulty_label}'})
        
        return jsonify({'success': False, 'message': '数据文件不存在'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
