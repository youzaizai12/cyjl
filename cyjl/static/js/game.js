class IdiomGame {
    constructor() {
        this.gameState = null;
        this.useOllama = true;
        this.gameHistory = [];
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.checkOllamaStatus();
        await this.loadHistory();
    }

    bindEvents() {
        document.getElementById('newGameBtn').addEventListener('click', () => this.startNewGame());
        document.getElementById('submitBtn').addEventListener('click', () => this.submitMove());
        document.getElementById('surrenderBtn').addEventListener('click', () => this.surrender());
        document.getElementById('clearHistoryBtn').addEventListener('click', () => this.clearHistory());
        document.getElementById('playAgainBtn').addEventListener('click', () => {
            document.getElementById('gameOverModal').style.display = 'none';
            this.startNewGame();
        });
        
        document.getElementById('idiomInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.submitMove();
        });
    }

    async checkOllamaStatus() {
        try {
            const response = await fetch('/api/ollama/status');
            const data = await response.json();
            if (!data.available) {
                this.addMessage('⚠️ Ollama服务未运行，将使用传统模式', 'error');
                document.getElementById('aiModeSelect').value = 'traditional';
            } else {
                this.addMessage('✅ Ollama已连接，可以使用智能模式', 'success');
            }
        } catch (error) {
            console.error('检查Ollama状态失败:', error);
        }
    }

    async startNewGame() {
        const firstPlayer = document.getElementById('firstPlayerSelect').value;
        const aiMode = document.getElementById('aiModeSelect').value;
        this.useOllama = (aiMode === 'ollama');
        
        const messageArea = document.getElementById('messageArea');
        messageArea.innerHTML = '<div class="message-item welcome">游戏开始！等待出招...</div>';
        document.getElementById('idiomInput').value = '';
        
        try {
            const response = await fetch('/api/init', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    first_player: firstPlayer,
                    use_ollama: this.useOllama
                })
            });
            const data = await response.json();
            
            if (data.success) {
                this.gameState = data.game_state;
                this.updateUI();
                
                const modeText = this.useOllama ? '🧠 智能模式' : '📚 传统模式';
                
                if (data.ai_move) {
                    this.addMessage(`🤖 AI先出：【${data.ai_move}】`, 'ai');
                    this.addMessage(`🎮 轮到你了！请接「${data.ai_move.slice(-1)}」字开头的成语`, 'welcome');
                } else {
                    this.addMessage(`${modeText}，请你先出一个四字成语。`, 'welcome');
                }
            }
        } catch (error) {
            console.error('初始化游戏失败:', error);
            this.addMessage('初始化游戏失败，请刷新页面重试！', 'error');
        }
    }

    async submitMove() {
        if (!this.gameState || !this.gameState.game_active) {
            this.addMessage('⚠️ 游戏未开始，请点击"新游戏"！', 'error');
            return;
        }

        if (this.gameState.turn !== 'player') {
            this.addMessage('⏳ 请等待AI出招...', 'error');
            return;
        }

        const idiomInput = document.getElementById('idiomInput');
        const idiom = idiomInput.value.trim();
        
        if (!idiom) {
            this.addMessage('📝 请输入成语！', 'error');
            return;
        }

        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = true;
        submitBtn.textContent = '提交中...';
        
        try {
            const response = await fetch('/api/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    idiom: idiom,
                    use_ollama: this.useOllama
                })
            });
            const data = await response.json();
            
            if (data.success) {
                idiomInput.value = '';
                this.gameState = data.game_state;
                this.updateUI();
                
                if (data.player_move) {
                    this.addMessage(`👤 你出：【${data.player_move}】`, 'player');
                }
                
                if (data.ai_move) {
                    this.addMessage(`🤖 AI接：【${data.ai_move}】`, 'ai');
                    this.addMessage(`🎮 轮到你了！请接「${data.ai_move.slice(-1)}」字开头的成语`, 'welcome');
                }
                
                if (data.game_over) {
                    if (data.winner === 'player') {
                        this.addMessage('🎉 恭喜你赢了！太厉害了！', 'success');
                        this.showGameOver('🎉 恭喜获胜！\n你的成语储备真丰富！');
                    } else {
                        this.addMessage('😢 AI赢了！再接再厉！', 'error');
                        this.showGameOver('😢 惜败！\n继续加油！');
                    }
                    await this.loadHistory();
                }
            } else {
                this.addMessage(`❌ ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('提交失败:', error);
            this.addMessage('网络错误，请重试！', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = '出招';
            idiomInput.focus();
        }
    }

    async surrender() {
        if (!this.gameState || !this.gameState.game_active) {
            this.addMessage('⚠️ 游戏未开始！', 'error');
            return;
        }
        
        if (this.gameState.turn !== 'player') {
            this.addMessage('⏳ 现在不是你的回合，无法认输！', 'error');
            return;
        }
        
        const confirmSurrender = confirm('确定要认输吗？');
        if (!confirmSurrender) return;
        
        try {
            const response = await fetch('/api/surrender', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            
            if (data.success) {
                this.gameState = data.game_state;
                this.updateUI();
                this.addMessage('🏳️ 你认输了！AI获胜！', 'error');
                this.showGameOver('😢 你认输了！\n下次再接再厉！');
                await this.loadHistory();
            }
        } catch (error) {
            console.error('认输失败:', error);
            this.addMessage('认输失败，请重试！', 'error');
        }
    }

    updateUI() {
        if (!this.gameState) return;
        
        const currentIdiomSection = document.getElementById('currentIdiomSection');
        const currentIdiomElem = document.getElementById('currentIdiom');
        const nextCharElem = document.getElementById('nextChar');
        const inputArea = document.getElementById('inputArea');
        
        if (this.gameState.current_idiom) {
            currentIdiomSection.style.display = 'block';
            currentIdiomElem.textContent = this.gameState.current_idiom;
            nextCharElem.textContent = this.gameState.last_char;
        } else {
            currentIdiomSection.style.display = 'none';
        }
        
        if (this.gameState.game_active && this.gameState.turn === 'player') {
            inputArea.style.display = 'block';
        } else {
            inputArea.style.display = 'none';
        }
        
        const turnIndicator = document.getElementById('turnIndicator');
        if (this.gameState.game_active) {
            if (this.gameState.turn === 'player') {
                turnIndicator.innerHTML = '<span class="turn-text">🎮 你的回合</span>';
            } else {
                turnIndicator.innerHTML = '<span class="turn-text">🤖 AI思考中...</span>';
            }
        } else {
            turnIndicator.innerHTML = '<span class="turn-text">🏆 游戏结束</span>';
        }
        
        this.updateUsedIdioms();
    }

    updateUsedIdioms() {
        const container = document.getElementById('usedIdiomsList');
        if (!this.gameState.used_idioms || this.gameState.used_idioms.length === 0) {
            container.innerHTML = '<div class="empty-message">暂无</div>';
            return;
        }
        
        container.innerHTML = this.gameState.used_idioms
            .map(idiom => `<div class="idiom-tag">${idiom}</div>`)
            .join('');
    }

    async loadHistory() {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            if (data.success && data.history) {
                this.gameHistory = data.history;
                this.displayHistory(this.gameHistory);
                console.log('历史记录加载成功:', this.gameHistory.length, '条');
            } else {
                this.displayHistory([]);
            }
        } catch (error) {
            console.error('加载历史记录失败:', error);
            this.displayHistory([]);
        }
    }

    displayHistory(history) {
        const container = document.getElementById('historyList');
        if (!history || history.length === 0) {
            container.innerHTML = '<div class="empty-message">暂无游戏记录</div>';
            return;
        }
        
        container.innerHTML = history.map(record => `
            <div class="history-item">
                <div class="history-time">📅 ${record.timestamp}</div>
                <div class="history-info">
                    <div>
                        <span class="history-winner ${record.winner === 'player' ? 'winner-player' : 'winner-ai'}">
                            ${record.winner === 'player' ? '👤 玩家胜' : '🤖 AI胜'}
                        </span>
                    </div>
                    <div class="history-stats">
                        📊 共 ${record.total_moves} 步 | 🎲 先手: ${record.first_player === 'player' ? '玩家' : 'AI'}
                    </div>
                    <button class="history-detail-btn" onclick="game.showGameDetail('${record.game_id}')">
                        📖 查看详情
                    </button>
                </div>
            </div>
        `).join('');
    }

    showGameDetail(gameId) {
        const record = this.gameHistory.find(r => r.game_id === gameId);
        if (record) {
            let detailText = '📝 出招记录：\n\n';
            detailText += '👤 玩家：\n';
            record.player_moves.forEach((move, i) => {
                detailText += `  ${i+1}. ${move}\n`;
            });
            detailText += '\n🤖 AI：\n';
            record.ai_moves.forEach((move, i) => {
                detailText += `  ${i+1}. ${move}\n`;
            });
            alert(detailText);
        } else {
            alert('找不到游戏记录');
        }
    }

    async clearHistory() {
        if (confirm('⚠️ 确定要清空所有历史记录吗？')) {
            try {
                const response = await fetch('/api/clear_history', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    this.gameHistory = [];
                    await this.loadHistory();
                    this.addMessage('🗑️ 历史记录已清空', 'success');
                }
            } catch (error) {
                console.error('清空历史记录失败:', error);
                this.addMessage('清空历史记录失败', 'error');
            }
        }
    }

    addMessage(message, type) {
        const messageArea = document.getElementById('messageArea');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-item ${type}`;
        messageDiv.textContent = message;
        messageArea.appendChild(messageDiv);
        messageArea.scrollTop = messageArea.scrollHeight;
        
        while (messageArea.children.length > 100) {
            messageArea.removeChild(messageArea.firstChild);
        }
    }

    showGameOver(message) {
        const modal = document.getElementById('gameOverModal');
        const msgElem = document.getElementById('gameOverMessage');
        msgElem.innerHTML = message;
        modal.style.display = 'block';
    }
}

let game;
document.addEventListener('DOMContentLoaded', () => {
    game = new IdiomGame();
    window.game = game;
});