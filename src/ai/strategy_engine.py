"""
AI策略引擎
- 通过视觉识别游戏界面
- 理解角色和敌人的所有信息（包括技能详情）
- 制定最优战斗策略
- 实时战斗决策
"""
from __future__ import annotations

import base64
import io
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    from PIL import Image
except ImportError:
    Image = None

# Lazy import pyautogui to avoid display issues
pyautogui = None


@dataclass
class CharacterInfo:
    """角色完整信息"""
    name: str
    element: str
    path: str
    level: int
    stats: Dict[str, float]  # 所有属性值
    skills: List[Dict[str, Any]]  # 技能列表（包含详细描述）
    raw_data: Dict[str, Any]  # 原始识别数据


@dataclass
class EnemyInfo:
    """敌人完整信息"""
    name: str
    level: int
    stats: Dict[str, float]
    weaknesses: List[str]
    resistances: Dict[str, float]
    buffs: List[str]
    raw_data: Dict[str, Any]


@dataclass
class BattleAction:
    """战斗动作"""
    action_type: str  # "ultimate", "skill", "basic_attack", "switch_target_left", "switch_target_right", "wait"
    character_index: Optional[int] = None  # 1-4，用于大招
    target_direction: Optional[str] = None  # "left", "right"
    reasoning: str = ""  # AI的决策理由


class AIStrategyEngine:
    """AI驱动的策略引擎"""
    
    def __init__(self, ai_client, game_controller, memory_store, logger=None):
        """
        Args:
            ai_client: AI客户端（支持视觉识别）
            game_controller: 游戏控制器
            memory_store: 记忆存储
            logger: 日志记录器
        """
        self.ai = ai_client
        self.ctrl = game_controller
        self.memory = memory_store
        self.logger = logger or logging.getLogger(__name__)
        
        # 缓存的角色和敌人信息
        self.characters: List[CharacterInfo] = []
        self.enemies: List[EnemyInfo] = []
        self.battle_context: Dict[str, Any] = {}
        
    def screenshot_to_base64(self, region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """截图并转为base64"""
        global pyautogui
        if pyautogui is None:
            try:
                import pyautogui as pag
                pyautogui = pag
            except ImportError:
                raise RuntimeError("需要安装 pyautogui")
        
        if region:
            img = pyautogui.screenshot(region=region)
        else:
            img = pyautogui.screenshot()
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    def scan_character_with_ai(self, name: str, element: str, path: str, 
                               ui_regions: Dict[str, Any]) -> CharacterInfo:
        """
        使用AI扫描角色信息
        1. 截取角色面板
        2. 点击每个技能按钮并截图（粗略描述和详细描述）
        3. AI分析所有截图，提取完整信息
        """
        self.logger.info(f"开始扫描角色：{name}")
        
        # 截取基础属性面板
        char_region = ui_regions.get("character_stats", [100, 100, 400, 300])
        stats_img = self.screenshot_to_base64(tuple(char_region))
        
        # 扫描技能
        skill_buttons = ui_regions.get("skill_buttons", [])
        skill_images = []
        
        for i, (x, y) in enumerate(skill_buttons):
            self.logger.info(f"扫描技能 {i+1}/{len(skill_buttons)}")
            
            # 点击技能按钮
            self.ctrl.move_to(x, y, duration=0.2)
            self.ctrl.click()
            time.sleep(0.5)
            
            # 截取粗略描述
            skill_region = ui_regions.get("skill_detail_region", [600, 200, 600, 600])
            brief_img = self.screenshot_to_base64(tuple(skill_region))
            skill_images.append(("brief", brief_img))
            
            # 如果有详情按钮，点击查看详细描述
            detail_button = ui_regions.get("detail_button")
            if detail_button:
                self.ctrl.move_to(detail_button[0], detail_button[1], duration=0.2)
                self.ctrl.click()
                time.sleep(0.5)
                detail_img = self.screenshot_to_base64(tuple(skill_region))
                skill_images.append(("detail", detail_img))
            
            # 关闭面板
            self.ctrl.press_key('esc')
            time.sleep(0.3)
        
        # 让AI分析所有截图
        prompt = f"""
请分析《崩坏：星穹铁道》角色"{name}"的信息。

角色基本信息：
- 名称：{name}
- 元素：{element}
- 命途：{path}

我会提供以下截图：
1. 角色属性面板（包含攻击、生命、防御、速度、暴击等所有数值）
2. 每个技能的粗略描述和详细描述

请提取以下信息并以JSON格式输出：
{{
    "stats": {{
        "atk": 数值,
        "hp": 数值,
        "def": 数值,
        "spd": 数值,
        "crit_rate": 数值（小数，如0.50表示50%）,
        "crit_dmg": 数值（小数，如1.20表示120%）,
        "break_effect": 数值,
        "energy_regen": 数值,
        "effect_hit": 数值,
        "effect_res": 数值
    }},
    "skills": [
        {{
            "name": "技能名称",
            "type": "basic/skill/ultimate/talent/technique",
            "brief_description": "简短描述",
            "detailed_description": "详细描述（包含所有数值、倍率、效果）",
            "energy_cost": 能量消耗（如果是大招）,
            "cooldown": 冷却时间（如果有）,
            "effects": ["效果1", "效果2", ...]
        }}
    ]
}}

注意：
1. 仔细阅读所有数值，包括百分比
2. 技能描述要完整，包括所有倍率和特殊效果
3. 不要遗漏任何重要信息
4. 如果某些信息不确定，可以标注为null
"""
        
        # 发送所有图片给AI
        all_images = [stats_img] + [img for _, img in skill_images]
        
        try:
            response = self.ai.chat_vision(all_images, prompt, temperature=0.1)
            self.logger.debug(f"AI响应: {response}")
            
            # 解析JSON响应
            # 尝试提取JSON（有些模型会在代码块中返回）
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            data = json.loads(json_str)
            
            char_info = CharacterInfo(
                name=name,
                element=element,
                path=path,
                level=80,  # 默认值，可从UI读取
                stats=data.get("stats", {}),
                skills=data.get("skills", []),
                raw_data=data
            )
            
            # 保存到记忆
            self.memory.save(f"character_{name}", {
                "name": name,
                "element": element,
                "path": path,
                "stats": char_info.stats,
                "skills": char_info.skills,
                "scanned_at": time.time()
            })
            
            return char_info
            
        except Exception as e:
            self.logger.error(f"AI分析角色信息失败: {e}")
            raise
    
    def scan_enemy_with_ai(self, name: str, ui_regions: Dict[str, Any]) -> EnemyInfo:
        """使用AI扫描敌人信息"""
        self.logger.info(f"开始扫描敌人：{name}")
        
        enemy_region = ui_regions.get("enemy_panel", [1000, 100, 400, 300])
        enemy_img = self.screenshot_to_base64(tuple(enemy_region))
        
        prompt = f"""
请分析《崩坏：星穹铁道》敌人"{name}"的信息。

请提取以下信息并以JSON格式输出：
{{
    "level": 等级,
    "stats": {{
        "hp": 生命值,
        "def": 防御力,
        "spd": 速度,
        "toughness": 韧性值
    }},
    "weaknesses": ["弱点元素1", "弱点元素2", ...],
    "resistances": {{"元素": 抗性值（小数）}},
    "buffs": ["增益/机制描述1", "增益/机制描述2", ...]
}}

注意：
1. 弱点元素包括：Physical, Fire, Ice, Lightning, Wind, Quantum, Imaginary
2. 抗性为负数表示易伤，正数表示抗性
3. buffs包括特殊机制、环境增益等
"""
        
        try:
            response = self.ai.chat_vision([enemy_img], prompt, temperature=0.1)
            
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            data = json.loads(json_str)
            
            enemy_info = EnemyInfo(
                name=name,
                level=data.get("level", 90),
                stats=data.get("stats", {}),
                weaknesses=data.get("weaknesses", []),
                resistances=data.get("resistances", {}),
                buffs=data.get("buffs", []),
                raw_data=data
            )
            
            # 保存到记忆
            self.memory.save(f"enemy_{name}", {
                "name": name,
                "level": enemy_info.level,
                "stats": enemy_info.stats,
                "weaknesses": enemy_info.weaknesses,
                "resistances": enemy_info.resistances,
                "buffs": enemy_info.buffs,
                "scanned_at": time.time()
            })
            
            return enemy_info
            
        except Exception as e:
            self.logger.error(f"AI分析敌人信息失败: {e}")
            raise
    
    def generate_strategy(self, mode: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成战斗策略
        
        Args:
            mode: 战斗模式（material_farm, abyss, custom等）
            preferences: 用户偏好（是否允许凹本等）
        
        Returns:
            策略字典，包含多个可选方案
        """
        self.logger.info(f"生成策略：模式={mode}")
        
        # 准备上下文
        context = {
            "mode": mode,
            "preferences": preferences,
            "characters": [
                {
                    "name": c.name,
                    "element": c.element,
                    "path": c.path,
                    "stats": c.stats,
                    "skills": c.skills
                }
                for c in self.characters
            ],
            "enemies": [
                {
                    "name": e.name,
                    "level": e.level,
                    "stats": e.stats,
                    "weaknesses": e.weaknesses,
                    "resistances": e.resistances,
                    "buffs": e.buffs
                }
                for e in self.enemies
            ]
        }
        
        # 构建提示词
        mode_descriptions = {
            "material_farm": "刷材料模式：追求快速通关，减少回合数",
            "abyss": "深渊模式：根据buff和敌人机制制定最少回合数计划",
            "custom": "自定义模式：根据具体情况制定策略"
        }
        
        allow_reroll = preferences.get("allow_reroll", True)
        reroll_settings = preferences.get("reroll_settings", {})
        
        prompt = f"""
你是《崩坏：星穹铁道》的顶级战斗策略专家。

战斗模式：{mode_descriptions.get(mode, mode)}
用户偏好：{"允许凹本" if allow_reroll else "不凹本，追求稳定"}

角色队伍：
{json.dumps(context["characters"], ensure_ascii=False, indent=2)}

敌人信息：
{json.dumps(context["enemies"], ensure_ascii=False, indent=2)}

请根据以上信息，制定最优战斗策略。注意：

1. **深入分析**：
   - 计算每个角色的实际伤害（考虑属性、暴击、增伤等）
   - 分析速度轮次，确定行动顺序
   - 考虑弱点击破、能量恢复、buff/debuff时机
   - 评估敌人的威胁和最优击杀顺序

2. **按键说明**：
   - 1-4：释放对应位置角色的大招（终结技）
   - Q：普通攻击
   - E：战技
   - 左右方向键或鼠标点击：选择目标
   - 注意：每个角色的战技效果不同，不要固化思维！有的是增益，有的是攻击，有的是控制

3. **制定方案**：
   请提供至少2个方案供玩家选择：

   **方案A（稳定）**：
   - 不依赖凹本，追求稳定通关
   - 详细步骤：第X回合，角色Y使用Z技能，目标W
   - 预计回合数
   
   **方案B（极限）**：
   - 追求最少回合数，可以包含凹本操作
   - 如果允许凹本，说明凹点条件：
     * 需要哪个角色被攻击
     * 什么时候被攻击（第几回合，敌人哪个技能）
     * 目的是什么（回能、触发反击等）
     * 如果不满足条件，是否重开
   - 详细步骤
   - 预计回合数

4. **输出格式**（JSON）：
{{
    "analysis": {{
        "damage_calculation": "伤害计算详情",
        "turn_order": "行动顺序分析",
        "synergy": "队伍协同分析",
        "key_points": ["关键点1", "关键点2", ...]
    }},
    "plan_a": {{
        "name": "稳定方案",
        "description": "方案描述",
        "expected_rounds": 预计回合数,
        "steps": [
            {{
                "round": 1,
                "actions": [
                    {{
                        "character": "角色名",
                        "action": "释放大招1" 或 "普攻Q" 或 "战技E",
                        "target": "目标描述" 或 "切换目标（左/右）",
                        "reasoning": "理由"
                    }}
                ]
            }}
        ]
    }},
    "plan_b": {{
        "name": "极限方案",
        "description": "方案描述",
        "expected_rounds": 预计回合数,
        "requires_reroll": true/false,
        "reroll_condition": {{
            "target_character": "被攻击角色",
            "trigger_timing": "触发时机",
            "purpose": "目的",
            "max_retries": 最大重试次数
        }},
        "steps": [...]
    }},
    "recommendation": "推荐方案A还是B，以及理由"
}}
"""
        
        try:
            response = self.ai.chat([{"role": "user", "content": prompt}], temperature=0.2)
            
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            strategy = json.loads(json_str)
            
            # 保存策略
            self.memory.save("current_strategy", strategy)
            
            return strategy
            
        except Exception as e:
            self.logger.error(f"生成策略失败: {e}")
            raise
    
    def make_battle_decision(self, current_round: int, executed_actions: List[Dict]) -> BattleAction:
        """
        实时战斗决策
        
        Args:
            current_round: 当前回合数
            executed_actions: 已执行的动作列表
        
        Returns:
            下一步动作
        """
        # 截取当前战斗画面
        battle_img = self.screenshot_to_base64()
        
        # 获取当前策略
        strategy = self.memory.load("current_strategy") or {}
        selected_plan = self.battle_context.get("selected_plan", "plan_a")
        plan = strategy.get(selected_plan, {})
        
        prompt = f"""
当前战斗状态：
- 回合数：{current_round}
- 已执行动作：{json.dumps(executed_actions, ensure_ascii=False)}
- 原定策略：{json.dumps(plan, ensure_ascii=False)}

请查看当前战斗画面，分析：
1. 当前轮到谁行动
2. 各角色和敌人的状态（生命、能量、buff/debuff）
3. 是否需要调整策略

然后决定下一步动作，输出JSON格式：
{{
    "action_type": "ultimate" | "skill" | "basic_attack" | "switch_target_left" | "switch_target_right" | "wait",
    "character_index": 1-4（如果是大招）,
    "target_direction": "left" | "right"（如果是切换目标）,
    "reasoning": "决策理由"
}}
"""
        
        try:
            response = self.ai.chat_vision([battle_img], prompt, temperature=0.1)
            
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            decision = json.loads(json_str)
            
            return BattleAction(
                action_type=decision.get("action_type", "wait"),
                character_index=decision.get("character_index"),
                target_direction=decision.get("target_direction"),
                reasoning=decision.get("reasoning", "")
            )
            
        except Exception as e:
            self.logger.error(f"AI决策失败: {e}，使用默认动作")
            return BattleAction(action_type="basic_attack", reasoning="AI决策失败，默认普攻")
