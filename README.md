# 还在修改！没有完工！

# Star-Rail-AI-Auto-Battle

崩坏星穹铁道AI自动战斗系统

## 📖 项目简介

这是一个为《崩坏：星穹铁道》游戏开发的AI自动战斗系统，使用 Python 实现，集成了图像识别、智能决策和游戏控制功能。

## ⚠️ 免责声明

**本项目仅供学习和技术研究使用**
- 请遵守游戏服务条款
- 不要用于商业用途  
- 使用时请注意账号安全
- 作者不承担任何责任

## 🚀 快速开始

### 环境要求
- Python 3.8+
- pip 包管理器
- Git

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/YSparkle/Star-Rail-AI-Auto-Battle.git
cd Star-Rail-AI-Auto-Battle

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 配置（可选，但推荐）

- 复制示例配置：

```bash
cp config.example.json config.json
```

- 修改 config.json 填入你的 AI 提供商与密钥、模式、角色与敌人信息：
  - ai.enabled: 是否启用 AI 生成详细策略
  - ai.provider: openai_compatible 或 custom_http（OpenAI 兼容网关请选择 openai_compatible）
  - ai.api_key: 你的 API Key（不会被提交到版本库，已写入 .gitignore）
  - ai.base_url + ai.model: 兼容网关的基础地址与模型名（当 provider=openai_compatible）
  - ai.endpoint + ai.headers: 自定义 HTTP 提供商的请求地址与额外请求头（当 provider=custom_http）
  - ai.system_prompt: 系统提示词，可自定义要求输出多套策略（稳定/极限等）
  - mode: material_farm（刷材料）、abyss（深渊）或 custom（自定义）
  - preferences.allow_reroll: 是否允许“凹”（为极限回合/更优循环而重试）
  - preferences.selected_option: 选择策略 A（稳定）或 B（极限），不填则仅给出推荐
  - preferences.reroll_settings: 可选，细化“凹”的偏好，如 {"max_retries": 10, "bait_target": "主C示例", "bait_condition": "第一波吃单体"}
  - roster: 角色 + 遗器/光锥/技能等信息（程序会自动计算衍生属性）
  - enemy: 敌人与关卡信息（弱点/祝福/环境增益、可选 resistances/base_stats 等）

### 运行程序

```bash
python main.py
```

程序启动后会：
- 加载配置并计算角色与敌人的衍生属性（速度/估算伤害/弱点等），生成首轮行动顺序与队伍估算，并保存到 data/memory/
- 进行队伍 vs 敌人的契合度分析（元素覆盖、弱点命中比例、敌方对队伍元素平均抗性、队伍速度概况等），在日志中展示
- 按模式生成基础策略（刷材料/深渊/自定义等模式分开设计）
- 若启用 AI，会生成更详细的多方案文本（稳定/极限可选）并保存到 data/memory/，并在日志中提示文案保存路径
- 日志提示你“请手动切换到游戏内目标模式界面”，然后开始自动战斗循环

## 📁 项目结构

```
Star-Rail-AI-Auto-Battle/
├── src/
│   ├── image_recognition/    # 图像识别模块
│   ├── decision_engine/      # 基础决策引擎
│   ├── game_control/         # 游戏控制模块
│   ├── ai/                   # AI 提供商与客户端（自定义 API Key / Base URL / 模型）
│   ├── strategy/             # 分模式策略（刷材料/深渊等，独立设计）
│   ├── storage/              # 本地记忆存储（JSON）
│   ├── models/               # 数据结构与属性计算
│   └── __init__.py
├── config.example.json       # 配置示例（复制为 config.json）
├── main.py                   # 主程序入口
├── requirements.txt          # 依赖包列表
├── PROJECT_PLAN.md           # 项目计划
└── README.md                 # 本文件
```

## 🔧 核心功能

- **图像识别**: 基于 OpenCV 的游戏界面识别
- **智能决策**: 基于规则的战斗策略系统
- **分模式策略**: 刷材料与深渊等模式分别设计策略逻辑
- **AI 策略规划（可选）**: 支持自定义 API 提供商与 Key（OpenAI 兼容网关等），可配置 system prompt，
  自动生成多套方案（稳定/极限“可凹”），供玩家选择
- **本地记忆**: 自动保存角色/敌人与策略数据到 data/memory 便于复用
- **游戏控制**: PyAutoGUI 实现的鼠标键盘模拟
- **日志系统**: 完整的运行日志记录

## 📚 技术栈

- **Python 3.8+**: 主要编程语言
- **OpenCV**: 图像处理和识别
- **PyTorch**: 深度学习框架（规划中）
- **PyAutoGUI**: 自动化控制
- **NumPy & Pandas**: 数据处理
- **scikit-learn**: 机器学习（规划中）

## 📖 文档

- [项目计划](PROJECT_PLAN.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 📄 许可证

MIT License
