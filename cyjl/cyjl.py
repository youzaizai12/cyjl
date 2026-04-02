from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import random
import os
import json
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ---------------------- 配置 ----------------------
TXT_FILE_PATH = "idioms.txt"
MODEL_PATH = r"D:\大模型应用开发\案例四\models\AI-ModelScope\bge-large-zh-v1.5"
VECTOR_DB_PATH = "faiss_idioms"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

# 全局变量
vectorstore = None
all_idioms_list = []
all_idioms_set = set()
game_history = []
game_state = {
    'current_idiom': '',
    'last_char': '',
    'turn': 'player',
    'game_active': True,
    'winner': None,
    'used_idioms': [],
    'game_id': None,
    'first_player': 'player',
    'player_moves': [],
    'ai_moves': [],
    'use_ollama': True
}

# ---------------------- 构建/加载向量库 ----------------------
def get_or_build_vector_db():
    global vectorstore
    
    if os.path.exists(VECTOR_DB_PATH):
        try:
            embedding = HuggingFaceEmbeddings(model_name=MODEL_PATH)
            vs = FAISS.load_local(VECTOR_DB_PATH, embedding, allow_dangerous_deserialization=True)
            print("✅ 已加载本地成语向量库")
            vectorstore = vs
            return vs
        except Exception as e:
            print(f"加载向量库失败: {e}")
    
    print("🔨 正在构建成语向量库...")
    
    if not os.path.exists(TXT_FILE_PATH):
        print(f"❌ 找不到成语文件: {TXT_FILE_PATH}")
        return None
    
    with open(TXT_FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    valid_idioms = []
    for line in lines:
        word = line.strip()
        if len(word) == 4 and all('\u4e00' <= char <= '\u9fff' for char in word):
            valid_idioms.append(word)
    
    print(f"📚 从文件中解析出 {len(valid_idioms)} 个四字成语")
    
    documents = [Document(page_content=idiom, metadata={"source": "idiom_library"}) for idiom in valid_idioms]
    embedding = HuggingFaceEmbeddings(model_name=MODEL_PATH)
    vs = FAISS.from_documents(documents, embedding)
    vs.save_local(VECTOR_DB_PATH)
    print("✅ 成语向量库构建完成！")
    vectorstore = vs
    return vs

def load_idioms():
    """加载所有成语到列表和集合"""
    global all_idioms_list, all_idioms_set
    if vectorstore:
        docs = vectorstore.similarity_search("", k=15000)
        all_idioms_list = [doc.page_content.strip() for doc in docs]
        all_idioms_set = set(all_idioms_list)
        print(f"📚 加载了 {len(all_idioms_list)} 个成语")

# ---------------------- AI 接龙逻辑 ----------------------
def ai_make_move_with_ollama(last_char, used_idioms):
    """使用Ollama模型进行智能接龙"""
    
    if not last_char:
        available = [i for i in all_idioms_list if i not in used_idioms]
        return random.choice(available) if available else None
    
    used_list = "、".join(used_idioms[-15:]) if used_idioms else "无"
    
    prompt = f"""你是成语接龙专家。请根据上一个字的提示，接一个四字成语。

要求：
1. 成语必须以「{last_char}」字开头
2. 必须是真正的四字成语
3. 不能使用已经出现过的成语：{used_list}
4. 只输出成语本身，不要有任何解释

请输出一个符合要求的成语："""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.6,
                "max_tokens": 20
            },
            timeout=8
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_idiom = result.get('response', '').strip()
            ai_idiom = ai_idiom.replace('"', '').replace("'", "").replace('，', '').replace('。', '')
            
            if (len(ai_idiom) == 4 and 
                ai_idiom.startswith(last_char) and 
                ai_idiom not in used_idioms and 
                ai_idiom in all_idioms_set):
                return ai_idiom
                
    except Exception as e:
        print(f"Ollama调用失败: {e}")
    
    return None

def ai_make_move_traditional(last_char):
    """传统方法：随机选择匹配的成语"""
    if not last_char:
        available = [i for i in all_idioms_list if i not in game_state['used_idioms']]
        return random.choice(available) if available else None
    
    candidates = [idiom for idiom in all_idioms_list 
                  if idiom.startswith(last_char) and idiom not in game_state['used_idioms']]
    
    return random.choice(candidates) if candidates else None

def ai_make_move(last_char, use_ollama=True):
    """AI接龙主入口"""
    if use_ollama:
        result = ai_make_move_with_ollama(last_char, game_state['used_idioms'])
        if result:
            return result
        return ai_make_move_traditional(last_char)
    else:
        return ai_make_move_traditional(last_char)

def is_valid_idiom(idiom, last_char):
    """检查成语是否合法"""
    if len(idiom) != 4:
        return False, "成语必须是四个字"
    if not all('\u4e00' <= char <= '\u9fff' for char in idiom):
        return False, "只能使用中文字符"
    if last_char and idiom[0] != last_char:
        return False, f"成语必须以「{last_char}」开头"
    if idiom not in all_idioms_set:
        return False, "成语不在知识库中"
    if idiom in game_state['used_idioms']:
        return False, "成语已经使用过了"
    return True, ""

def save_game_to_history(winner, total_moves):
    """保存游戏记录"""
    game_record = {
        'game_id': game_state['game_id'],
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'winner': winner,
        'total_moves': total_moves,
        'first_player': game_state.get('first_player', 'player'),
        'player_moves': game_state.get('player_moves', []),
        'ai_moves': game_state.get('ai_moves', [])
    }
    
    game_history.insert(0, game_record)
    while len(game_history) > 20:
        game_history.pop()
    
    try:
        with open('game_history.json', 'w', encoding='utf-8') as f:
            json.dump(game_history, f, ensure_ascii=False, indent=2)
        print(f"✅ 游戏记录已保存: {winner}胜, 共{total_moves}步")
    except Exception as e:
        print(f"❌ 保存历史记录失败: {e}")

def load_history_from_file():
    """从文件加载历史记录"""
    global game_history
    try:
        if os.path.exists('game_history.json'):
            with open('game_history.json', 'r', encoding='utf-8') as f:
                game_history = json.load(f)
            print(f"📜 加载了 {len(game_history)} 条历史记录")
    except Exception as e:
        print(f"加载历史记录失败: {e}")
        game_history = []

# ---------------------- 路由 ----------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/init', methods=['POST'])
def init_game():
    global game_state
    
    if not vectorstore:
        get_or_build_vector_db()
        load_idioms()
    
    data = request.json
    first_player = data.get('first_player', 'player')
    use_ollama = data.get('use_ollama', True)
    
    game_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))
    
    game_state = {
        'current_idiom': '',
        'last_char': '',
        'turn': first_player,
        'game_active': True,
        'winner': None,
        'used_idioms': [],
        'game_id': game_id,
        'first_player': first_player,
        'player_moves': [],
        'ai_moves': [],
        'use_ollama': use_ollama
    }
    
    if first_player == 'ai':
        ai_idiom = ai_make_move('', use_ollama)
        if ai_idiom:
            game_state['current_idiom'] = ai_idiom
            game_state['last_char'] = ai_idiom[-1]
            game_state['used_idioms'].append(ai_idiom)
            game_state['ai_moves'].append(ai_idiom)
            game_state['turn'] = 'player'
            
            return jsonify({
                'success': True,
                'game_state': game_state,
                'ai_move': ai_idiom
            })
    
    return jsonify({
        'success': True,
        'game_state': game_state
    })

@app.route('/api/move', methods=['POST'])
def make_move():
    global game_state
    
    if not game_state['game_active']:
        return jsonify({'success': False, 'message': '游戏已结束！'})
    
    if game_state['turn'] != 'player':
        return jsonify({'success': False, 'message': '请等待AI出招！'})
    
    data = request.json
    idiom = data.get('idiom', '').strip()
    use_ollama = data.get('use_ollama', True)
    
    last_char = game_state['last_char'] if game_state['current_idiom'] else None
    
    is_valid, error_msg = is_valid_idiom(idiom, last_char)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg})
    
    game_state['player_moves'].append(idiom)
    game_state['used_idioms'].append(idiom)
    game_state['current_idiom'] = idiom
    game_state['last_char'] = idiom[-1]
    
    ai_response = ai_make_move(game_state['last_char'], use_ollama)
    
    if ai_response is None:
        game_state['game_active'] = False
        game_state['winner'] = 'player'
        game_state['turn'] = 'game_over'
        
        save_game_to_history('player', len(game_state['used_idioms']))
        
        return jsonify({
            'success': True,
            'game_state': game_state,
            'ai_move': None,
            'game_over': True,
            'winner': 'player',
            'player_move': idiom
        })
    
    game_state['ai_moves'].append(ai_response)
    game_state['used_idioms'].append(ai_response)
    game_state['current_idiom'] = ai_response
    game_state['last_char'] = ai_response[-1]
    game_state['turn'] = 'player'
    
    return jsonify({
        'success': True,
        'game_state': game_state,
        'ai_move': ai_response,
        'player_move': idiom,
        'game_over': False
    })

@app.route('/api/surrender', methods=['POST'])
def surrender():
    """玩家认输"""
    global game_state
    
    if not game_state['game_active']:
        return jsonify({'success': False, 'message': '游戏已结束！'})
    
    game_state['game_active'] = False
    game_state['winner'] = 'ai'
    game_state['turn'] = 'game_over'
    
    total_moves = len(game_state['used_idioms'])
    save_game_to_history('ai', total_moves)
    
    return jsonify({
        'success': True,
        'game_state': game_state,
        'game_over': True,
        'winner': 'ai',
        'message': '你认输了！'
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify({'success': True, 'history': game_history})

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    global game_history
    game_history = []
    try:
        if os.path.exists('game_history.json'):
            os.remove('game_history.json')
    except:
        pass
    return jsonify({'success': True})

@app.route('/api/ollama/status', methods=['GET'])
def check_ollama():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return jsonify({'success': True, 'available': True, 'models': [m['name'] for m in models]})
    except:
        pass
    return jsonify({'success': False, 'available': False})

if __name__ == '__main__':
    get_or_build_vector_db()
    load_idioms()
    load_history_from_file()
    print(f"\n✅ 成语库加载完成: {len(all_idioms_list)} 个成语")
    print(f"📜 历史记录: {len(game_history)} 条")
    print("🌐 访问 http://127.0.0.1:5000 开始游戏\n")
    app.run(debug=True, host='127.0.0.1', port=5000)