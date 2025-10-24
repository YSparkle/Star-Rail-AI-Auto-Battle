# 星穹铁道 AI 自动战斗系统 - 使用指南

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- `opencv-python`: 图像处理
- `pillow`: 图像操作
- `pyautogui`: 屏幕截图和键鼠控制
- `pynput`: 键鼠事件
- `requests`: HTTP请求（AI API）

### 2. 配置API

复制配置示例：
```bash
cp config.example.json config.json
```

编辑 `config.json`，填写你的AI API信息：

```json
{
  "ai": {
    "enabled": true,
    "provider": "openai_compatible",
    "api_key": "你的API密钥",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
    "timeout": 120
  }
}
```

**支持的API提供商：**
- OpenAI: `base_url: "https://api.openai.com/v1"`
- DeepSeek: `base_url: "https://api.deepseek.com/v1"`
- 硅基流动: `base_url: "https://api.siliconflow.cn/v1"`
- 其他兼容OpenAI格式的API

### 3. 配置UI区域

根据你的游戏分辨率，调整 `ui_regions`：

```json
{
  "ui_regions": {
    "character_stats": [100, 100, 400, 300],
    "skill_buttons": [[300, 800], [420, 800], [540, 800], [660, 800]],
    "skill_detail_region": [600, 200, 600, 600],
    "enemy_panel": [1000, 100, 400, 300],
    "detail_button": [800, 400]
  }
}
```

**如何确定坐标：**
1. 打开游戏，进入角色详情界面
2. 运行 `python -m pyautogui.mouseInfo` 查看鼠标位置
3. 记录各个UI元素的坐标

## 使用流程

### 模式1：仅扫描角色和敌人

这个模式会让AI识别游戏界面，提取角色和敌人的完整信息。

**配置：**
```json
{
  "run": {
    "scan_only": true
  },
  "roster": [
    {"name": "希儿", "element": "Quantum", "path": "Hunt"},
    {"name": "布洛妮娅", "element": "Wind", "path": "Harmony"}
  ],
  "enemy": {
    "name": "虚无之影"
  }
}
```

**运行：**
```bash
python main.py
```

**操作步骤：**
1. 程序启动后，会提示你打开角色详情界面
2. 等待2秒后，AI会开始扫描第一个角色
3. AI会自动点击技能按钮，查看详细描述
4. 重复扫描所有角色
5. 打开敌人信息界面，扫描敌人
6. 所有信息保存到 `data/memory/` 目录

**输出示例：**
```
✓ 角色 希儿 扫描完成
  属性：{'atk': 2100, 'hp': 8500, 'spd': 115, 'crit_rate': 0.75, ...}
  技能数：4
```

### 模式2：生成战斗策略

这个模式会在扫描后，让AI分析并生成战斗策略。

**配置：**
```json
{
  "run": {
    "plan_only": true
  },
  "mode": "material_farm",
  "preferences": {
    "allow_reroll": true,
    "selected_option": null
  }
}
```

**战斗模式：**
- `material_farm`: 刷材料，追求快速
- `abyss`: 深渊，追求最少回合
- `custom`: 自定义

**运行：**
```bash
python main.py
```

**AI会生成：**

1. **战斗分析**
   - 伤害计算
   - 速度轮次
   - 队伍协同

2. **方案A（稳定）**
   - 不依赖凹本
   - 详细步骤
   - 预计回合数

3. **方案B（极限）**
   - 追求最少回合
   - 凹本条件（如果允许）
   - 详细步骤

**输出示例：**
```
【方案A - 稳定】
  名称：稳定三回合通关
  预计回合数：3

【方案B - 极限】
  名称：极限二回合通关
  预计回合数：2
  需要凹本：
    - 目标角色：希儿
    - 触发时机：第一回合被敌人单体攻击
    - 目的：回能触发反击
    - 最大重试：5
```

### 模式3：自动战斗

完整流程：扫描 → 生成策略 → 自动战斗

**配置：**
```json
{
  "run": {
    "plan_only": false,
    "scan_only": false
  },
  "input": {
    "enable_inputs": true
  },
  "preferences": {
    "selected_option": "A"
  }
}
```

**重要：**
- 必须启用 `enable_inputs: true` 才会发送按键
- 必须选择方案：`selected_option: "A"` 或 `"B"`

**运行：**
```bash
python main.py
```

**操作步骤：**
1. 程序会先扫描角色和敌人（如果还没扫描）
2. AI生成战斗策略
3. 显示方案A和B
4. 在游戏中切换到对应模式界面（刷材料/深渊等）
5. 按回车键确认开始
6. AI开始自动战斗
7. 按 Ctrl+C 可以随时停止

## 自定义按键

在 `config.json` 中：

```json
{
  "input": {
    "keybinds": {
      "basic_attack": "q",
      "skill": "e",
      "ultimate_1": "1",
      "ultimate_2": "2",
      "ultimate_3": "3",
      "ultimate_4": "4",
      "target_left": "left",
      "target_right": "right"
    }
  }
}
```

**按键说明：**
- `basic_attack`: 普通攻击（默认Q）
- `skill`: 战技（默认E），每个角色效果不同
- `ultimate_1~4`: 第1-4个角色的大招（默认1-4）
- `target_left/right`: 切换目标（默认左右方向键）

## GUI界面

运行GUI程序：

```bash
python app.py
```

GUI功能：
- 配置AI API
- 设置按键
- 选择模式
- 扫描控制
- 查看策略

## 凹本设置

如果你想让AI制定包含凹本的策略：

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

AI会在方案B中考虑这些条件。

## 高级用法

### 使用记忆数据

扫描后的数据保存在 `data/memory/` 中：

```
data/memory/
├── character_希儿.json
├── character_布洛妮娅.json
├── enemy_虚无之影.json
└── current_strategy.json
```

如果已经扫描过，可以直接生成策略，无需重新扫描：

```bash
# 设置 scan_only: false, plan_only: true
python main.py
```

### 批量测试不同队伍

编写脚本测试不同配置：

```python
import json
from main import StarRailAutoBattle

configs = [
    {"roster": [...]},  # 配置1
    {"roster": [...]},  # 配置2
]

for i, cfg in enumerate(configs):
    with open('config.json', 'w') as f:
        json.dump(cfg, f)
    
    auto = StarRailAutoBattle()
    auto.initialize()
    auto.generate_strategy()
```

### 自定义策略

如果要实现特殊模式的策略，可以在 `src/strategy/` 中添加：

```python
from src.strategy.base import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def plan(self, context):
        # 你的策略逻辑
        pass
```

然后在配置中注册。

## 常见问题

### Q: AI识别不准确？
A: 
1. 检查游戏分辨率与ui_regions配置是否匹配
2. 尝试使用更强大的模型（如GPT-4）
3. 调整vision_prompt，提供更详细的提示

### Q: 按键没反应？
A:
1. 确保 `enable_inputs: true`
2. 确保游戏在前台
3. 检查日志中的安全拦截信息

### Q: AI生成的策略不合理？
A:
1. 确保扫描的信息准确
2. 在system_prompt中提供更多游戏机制说明
3. 手动补充config中的详细信息

### Q: 扫描时卡住？
A:
1. 检查是否正确打开了界面
2. 检查ui_regions坐标是否正确
3. 查看日志中的错误信息

### Q: API超时？
A:
1. 增加timeout时间（如120秒）
2. 使用更快的API提供商
3. 减少一次发送的图片数量

## 安全提示

1. **输入控制**：默认情况下输入是关闭的，需要手动启用
2. **按键过滤**：系统会自动拦截危险按键组合
3. **随时停止**：按 Ctrl+C 可以立即停止
4. **测试建议**：首次使用建议先用仅规划模式测试

## 性能优化

### 减少API调用
1. 使用记忆数据，避免重复扫描
2. 预先生成策略，战斗时只做实时决策

### 提高识别速度
1. 使用本地部署的模型
2. 优化图片大小和质量
3. 减少扫描区域

### 控制决策频率
在 `battle_loop()` 中调整sleep时间：

```python
time.sleep(0.5)  # 每0.5秒决策一次
```

## 项目结构

```
star-rail-ai-auto-battle/
├── main.py                 # 主程序
├── app.py                  # GUI程序
├── config.json            # 配置文件
├── data/
│   ├── memory/           # AI记忆存储
│   └── screenshots/      # 截图
└── src/
    ├── ai/               # AI模块
    │   ├── client.py     # AI客户端
    │   └── strategy_engine.py  # 策略引擎
    ├── decision_engine/  # 决策引擎
    ├── game_control/     # 游戏控制
    └── image_recognition/  # 图像识别
```

## 贡献

欢迎提交问题和改进建议！

特别欢迎：
- 不同游戏分辨率的UI配置
- 各种角色的测试结果
- 策略优化建议
- Bug修复

## 许可

本项目仅供学习研究使用，请勿用于违反游戏服务条款的行为。
