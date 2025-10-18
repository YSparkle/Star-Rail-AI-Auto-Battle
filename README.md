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

### 运行程序

```bash
python main.py
```

## 📁 项目结构

```
Star-Rail-AI-Auto-Battle/
├── src/
│   ├── image_recognition/    # 图像识别模块
│   │   ├── __init__.py
│   │   └── recognizer.py
│   ├── decision_engine/      # AI决策引擎
│   │   ├── __init__.py
│   │   └── decision.py
│   ├── game_control/         # 游戏控制模块
│   │   ├── __init__.py
│   │   └── controller.py
│   └── __init__.py
├── docs/                     # 项目文档
│   └── 新手入门指南.md
├── main.py                   # 主程序入口
├── requirements.txt          # 依赖包列表
├── PROJECT_PLAN.md          # 项目计划
└── README.md                # 本文件
```

## 🔧 核心功能

- **图像识别**: 基于 OpenCV 的游戏界面识别
- **智能决策**: 基于规则的战斗策略系统
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

---

## ⚙️ 配置 AI 提供商与系统提示词

程序首次运行会在 config/config.json 生成配置模板，你也可以手动编辑该文件：

- ai.provider: 可选 mock/openai/azure/ollama/custom
- ai.api_key: 你的 API Key（如果需要）
- ai.base_url: API 基础地址（OpenAI 兼容或自定义 JSON 接口）
- ai.model: 模型名称（如 gpt-4o-mini/llama3 等）
- ai.system_prompt: 系统提示词（用于指导 AI 制定策略）

示例：

```
{
  "ai": {
    "provider": "openai",
    "api_key": "sk-...",
    "base_url": "https://api.openai.com/v1/chat/completions",
    "model": "gpt-4o-mini",
    "system_prompt": "你是星穹铁道战斗策划AI。根据队伍与敌人信息制定最优策略。"
  },
  "mode": "material_farm",
  "allow_rng_fishing": true
}
```

## 🎮 模式与策略（按模式分别设计）

- material_farm（刷材料）：追求少轮数与高节奏，提供两轮/三轮等方案。
- abyss（深渊）：结合关卡 buff 制定最少轮数的稳定/可凹方案。

程序会：
1. 引导你手动打开星铁并切换到目标模式；
2. 读取 config 中的队伍与敌人信息，计算有效面板；
3. 生成多套策略方案（本地结构化+AI 文本建议），供你选择；
4. 你可以选择是否“凹”（让怪物打到指定角色以回能等）。

## 🧠 记忆与数据保存

- 默认开启持久化（config.persist_memory=true），数据写入 game_data/memory.json：
  - 上次队伍/敌人信息
  - AI 文本建议
  - 用户选择的方案

## 🧩 队伍与遗器输入

在 config/config.json 填写队伍数据（角色、光锥、遗器、天赋等），程序会计算有效面板：

```
"team": {
  "characters": [
    {
      "name": "丹恒•饮月",
      "path": "毁灭",
      "element": "冰",
      "level": 80,
      "eidolons": 0,
      "light_cone": {"name": "某某光锥", "level": 80, "superimpose": 1, "stats": {"atk": 0, "hp": 0, "def": 0, "spd": 0, "crit_rate": 0.0, "crit_dmg": 0.0}},
      "base_stats": {"atk": 1000, "hp": 5000, "def": 600, "spd": 120, "crit_rate": 0.05, "crit_dmg": 0.5, "break_effect": 0.0, "energy_regen": 1.0},
      "relics": {"sets": ["冰套2", "攻击2"], "stats": {"atk": 500, "spd": 12, "crit_rate": 0.2, "crit_dmg": 0.5}},
      "traces": {"atk_pct": 0.0, "hp_pct": 0.0, "def_pct": 0.0, "crit_rate": 0.0, "crit_dmg": 0.0, "spd": 0}
    }
  ]
}
```

敌人信息（包含弱点与关卡 BUFF）：

```
"enemies": {"name": "某某", "level": 80, "count": 3, "weakness": ["冰"], "base_stats": {"hp": 20000, "def": 1000}, "special_buffs": []}
"abyss": {"buffs": [{"type": "增伤", "value": 0.2, "desc": "冻结伤害+20%"}]}
```
