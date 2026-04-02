# -成语接龙 AI 对战系统
一个基于大语言模型和向量检索技术的智能成语接龙游戏系统

📖项目简介
本项目是一个结合了大语言模型和向量检索技术的智能成语接龙游戏。系统提供了两种AI对战模式：

智能模式：使用 Ollama 运行的 Llama3 大语言模型，能够理解语义并创造性地进行成语接龙

传统模式：基于规则匹配的快速接龙算法

核心特性
🎮 双模式AI对战：智能模式（LLM）和传统模式（规则匹配）

🎲 自由选择先后手：玩家可选择先手或后手

📊 完整的游戏历史记录：自动保存每场游戏的详细记录

🏳️ 认输功能：玩家可随时认输结束游戏

🎨 现代化Web界面：响应式设计，支持移动端和PC端

🚀 高性能向量检索：基于 FAISS 的成语向量库，毫秒级检索

🏗️ 系统架构
<img width="870" height="648" alt="image" src="https://github.com/user-attachments/assets/78047268-bedc-4063-8cbd-96fec1e88d2b" />

📁 项目结构
<img width="671" height="505" alt="image" src="https://github.com/user-attachments/assets/e9ae6bb3-afeb-450e-a2f9-dd996b7217d7" />


🚀 快速开始
环境要求
Python 3.9+

Ollama (用于智能模式)

4GB+ 内存（推荐 8GB）

安装步骤
1. 克隆项目
2. 
RAG

git clone <repository-url>

cd cyjl

3. 安装 Python 依赖（在自己的虚拟环境中，我的虚拟环境叫RAG）
   
RAG

pip install -r requirements.txt

或手动安装：

RAG

pip install flask==2.3.0
pip install flask-cors==4.0.0
pip install langchain==0.1.0
pip install langchain-community==0.1.0
pip install langchain-huggingface==0.0.1
pip install faiss-cpu==1.7.4
pip install sentence-transformers==2.2.2
pip install requests

3. 准备成语库
创建 idioms.txt 文件，每行一个四字成语
（文件如上，需要自取）


5. 安装并配置 Ollama（智能模式）

   
# 下载并安装 Ollama（官网下载）
# 访问 https://ollama.ai/ 下载对应系统版本

# 拉取 Llama3 模型
ollama pull llama3
<img width="1117" height="744" alt="image" src="https://github.com/user-attachments/assets/431e846d-cf80-4765-a807-43d47351072c" />


# 启动 Ollama 服务
ollama serve


5. 运行游戏(也可以直接在VScode或者pycharm里面直接运行，VS是Ctrl+Shift+P然后点击Python:选择解释器 选择自己的虚拟环境)

RAG
python cyjl.py
访问 http://127.0.0.1:5000 开始游戏


🎮 使用说明
游戏规则
玩家和AI轮流说出四字成语

每个成语的第一个字必须与上一个成语的最后一个字相同

不能重复使用已经出现过的成语

无法接龙的一方失败

界面操作
游戏设置
先后手选择：选择玩家先手或AI先手

AI模式选择：

智能模式：使用 Ollama Llama3 大模型

传统模式：使用规则匹配算法

游戏控制
出招：输入四字成语后点击"出招"或按回车

认输：点击"🏳️ 认输"按钮结束游戏

新游戏：开始新的对局

清空历史：清除所有游戏记录

信息查看
当前成语：显示最新的成语

提示信息：显示游戏状态和错误提示

已使用成语：列出本局已使用的所有成语

历史记录：查看过往游戏记录和详情

🔧 技术实现
后端技术栈
技术	用途	说明
Flask	Web框架	提供 RESTful API
FAISS	向量检索	高效检索成语向量
Sentence-Transformers	文本向量化	BGE-large-zh-v1.5 模型
Ollama	LLM服务	运行 Llama3 模型
LangChain	框架集成	简化向量库操作
核心算法

1. 向量检索优化
2. 
python
# 使用 FAISS 构建成语向量索引
embedding = HuggingFaceEmbeddings(model_name="bge-large-zh-v1.5")

vectorstore = FAISS.from_documents(documents, embedding)

2. LLM 接龙策略
3. 
python
# 智能提示词设计

prompt = f"""
你是成语接龙专家。请根据「{last_char}」字接一个四字成语。
要求：
1. 必须以「{last_char}」开头
2. 不能使用已出现的成语：{used_idioms}
3. 只输出成语本身
"""
3. 传统匹配算法
4. 
python
# 基于前缀的快速匹配
candidates = [idiom for idiom in idioms 
              if idiom.startswith(last_char) 
              and idiom not in used_idioms]
return random.choice(candidates) if candidates else None

前端特性
响应式设计：适配移动端和PC端

实时交互：异步请求，无刷新更新

动画效果：流畅的过渡和弹出动画

状态管理：完整的前端游戏状态维护

📊 API 接口文档
初始化游戏
http
POST /api/init
Content-Type: application/json

{
    "first_player": "player",  // "player" 或 "ai"
    "use_ollama": true          // true: 智能模式, false: 传统模式
}
玩家出招
http
POST /api/move
Content-Type: application/json

{
    "idiom": "一帆风顺",
    "use_ollama": true
}

认输
http
POST /api/surrender

获取历史记录
http
GET /api/history

清空历史记录
http
POST /api/clear_history

检查 Ollama 状态
http
GET /api/ollama/status

结果如图
<img width="1892" height="1403" alt="image" src="https://github.com/user-attachments/assets/678ac0f0-4afb-4d30-a949-5e3bb34c35f8" />


🎯 性能优化
向量库缓存
首次构建后保存到本地

后续启动直接加载，速度提升 10x+

支持增量更新

前端优化
消息区域限制 100 条，防止内存溢出

历史记录限制 20 条，控制文件大小

输入防抖，避免重复提交

LLM 调用优化
设置超时机制（8秒）

失败自动降级到传统模式

提示词优化，提高准确率

🐛 常见问题
Q: Ollama 连接失败？

A: 检查 Ollama 服务是否运行：

bash

ollama serve

ollama list  # 查看已安装模型（或者直接打开ollama看自己有哪些模型）

Q: 向量库加载失败？

A: 删除 faiss_idioms 文件夹，让程序重新构建：

RAG

rm -rf faiss_idioms

python app.py


Q: 成语文件找不到？

A: 确保 idioms.txt 在项目根目录，格式正确（每行一个四字成语）


Q: 历史记录不显示？

A: 检查控制台错误信息，确保 game_history.json 文件可写


Q: 端口被占用？

A: 修改 cyjl.py 中的端口号：

python

app.run(debug=True, host='127.0.0.1', port=5001)  # 改为其他端口



📈 未来改进
多人联机对战模式

成语难度分级系统

排行榜和成就系统

成语释义和学习功能

WebSocket 实时通信

Docker 容器化部署

支持更多 LLM 模型（GPT、Claude 等）

语音输入支持
