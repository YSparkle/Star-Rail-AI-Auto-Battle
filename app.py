#!/usr/bin/env python3
"""
图形化启动入口
- 双击 exe 或运行此脚本，将出现一个窗口用于：
  - 配置 AI 提供商 / API Key / 模型 / System Prompt
  - 选择模式（刷材料/深渊/自定义）与偏好（是否凹本、A/B 方案、凹点细节）
  - 粘贴队伍与敌人 JSON，点击“生成策略（仅规划）”后会计算衍生值并保存记忆
  - 可选择启动自动战斗（需玩家先在游戏内切换到对应模式界面）
"""
from src.ui import run_app

if __name__ == "__main__":
    run_app()
