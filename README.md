# 星穹铁道 AI 自动战斗系统

基于AI视觉识别和智能决策的《崩坏：星穹铁道》自动战斗系统。

## ✨ 核心特性

### 🤖 AI驱动
- **智能识别**：AI直接识别游戏画面，无需复杂OCR配置
- **策略生成**：根据角色和敌人信息，生成最优战斗方案
- **实时决策**：战斗中AI实时分析画面并做出决策

### 🎯 多模式支持
- **刷材料模式**：追求快速通关
- **深渊模式**：根据buff和机制制定最少回合数计划
- **自定义模式**：灵活调整策略

### 🎮 游戏操作
- **1-4**：释放对应位置角色的大招
- **Q**：普通攻击
- **E**：战技（每个角色效果不同，AI自动判断）
- **左/右方向键**：切换目标
- 所有按键可自定义

### 🔄 凹本支持
- 方案A：稳定通关，不依赖凹本
- 方案B：极限通关，支持设计凹本策略
- 用户可选择是否凹本，AI提供详细条件

## 📦 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置AI
复制配置文件：
```bash
cp config.example.json config.json
```

编辑 `config.json`，填写API信息：
```json
{
  "ai": {
    "enabled": true,
    "api_key": "你的API密钥",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini"
  }
}
```

支持的API：OpenAI、DeepSeek、硅基流动等兼容OpenAI格式的服务

### 3. 配置UI区域
根据游戏分辨率调整 `ui_regions` 坐标（详见 [USAGE_GUIDE.md](USAGE_GUIDE.md)）

### 4. 运行

**仅扫描模式**（识别角色和敌人信息）：
```json
{"run": {"scan_only": true}}
```
```bash
python main.py
```

**仅规划模式**（生成战斗策略）：
```json
{"run": {"plan_only": true}}
```
```bash
python main.py
```

**自动战斗模式**（完整流程）：
```json
{
  "run": {"plan_only": false},
  "input": {"enable_inputs": true},
  "preferences": {"selected_option": "A"}
}
```
```bash
python main.py
```

## 📖 详细文档

- [使用指南](USAGE_GUIDE.md) - 详细的使用说明
- [AI功能说明](README_AI.md) - AI特性和工作原理

## 🎯 使用流程

```
1. 扫描角色和敌人
   ↓
2. AI生成战斗策略
   ├─ 方案A（稳定）
   └─ 方案B（极限）
   ↓
3. 用户选择方案
   ↓
4. AI自动战斗
```

## 🔒 安全特性

- ✅ 输入默认禁用，需手动启用
- ✅ 危险按键自动拦截（Ctrl/Alt/Win等）
- ✅ 随时可按Ctrl+C停止
- ✅ 确认机制，防止误操作

## 🎨 GUI界面

运行图形界面：
```bash
python app.py
```

提供：
- AI配置界面
- 按键设置
- 扫描控制
- 策略查看

## 📁 项目结构

```
.
├── main.py                 # 主程序入口
├── app.py                  # GUI程序入口
├── config.json            # 配置文件
├── src/
│   ├── ai/                # AI模块
│   │   ├── client.py      # AI客户端
│   │   └── strategy_engine.py  # AI策略引擎
│   ├── decision_engine/   # 决策引擎
│   │   └── ai_decision.py # AI决策
│   ├── game_control/      # 游戏控制
│   │   └── controller.py  # 键鼠控制
│   └── image_recognition/ # 图像识别
│       └── scanner.py     # UI扫描
└── data/
    └── memory/           # AI记忆存储
```

## 🌟 核心优势

### vs 传统OCR方案
- ❌ 传统OCR：需要大量模板匹配，识别率低
- ✅ AI视觉：直接理解画面内容，准确率高

### vs 硬编码规则
- ❌ 硬编码：角色/敌人变化需要重新编程
- ✅ AI决策：自动理解角色技能和敌人机制

### vs 固定流程
- ❌ 固定流程：无法应对突发情况
- ✅ 实时决策：动态调整策略

## 🔧 自定义

### 按键映射
```json
{
  "input": {
    "keybinds": {
      "basic_attack": "q",
      "skill": "e",
      "ultimate_1": "1",
      "ultimate_2": "2",
      "ultimate_3": "3",
      "ultimate_4": "4"
    }
  }
}
```

### 凹本设置
```json
{
  "preferences": {
    "allow_reroll": true,
    "reroll_settings": {
      "max_retries": 5,
      "bait_target": "希儿",
      "bait_condition": "第一回合被单体攻击",
      "purpose": "回能触发反击"
    }
  }
}
```

## ⚠️ 注意事项

1. **首次使用**：建议先用仅规划模式测试AI的策略
2. **游戏更新**：界面变化可能需要重新配置ui_regions
3. **API成本**：使用AI需要调用API，注意成本控制
4. **合规性**：仅供学习研究，请遵守游戏服务条款

## 🐛 故障排除

### AI无法连接
- 检查API密钥和base_url
- 检查网络连接
- 增加timeout时间

### 扫描失败
- 确保游戏在前台
- 检查ui_regions坐标
- 查看日志中的错误信息

### 按键无效
- 确保 `enable_inputs: true`
- 检查游戏是否在前台
- 查看安全拦截日志

详细解决方案见 [USAGE_GUIDE.md](USAGE_GUIDE.md)

## 📝 技术栈

- **Python 3.12+**
- **OpenCV**: 图像处理
- **PyAutoGUI**: 屏幕操作
- **AI API**: GPT-4/DeepSeek等视觉模型
- **tkinter**: GUI界面

## 🤝 贡献

欢迎提交问题和改进建议！

特别欢迎：
- 不同分辨率的UI配置
- 角色/敌人测试结果
- 策略优化建议
- Bug修复

## 📄 许可

本项目仅供学习研究使用。

---

**⚡ 开始使用：**
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置API
cp config.example.json config.json
# 编辑 config.json 填写 API 密钥

# 3. 运行
python main.py
```

更多信息请查看 [使用指南](USAGE_GUIDE.md)
