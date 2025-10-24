# 星穹铁道 AI 自动战斗系统 - AI驱动版本

## 概述

这是一个基于AI视觉识别和智能决策的《崩坏：星穹铁道》自动战斗系统。系统通过AI直接识别游戏画面，理解角色和敌人信息，制定最优战斗策略，并实时做出战斗决策。

## 核心特性

### 1. AI视觉识别
- **智能扫描**：AI直接识别游戏界面，无需复杂的OCR配置
- **完整信息提取**：自动点击并读取角色技能的详细描述
- **实时画面分析**：战斗中实时识别当前状态

### 2. 智能策略生成
- **多模式支持**：
  - 刷材料模式：追求快速通关，减少回合数
  - 深渊模式：根据buff和机制制定最少回合数计划
  - 自定义模式：根据具体情况灵活调整
- **双方案制定**：
  - 方案A（稳定）：不依赖凹本，追求稳定通关
  - 方案B（极限）：追求最少回合，支持凹本操作
- **用户可选**：AI制定计划后供用户选择，支持自定义是否凹本

### 3. 实时战斗决策
- AI分析当前战斗画面
- 根据策略和实际情况做出最优决策
- 支持动态调整策略

## 按键说明

### 默认按键映射
- **Q**：普通攻击
- **E**：战技（每个角色的战技效果不同，由AI判断如何使用）
- **1-4**：释放对应位置角色的大招（终结技）
  - 1 = 第1个角色大招
  - 2 = 第2个角色大招
  - 3 = 第3个角色大招
  - 4 = 第4个角色大招
- **左/右方向键**：切换攻击目标
- **ESC**：打开菜单
- **Enter**：确认
- **Backspace**：取消

### 自定义按键
所有按键都可以在 `config.json` 的 `input.keybinds` 中自定义。

## 使用流程

### 1. 配置AI

编辑 `config.json`：

```json
{
  "ai": {
    "enabled": true,
    "provider": "openai_compatible",
    "api_key": "你的API密钥",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
    "system_prompt": "你是《崩坏：星穹铁道》的战斗策略专家。",
    "timeout": 120
  }
}
```

支持的API提供商：
- OpenAI
- DeepSeek
- 硅基流动
- 其他兼容OpenAI API的服务

### 2. 配置UI区域

在 `config.json` 中配置游戏界面的区域坐标：

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

### 3. 配置角色和敌人

在 `config.json` 中配置要扫描的角色和敌人：

```json
{
  "roster": [
    {
      "name": "希儿",
      "element": "Quantum",
      "path": "Hunt"
    },
    {
      "name": "布洛妮娅",
      "element": "Wind",
      "path": "Harmony"
    }
  ],
  "enemy": {
    "name": "虚无之影",
    "level": 90
  }
}
```

### 4. 扫描角色和敌人

运行扫描模式：

```bash
python main.py
```

在 `config.json` 中设置：
```json
{
  "run": {
    "scan_only": true
  }
}
```

扫描流程：
1. 程序会提示你打开角色详情界面
2. AI会自动点击技能按钮并截图
3. AI分析所有截图，提取完整信息
4. 扫描敌人信息
5. 所有信息保存到 `data/memory/` 目录

### 5. 生成战斗策略

运行规划模式：

```bash
python main.py
```

在 `config.json` 中设置：
```json
{
  "run": {
    "plan_only": true
  },
  "mode": "material_farm",
  "preferences": {
    "allow_reroll": true,
    "selected_option": "A"
  }
}
```

程序会：
1. 扫描角色和敌人（如果还没扫描）
2. AI分析队伍和敌人信息
3. 计算伤害、速度、行动顺序
4. 生成方案A（稳定）和方案B（极限）
5. 给出推荐

### 6. 启动自动战斗

1. **选择方案**：在 `config.json` 中设置 `preferences.selected_option` 为 "A" 或 "B"

2. **启用输入**：
```json
{
  "input": {
    "enable_inputs": true
  }
}
```

3. **在游戏中切换到对应模式界面**（刷材料/深渊等）

4. **运行完整模式**：
```json
{
  "run": {
    "plan_only": false,
    "scan_only": false
  }
}
```

5. **启动**：
```bash
python main.py
```

6. 按照提示确认后，AI将开始自动战斗

## 运行模式

### scan_only（仅扫描）
只扫描角色和敌人信息，保存到记忆中，不生成策略和战斗。

### plan_only（仅规划）
扫描信息并生成策略，不启动自动战斗。用于预先规划或查看AI的策略建议。

### 完整模式
扫描 → 生成策略 → 自动战斗

## 凹本机制

如果允许凹本（`preferences.allow_reroll: true`），AI会在方案B中设计凹本策略：

```json
{
  "preferences": {
    "allow_reroll": true,
    "reroll_settings": {
      "max_retries": 5,
      "bait_target": "希儿",
      "bait_condition": "第一回合被敌人单体攻击",
      "purpose": "回能触发反击"
    }
  }
}
```

AI会分析：
- 哪个角色需要被攻击
- 什么时候被攻击
- 目的是什么（回能、触发反击、获取buff等）
- 最大重试次数

## 安全机制

### 输入安全开关
- 默认情况下，`enable_inputs` 为 `false`，程序不会发送任何按键
- 只有明确启用后才会操作游戏

### 按键白名单
- 系统只允许安全的按键（字母、数字、方向键、功能键）
- 自动拦截危险组合键（Ctrl、Alt、Win等）

### 确认机制
- 启动自动战斗前需要用户确认
- 随时可以按 Ctrl+C 停止

## 目录结构

```
.
├── config.json              # 主配置文件
├── main.py                  # 主程序入口
├── app.py                   # GUI界面入口
├── data/
│   ├── memory/             # AI记忆存储
│   └── screenshots/        # 截图保存
├── src/
│   ├── ai/
│   │   ├── client.py       # AI客户端
│   │   └── strategy_engine.py  # AI策略引擎
│   ├── decision_engine/
│   │   └── ai_decision.py  # AI决策引擎
│   ├── game_control/
│   │   └── controller.py   # 游戏控制器
│   ├── image_recognition/
│   │   ├── recognizer.py   # 图像识别
│   │   └── scanner.py      # UI扫描器
│   └── storage/
│       └── memory.py       # 记忆存储
```

## GUI界面

运行GUI界面：

```bash
python app.py
```

GUI提供：
- AI配置界面（API密钥、模型等）
- 按键设置
- 模式选择
- 扫描控制
- 策略生成和查看

## 故障排除

### AI无法连接
1. 检查API密钥是否正确
2. 检查网络连接
3. 检查API提供商的base_url是否正确
4. 增加timeout时间

### 扫描失败
1. 确保游戏界面在前台
2. 检查ui_regions坐标是否正确
3. 确保游戏分辨率与配置匹配
4. 尝试手动截图测试

### 按键无效
1. 确保 `enable_inputs` 为 `true`
2. 检查游戏是否在前台
3. 检查按键映射是否正确
4. 查看日志中的安全拦截信息

### AI策略不合理
1. 确保扫描的角色和敌人信息准确
2. 调整system_prompt，提供更详细的指示
3. 尝试不同的模型（如GPT-4）
4. 手动补充config.json中的详细信息

## 高级功能

### 自定义模式策略

可以在 `src/strategy/` 中添加自定义策略类，并在配置中使用。

### 记忆管理

所有扫描数据和策略都保存在 `data/memory/` 中，可以：
- 查看历史策略
- 重用扫描数据
- 分析战斗记录

### 批量测试

可以编写脚本批量测试不同队伍配置的策略。

## 注意事项

1. **首次使用建议**：
   - 先在仅规划模式下测试AI的策略
   - 确认策略合理后再启用自动战斗
   - 初期建议监督运行

2. **游戏更新**：
   - 游戏界面变化可能需要重新配置ui_regions
   - 新角色/敌人需要重新扫描

3. **性能考虑**：
   - AI识图需要一定时间，建议使用较快的API
   - 战斗决策频率可以调整

4. **合规性**：
   - 本工具仅供学习研究使用
   - 使用前请确认不违反游戏服务条款

## 贡献

欢迎提交问题和改进建议！

## 许可证

本项目仅供学习研究使用。
