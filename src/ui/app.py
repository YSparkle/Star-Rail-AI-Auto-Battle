from __future__ import annotations

import json
import os
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, Optional, Tuple

from src.config import load_config
from src.ai import AIClient, AIConfig, AIProviderType
from src.storage.memory import MemoryStore
from src.models.character import character_from_config
from src.models.enemy import enemy_from_config
from src.models.combat import compute_turn_order, summarize_team_estimates, analyze_team_enemy_synergy
from src.strategy import StrategyManager, MaterialFarmStrategy, AbyssStrategy, StrategyContext, CustomStrategy
from src.image_recognition.ocr import OCR, OCRConfig
from src.image_recognition.scanner import (
    UIRegions,
    CharacterScanner,
    EnemyScanner,
    assemble_character_from_scan,
    assemble_enemy_from_scan,
)
from main import StarRailAutoBattle


class AppState:
    def __init__(self):
        self.config: Dict[str, Any] = load_config()
        self.ai_client: Optional[AIClient] = None
        self.memory = MemoryStore()
        self.strategy_manager = StrategyManager({
            "material_farm": MaterialFarmStrategy(),
            "abyss": AbyssStrategy(),
            "custom": CustomStrategy(),
        })
        self.auto: Optional[StarRailAutoBattle] = None

    def ensure_ai(self):
        ai_cfg = self.config.get("ai", {})
        try:
            cfg = AIConfig(
                enabled=ai_cfg.get("enabled", False),
                provider=AIProviderType(ai_cfg.get("provider", "openai_compatible")),
                api_key=ai_cfg.get("api_key"),
                base_url=ai_cfg.get("base_url", "https://api.openai.com/v1"),
                model=ai_cfg.get("model", "gpt-4o-mini"),
                system_prompt=ai_cfg.get("system_prompt"),
                timeout=int(ai_cfg.get("timeout", 60)),
                endpoint=ai_cfg.get("endpoint"),
                headers=ai_cfg.get("headers"),
            )
        except Exception:
            cfg = AIConfig(enabled=False)
        self.ai_client = AIClient(cfg)
        return self.ai_client

    def compute_and_plan(self) -> Dict[str, Any]:
        roster_cfg = self.config.get("roster", [])
        characters = [character_from_config(c) for c in roster_cfg]
        computed_chars = [{"name": c.name, **c.computed} for c in characters]

        enemy_cfg = self.config.get("enemy", {})
        enemy_obj = enemy_from_config(enemy_cfg or {})
        computed_enemy = {
            "name": enemy_obj.name,
            **enemy_obj.computed,
            "weaknesses": enemy_obj.weaknesses,
            "resistances": enemy_obj.resistances,
            "buffs": enemy_obj.buffs,
        }

        turn_order = compute_turn_order(computed_chars)
        team_estimates = summarize_team_estimates(computed_chars)
        synergy = analyze_team_enemy_synergy(roster_cfg, computed_chars, enemy_cfg)

        computed_all = {
            "characters": computed_chars,
            "turn_order": turn_order,
            "team_estimates": team_estimates,
            "enemy": computed_enemy,
            "synergy": synergy,
        }

        ctx = StrategyContext(
            mode=self.config.get("mode", "material_farm"),
            preferences=self.config.get("preferences", {}),
            roster=roster_cfg,
            enemy=enemy_cfg,
            computed=computed_all,
        )

        plan = self.strategy_manager.plan(ctx)

        # AI 详细策略文案
        ai_text = None
        ai_text_path = None
        if self.ai_client and self.ai_client.is_available():
            context_for_ai = {
                "mode": ctx.mode,
                "preferences": ctx.preferences,
                "roster": ctx.roster,
                "enemy": ctx.enemy,
                "computed": ctx.computed,
            }
            ai_text = self.ai_client.summarize_to_plan(context_for_ai)
            ai_text_path = self.memory.save("ai_strategy_text", {"plan": ai_text})

        # 保存记忆
        self.memory.save("characters", {"list": ctx.roster, "computed": computed_chars})
        self.memory.save("enemy", enemy_cfg)
        self.memory.save("computed", computed_all)
        self.memory.save("ai_config", self.config.get("ai", {}))
        self.memory.save("preferences", self.config.get("preferences", {}))
        self.memory.save("strategy_plan", {
            "name": plan.name,
            "description": plan.description,
            "options": plan.options,
            "recommends": plan.recommends,
            "steps": plan.steps,
            "requires_reroll": plan.requires_reroll,
            "expected_rounds": plan.expected_rounds,
        })

        summary = {
            "mode": ctx.mode,
            "preferences": ctx.preferences,
            "computed": computed_all,
            "strategy_plan": plan.__dict__,
            "ai_text_file": ai_text_path,
        }
        self.memory.save("planning_summary", summary)

        return {"plan": plan, "computed": computed_all, "ai_text": ai_text, "ai_text_file": ai_text_path}


class ConfigFrame(ttk.Frame):
    def __init__(self, master, state: AppState):
        super().__init__(master)
        self.state = state

        # AI 配置
        self.var_ai_enabled = tk.BooleanVar(value=bool(state.config.get("ai", {}).get("enabled", False)))
        self.var_provider = tk.StringVar(value=state.config.get("ai", {}).get("provider", "openai_compatible"))
        self.var_api_key = tk.StringVar(value=state.config.get("ai", {}).get("api_key") or "")
        self.var_base_url = tk.StringVar(value=state.config.get("ai", {}).get("base_url", "https://api.openai.com/v1"))
        self.var_model = tk.StringVar(value=state.config.get("ai", {}).get("model", "gpt-4o-mini"))
        self.var_system_prompt = tk.StringVar(value=state.config.get("ai", {}).get("system_prompt") or "")
        self.var_endpoint = tk.StringVar(value=state.config.get("ai", {}).get("endpoint") or "")
        self.var_headers = tk.StringVar(value=json.dumps(state.config.get("ai", {}).get("headers", {}), ensure_ascii=False))

        group_ai = ttk.LabelFrame(self, text="AI 配置（可选）")
        group_ai.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        ttk.Checkbutton(group_ai, text="启用 AI", variable=self.var_ai_enabled).grid(row=0, column=0, sticky="w")
        ttk.Label(group_ai, text="Provider").grid(row=0, column=1, sticky="e")
        ttk.Combobox(group_ai, textvariable=self.var_provider, values=["openai_compatible", "custom_http"], width=20).grid(row=0, column=2, sticky="w")

        ttk.Label(group_ai, text="API Key").grid(row=1, column=0, sticky="e")
        ttk.Entry(group_ai, textvariable=self.var_api_key, width=40, show="*").grid(row=1, column=1, columnspan=2, sticky="we")

        ttk.Label(group_ai, text="Base URL").grid(row=2, column=0, sticky="e")
        ttk.Entry(group_ai, textvariable=self.var_base_url, width=40).grid(row=2, column=1, columnspan=2, sticky="we")

        ttk.Label(group_ai, text="Model").grid(row=3, column=0, sticky="e")
        ttk.Entry(group_ai, textvariable=self.var_model, width=40).grid(row=3, column=1, columnspan=2, sticky="we")

        ttk.Label(group_ai, text="System Prompt").grid(row=4, column=0, sticky="e")
        ttk.Entry(group_ai, textvariable=self.var_system_prompt, width=60).grid(row=4, column=1, columnspan=2, sticky="we")

        ttk.Label(group_ai, text="Custom Endpoint").grid(row=5, column=0, sticky="e")
        ttk.Entry(group_ai, textvariable=self.var_endpoint, width=40).grid(row=5, column=1, columnspan=2, sticky="we")

        ttk.Label(group_ai, text="Custom Headers(JSON)").grid(row=6, column=0, sticky="e")
        ttk.Entry(group_ai, textvariable=self.var_headers, width=60).grid(row=6, column=1, columnspan=2, sticky="we")

        for i in range(3):
            group_ai.columnconfigure(i, weight=1)

        # 运行与模式
        group_run = ttk.LabelFrame(self, text="运行与模式")
        group_run.pack(fill=tk.X, padx=8, pady=4)
        self.var_plan_only = tk.BooleanVar(value=bool(state.config.get("run", {}).get("plan_only", False)))
        ttk.Checkbutton(group_run, text="仅规划（不启动自动战斗）", variable=self.var_plan_only).grid(row=0, column=0, sticky="w")
        ttk.Label(group_run, text="模式").grid(row=0, column=1, sticky="e")
        self.var_mode = tk.StringVar(value=state.config.get("mode", "material_farm"))
        ttk.Combobox(group_run, textvariable=self.var_mode, values=["material_farm", "abyss", "custom"], width=20).grid(row=0, column=2, sticky="w")

        for i in range(3):
            group_run.columnconfigure(i, weight=1)

    def export_to_config(self) -> Dict[str, Any]:
        # 解析 headers
        try:
            headers = json.loads(self.var_headers.get().strip() or "{}")
        except Exception as e:
            messagebox.showerror("错误", f"Headers 不是合法 JSON: {e}")
            raise
        cfg = self.state.config.copy()
        cfg.setdefault("ai", {})
        cfg["ai"].update({
            "enabled": bool(self.var_ai_enabled.get()),
            "provider": self.var_provider.get(),
            "api_key": self.var_api_key.get().strip() or None,
            "base_url": self.var_base_url.get().strip() or "https://api.openai.com/v1",
            "model": self.var_model.get().strip() or "gpt-4o-mini",
            "system_prompt": self.var_system_prompt.get().strip() or None,
            "timeout": 60,
            "endpoint": self.var_endpoint.get().strip() or None,
            "headers": headers,
        })
        cfg.setdefault("run", {})
        cfg["run"].update({"plan_only": bool(self.var_plan_only.get())})
        cfg["mode"] = self.var_mode.get()
        self.state.config = cfg
        return cfg


class PrefsFrame(ttk.Frame):
    def __init__(self, master, state: AppState):
        super().__init__(master)
        self.state = state

        prefs = state.config.get("preferences", {})
        self.var_allow_reroll = tk.BooleanVar(value=bool(prefs.get("allow_reroll", True)))
        self.var_selected_option = tk.StringVar(value=str(prefs.get("selected_option") or ""))

        rr = prefs.get("reroll_settings", {}) or {}
        self.var_bait_target = tk.StringVar(value=rr.get("bait_target", ""))
        self.var_bait_condition = tk.StringVar(value=rr.get("bait_condition", ""))
        self.var_max_retries = tk.IntVar(value=int(rr.get("max_retries", 5)))

        group = ttk.LabelFrame(self, text="偏好设置")
        group.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        ttk.Checkbutton(group, text="允许凹本（通过重开/诱导来优化回合）", variable=self.var_allow_reroll).grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(group, text="策略选项（A 稳定 / B 极限，留空为仅推荐）").grid(row=1, column=0, sticky="e")
        ttk.Entry(group, textvariable=self.var_selected_option, width=8).grid(row=1, column=1, sticky="w")

        ttk.Label(group, text="凹点：诱导对象").grid(row=2, column=0, sticky="e")
        ttk.Entry(group, textvariable=self.var_bait_target, width=20).grid(row=2, column=1, sticky="w")

        ttk.Label(group, text="凹点：触发条件").grid(row=3, column=0, sticky="e")
        ttk.Entry(group, textvariable=self.var_bait_condition, width=40).grid(row=3, column=1, sticky="w")

        ttk.Label(group, text="凹点：最大重试").grid(row=4, column=0, sticky="e")
        ttk.Spinbox(group, from_=0, to=50, textvariable=self.var_max_retries, width=6).grid(row=4, column=1, sticky="w")

        for i in range(2):
            group.columnconfigure(i, weight=1)

    def export_to_config(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        cfg = cfg.copy()
        cfg.setdefault("preferences", {})
        cfg["preferences"].update({
            "allow_reroll": bool(self.var_allow_reroll.get()),
            "selected_option": (self.var_selected_option.get().strip().upper() or None),
            "reroll_settings": {
                "bait_target": self.var_bait_target.get().strip() or None,
                "bait_condition": self.var_bait_condition.get().strip() or None,
                "max_retries": int(self.var_max_retries.get()),
            }
        })
        return cfg


class KeybindsFrame(ttk.Frame):
    def __init__(self, master, state: AppState):
        super().__init__(master)
        self.state = state

        input_cfg = state.config.get("input", {}) or {}
        keybinds = (input_cfg.get("keybinds") or {})
        self.var_enable_inputs = tk.BooleanVar(value=bool(input_cfg.get("enable_inputs", False)))

        group_switch = ttk.LabelFrame(self, text="输入安全开关")
        group_switch.pack(fill=tk.X, padx=8, pady=6)
        ttk.Checkbutton(group_switch, text="启用键鼠输入（未开启时不会发送任何按键）", variable=self.var_enable_inputs).pack(anchor="w", padx=8, pady=4)
        ttk.Label(group_switch, text="提示：为避免危险操作，程序会忽略包含 ctrl/alt/win/command 等组合键").pack(anchor="w", padx=8)

        group_keys = ttk.LabelFrame(self, text="键位映射（动作 → 按键名）")
        group_keys.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        self._action_vars: Dict[str, tk.StringVar] = {}
        actions = [
            ("attack", "普通攻击/普攻"),
            ("single_skill", "单体技能"),
            ("aoe_skill", "群体技能"),
            ("heal_skill", "治疗技能"),
            ("ultimate", "终结技/大招"),
            ("interact", "交互/拾取"),
            ("open_menu", "打开菜单"),
            ("confirm", "确认/确定"),
            ("cancel", "取消/返回"),
            ("switch_1", "切换角色1"),
            ("switch_2", "切换角色2"),
            ("switch_3", "切换角色3"),
            ("switch_4", "切换角色4"),
        ]
        for i, (k, label) in enumerate(actions):
            ttk.Label(group_keys, text=label).grid(row=i, column=0, sticky="e", padx=4, pady=2)
            var = tk.StringVar(value=str(keybinds.get(k, "")))
            self._action_vars[k] = var
            ttk.Entry(group_keys, textvariable=var, width=14).grid(row=i, column=1, sticky="w")
        for c in range(2):
            group_keys.columnconfigure(c, weight=1)

    def export_to_config(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        cfg = cfg.copy()
        cfg.setdefault("input", {})
        # 构建 keybinds
        keybinds: Dict[str, str] = {}
        for k, var in self._action_vars.items():
            v = (var.get() or "").strip()
            if v:
                keybinds[k] = v
        cfg["input"].update({
            "enable_inputs": bool(self.var_enable_inputs.get()),
            "keybinds": keybinds,
        })
        self.state.config = cfg
        return cfg


class DataFrame(ttk.Frame):
    def __init__(self, master, state: AppState):
        super().__init__(master)
        self.state = state

        group_team = ttk.LabelFrame(self, text="队伍（JSON 列表）")
        group_team.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.text_roster = tk.Text(group_team, height=12)
        self.text_roster.pack(fill=tk.BOTH, expand=True)

        group_enemy = ttk.LabelFrame(self, text="敌人/关卡（JSON 对象）")
        group_enemy.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.text_enemy = tk.Text(group_enemy, height=8)
        self.text_enemy.pack(fill=tk.BOTH, expand=True)

        # 预填入当前配置
        self.text_roster.insert("1.0", json.dumps(self.state.config.get("roster", []), ensure_ascii=False, indent=2))
        self.text_enemy.insert("1.0", json.dumps(self.state.config.get("enemy", {}), ensure_ascii=False, indent=2))

        # 提示
        tip = ttk.Label(self, text="提示：点击“生成策略”会自动计算角色/敌人衍生属性，并保存到 data/memory/ 作为记忆。")
        tip.pack(fill=tk.X, padx=8, pady=2)

    def export_to_config(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        cfg = cfg.copy()
        try:
            roster = json.loads(self.text_roster.get("1.0", tk.END))
            enemy = json.loads(self.text_enemy.get("1.0", tk.END))
            if not isinstance(roster, list):
                raise ValueError("roster 必须是列表")
            if not isinstance(enemy, dict):
                raise ValueError("enemy 必须是对象")
        except Exception as e:
            messagebox.showerror("错误", f"JSON 解析失败: {e}")
            raise
        cfg["roster"] = roster
        cfg["enemy"] = enemy
        return cfg


class ScanFrame(ttk.Frame):
    def __init__(self, master, state: AppState, frames: Optional[Dict[str, Any]] = None):
        super().__init__(master)
        self.state = state
        self.frames = frames or {}

        ocr_cfg = state.config.get("ocr", {})
        ui_cfg = state.config.get("ui_regions", {})

        # OCR 配置表单
        group_ocr = ttk.LabelFrame(self, text="OCR 识别设置（Tesseract 或 AI 视觉）")
        group_ocr.pack(fill=tk.X, padx=8, pady=6)
        self.var_ocr_provider = tk.StringVar(value=ocr_cfg.get("provider", "tesseract"))
        self.var_tess_path = tk.StringVar(value=ocr_cfg.get("tesseract_path") or "")
        self.var_lang = tk.StringVar(value=ocr_cfg.get("lang", "chi_sim+eng"))
        self.var_psm = tk.IntVar(value=int(ocr_cfg.get("psm", 6)))
        self.var_oem = tk.IntVar(value=int(ocr_cfg.get("oem", 3)))
        self.var_threshold = tk.IntVar(value=int(ocr_cfg.get("threshold", 180)))
        self.var_invert = tk.BooleanVar(value=bool(ocr_cfg.get("invert", False)))
        self.var_blur = tk.IntVar(value=int(ocr_cfg.get("blur", 1)))
        self.var_vision_prompt = tk.StringVar(value=ocr_cfg.get("vision_prompt", ""))

        ttk.Label(group_ocr, text="Provider").grid(row=0, column=0, sticky="e")
        ttk.Combobox(group_ocr, textvariable=self.var_ocr_provider, values=["tesseract", "ai_vision"], width=16).grid(row=0, column=1, sticky="w")

        ttk.Label(group_ocr, text="Tesseract 路径").grid(row=1, column=0, sticky="e")
        ttk.Entry(group_ocr, textvariable=self.var_tess_path, width=48).grid(row=1, column=1, columnspan=3, sticky="we")
        ttk.Label(group_ocr, text="语言(lang)").grid(row=2, column=0, sticky="e")
        ttk.Entry(group_ocr, textvariable=self.var_lang, width=24).grid(row=2, column=1, sticky="w")
        ttk.Label(group_ocr, text="PSM").grid(row=2, column=2, sticky="e")
        ttk.Spinbox(group_ocr, from_=3, to=13, textvariable=self.var_psm, width=6).grid(row=2, column=3, sticky="w")
        ttk.Label(group_ocr, text="OEM").grid(row=3, column=0, sticky="e")
        self.var_oem_widget = ttk.Spinbox(group_ocr, from_=0, to=3, textvariable=self.var_oem, width=6)
        self.var_oem_widget.grid(row=3, column=1, sticky="w")
        ttk.Label(group_ocr, text="二值阈值").grid(row=3, column=2, sticky="e")
        ttk.Spinbox(group_ocr, from_=0, to=255, textvariable=self.var_threshold, width=8).grid(row=3, column=3, sticky="w")
        ttk.Checkbutton(group_ocr, text="反相", variable=self.var_invert).grid(row=4, column=0, sticky="w")
        ttk.Label(group_ocr, text="模糊核").grid(row=4, column=1, sticky="e")
        ttk.Spinbox(group_ocr, from_=1, to=9, increment=2, textvariable=self.var_blur, width=6).grid(row=4, column=2, sticky="w")

        ttk.Label(group_ocr, text="AI 视觉提示词").grid(row=5, column=0, sticky="e")
        ttk.Entry(group_ocr, textvariable=self.var_vision_prompt, width=60).grid(row=5, column=1, columnspan=3, sticky="we")

        for i in range(4):
            group_ocr.columnconfigure(i, weight=1)

        # UI 区域配置
        group_ui = ttk.LabelFrame(self, text="UI 区域（JSON，坐标/按钮）")
        group_ui.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        self.text_regions = tk.Text(group_ui, height=10)
        self.text_regions.pack(fill=tk.BOTH, expand=True)
        # 预填
        self.text_regions.insert("1.0", json.dumps(ui_cfg, ensure_ascii=False, indent=2))

        # 扫描控制
        group_ctrl = ttk.LabelFrame(self, text="扫描操作")
        group_ctrl.pack(fill=tk.X, padx=8, pady=6)
        # 角色基本信息（人工输入姓名/元素/命途）
        ttk.Label(group_ctrl, text="角色名").grid(row=0, column=0, sticky="e")
        self.var_char_name = tk.StringVar(value="角色A")
        ttk.Entry(group_ctrl, textvariable=self.var_char_name, width=12).grid(row=0, column=1, sticky="w")
        ttk.Label(group_ctrl, text="元素").grid(row=0, column=2, sticky="e")
        self.var_char_elem = tk.StringVar(value="Physical")
        ttk.Entry(group_ctrl, textvariable=self.var_char_elem, width=12).grid(row=0, column=3, sticky="w")
        ttk.Label(group_ctrl, text="命途").grid(row=0, column=4, sticky="e")
        self.var_char_path = tk.StringVar(value="Hunt")
        ttk.Entry(group_ctrl, textvariable=self.var_char_path, width=12).grid(row=0, column=5, sticky="w")

        ttk.Button(group_ctrl, text="截图预览（保存到 data/screenshots）", command=self.on_capture).grid(row=1, column=0, columnspan=3, sticky="w")
        ttk.Button(group_ctrl, text="扫描当前角色 → 追加到队伍", command=self.on_scan_character).grid(row=1, column=3, columnspan=3, sticky="e")

        ttk.Separator(self).pack(fill=tk.X, padx=8, pady=6)

        group_enemy = ttk.LabelFrame(self, text="敌人扫描")
        group_enemy.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(group_enemy, text="敌人名称").grid(row=0, column=0, sticky="e")
        self.var_enemy_name = tk.StringVar(value="敌人")
        ttk.Entry(group_enemy, textvariable=self.var_enemy_name, width=18).grid(row=0, column=1, sticky="w")
        ttk.Button(group_enemy, text="扫描敌人面板 → 写入 enemy", command=self.on_scan_enemy).grid(row=0, column=2, sticky="e")
        for i in range(3):
            group_enemy.columnconfigure(i, weight=1)

    def _read_regions(self) -> Dict[str, Any]:
        try:
            return json.loads(self.text_regions.get("1.0", tk.END))
        except Exception as e:
            messagebox.showerror("错误", f"UI 区域 JSON 解析失败: {e}")
            raise

    def export_to_config(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        cfg = cfg.copy()
        cfg.setdefault("ocr", {})
        cfg.setdefault("ui_regions", {})
        cfg["ocr"].update({
            "provider": self.var_ocr_provider.get(),
            "tesseract_path": (self.var_tess_path.get().strip() or None),
            "lang": self.var_lang.get().strip() or "chi_sim+eng",
            "psm": int(self.var_psm.get()),
            "oem": int(self.var_oem.get()),
            "threshold": int(self.var_threshold.get()),
            "invert": bool(self.var_invert.get()),
            "blur": int(self.var_blur.get()),
            "vision_prompt": (self.var_vision_prompt.get().strip() or None),
        })
        try:
            regions = self._read_regions()
        except Exception:
            return cfg
        cfg["ui_regions"].update(regions)
        self.state.config = cfg
        return cfg

    def on_capture(self):
        # 截图并保存
        try:
            out_dir = os.path.join(os.getcwd(), "data", "screenshots")
            os.makedirs(out_dir, exist_ok=True)
            import pyautogui
            img = pyautogui.screenshot()
            fname = time.strftime("%Y%m%d-%H%M%S") + ".png"
            path = os.path.join(out_dir, fname)
            img.save(path)
            messagebox.showinfo("成功", f"已保存截图: {path}")
        except Exception as e:
            messagebox.showerror("错误", f"截图失败：{e}")

    def _build_scanners(self) -> Tuple[CharacterScanner, EnemyScanner, UIRegions]:
        # 读取配置
        cfg = self.export_to_config(self.state.config)
        o = cfg.get("ocr", {})
        u = cfg.get("ui_regions", {})
        # 根据 provider 构建 OCR
        provider = o.get("provider", "tesseract")
        if provider == "ai_vision":
            # 确保 AI 客户端可用
            self.state.ensure_ai()
            from src.image_recognition.ai_vision_ocr import AIVisionOCR
            ocr = AIVisionOCR(self.state.ai_client, vision_prompt=o.get("vision_prompt"))
        else:
            ocr = OCR(OCRConfig(
                provider=provider,
                tesseract_path=o.get("tesseract_path"),
                lang=o.get("lang", "chi_sim+eng"),
                psm=int(o.get("psm", 6)),
                oem=int(o.get("oem", 3)),
                threshold=o.get("threshold", 180),
                invert=bool(o.get("invert", False)),
                blur=int(o.get("blur", 1)),
            ))
        ui = UIRegions(
            character_stats=tuple(u.get("character_stats", [100, 100, 400, 300])),
            skill_buttons=[tuple(x) for x in (u.get("skill_buttons", []) or [])],
            skill_detail_region=tuple(u.get("skill_detail_region", [600, 200, 600, 600])),
            enemy_panel=tuple(u.get("enemy_panel", [1000, 100, 400, 300])),
            detail_button=(tuple(u.get("detail_button")) if u.get("detail_button") else None),
        )
        cscan = CharacterScanner(ocr)
        escan = EnemyScanner(ocr)
        return cscan, escan, ui

    def on_scan_character(self):
        try:
            cscan, _, ui = self._build_scanners()
            data = cscan.scan_character_all(ui)
            basic = data.get("basic", {})
            stats = basic.get("stats", {})
            char = assemble_character_from_scan(
                name=self.var_char_name.get().strip() or "角色A",
                element=self.var_char_elem.get().strip() or "Physical",
                path=self.var_char_path.get().strip() or "Hunt",
                basic_stats=stats,
            )
            # 追加到队伍 JSON 框
            frm_data: DataFrame = self.frames.get("data")
            if frm_data is not None and hasattr(frm_data, "text_roster"):
                try:
                    roster = json.loads(frm_data.text_roster.get("1.0", tk.END) or "[]")
                    if not isinstance(roster, list):
                        roster = []
                except Exception:
                    roster = []
                roster.append(char)
                frm_data.text_roster.delete("1.0", tk.END)
                frm_data.text_roster.insert("1.0", json.dumps(roster, ensure_ascii=False, indent=2))
            messagebox.showinfo("完成", "已追加扫描到的角色数据（基础属性与空白遗器）")
        except Exception as e:
            messagebox.showerror("错误", f"扫描角色失败：{e}")

    def on_scan_enemy(self):
        try:
            _, escan, ui = self._build_scanners()
            data = escan.scan_enemy_panel(ui)
            enemy = assemble_enemy_from_scan(self.var_enemy_name.get().strip() or "敌人", data.get("raw_text", ""))
            # 写入敌人 JSON 框
            frm_data: DataFrame = self.frames.get("data")
            if frm_data is not None and hasattr(frm_data, "text_enemy"):
                frm_data.text_enemy.delete("1.0", tk.END)
                frm_data.text_enemy.insert("1.0", json.dumps(enemy, ensure_ascii=False, indent=2))
            messagebox.showinfo("完成", "已写入扫描到的敌人数据（原始文本在 notes 字段）")
        except Exception as e:
            messagebox.showerror("错误", f"扫描敌人失败：{e}")


class PlanFrame(ttk.Frame):
    def __init__(self, master, state: AppState, frames: Optional[Dict[str, Any]] = None):
        super().__init__(master)
        self.state = state
        self.frames = frames or {}

        self.btn_compute = ttk.Button(self, text="生成策略（仅规划）", command=self.on_compute)
        self.btn_compute.pack(anchor="w", padx=8, pady=6)

        self.text_output = tk.Text(self, height=24)
        self.text_output.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.btn_start = ttk.Button(self, text="开始自动战斗（需要先切到对应界面）", command=self.on_start)
        self.btn_start.pack(anchor="e", padx=8, pady=6)

    def _gather_config(self) -> Dict[str, Any]:
        # 尽可能从各个面板收集最新的表单数据，更新到 state.config
        cfg = self.state.config
        try:
            if "config" in self.frames and hasattr(self.frames["config"], "export_to_config"):
                cfg = self.frames["config"].export_to_config()
            if "prefs" in self.frames and hasattr(self.frames["prefs"], "export_to_config"):
                cfg = self.frames["prefs"].export_to_config(cfg)
            if "keybinds" in self.frames and hasattr(self.frames["keybinds"], "export_to_config"):
                cfg = self.frames["keybinds"].export_to_config(cfg)
            if "data" in self.frames and hasattr(self.frames["data"], "export_to_config"):
                cfg = self.frames["data"].export_to_config(cfg)
        finally:
            self.state.config = cfg
        return cfg

    def on_compute(self):
        try:
            # 先收集并应用最新配置
            self._gather_config()
            # 刷新 AI 客户端
            self.state.ensure_ai()
            # 计算并生成计划
            result = self.state.compute_and_plan()
            plan = result.get("plan")
            comp = result.get("computed")
            ai_text = result.get("ai_text")

            self.text_output.delete("1.0", tk.END)
            lines = []
            lines.append(f"策略：{plan.name}")
            lines.append("")
            lines.append(plan.description)
            lines.append("")
            lines.append("可选方案：")
            for i, opt in enumerate(plan.options, 1):
                lines.append(f"  {i}. {opt}")
            if plan.recommends:
                lines.append("")
                lines.append(f"推荐：{plan.recommends}")
            lines.append("")
            lines.append("执行步骤：")
            for i, step in enumerate(plan.steps, 1):
                lines.append(f"  {i}. {step}")
            lines.append("")
            lines.append(f"是否涉及凹：{plan.requires_reroll}")
            if plan.expected_rounds is not None:
                lines.append(f"预期回合数：{plan.expected_rounds}")

            # 显示契合度摘要
            syn = (comp or {}).get("synergy", {})
            lines.append("")
            lines.append("契合度摘要：")
            lines.append(f"  元素覆盖：{syn.get('element_counts', {})}")
            lines.append(f"  弱点命中：{syn.get('weakness_match_names', [])} / 覆盖率 {syn.get('weakness_match_ratio')}")
            lines.append(f"  敌方对队伍元素的平均抗性：{syn.get('avg_enemy_resistance_vs_team')}")
            lines.append(f"  速度概况：平均 {syn.get('avg_speed')} / 最高 {syn.get('max_speed')}")
            # 展示首轮行动顺序
            turn = (comp or {}).get("turn_order", []) or []
            if turn:
                lines.append("  首轮行动顺序：")
                for name, spd in turn:
                    lines.append(f"    - {name}（SPD {spd}）")

            # 角色计算详情
            chars = (comp or {}).get("characters", []) or []
            if chars:
                lines.append("")
                lines.append("角色计算详情：")
                for c in chars:
                    cname = c.get("name", "unknown")
                    lines.append(f"  - {cname}")
                    metrics = [
                        "atk","hp","def","spd","crit_rate","crit_dmg",
                        "energy_regen","break_effect","crit_factor","ehp","burst_ceiling",
                    ]
                    for m in metrics:
                        if m in c and c.get(m) is not None:
                            lines.append(f"      {m}: {c.get(m)}")

            # 队伍伤害估算
            team_est = (comp or {}).get("team_estimates", {}) or {}
            if team_est:
                lines.append("")
                lines.append("队伍伤害估算：")
                for nm, est in team_est.items():
                    lines.append(f"  - {nm}: avg_hit={est.get('avg_hit')}, burst_potential={est.get('burst_potential')}")

            # 敌人信息
            enemy = (comp or {}).get("enemy", {}) or {}
            lines.append("")
            lines.append("敌人信息：")
            lines.append(f"  名称: {enemy.get('name')}")
            lines.append(
                f"  属性: HP {enemy.get('hp')}, DEF {enemy.get('def')}, SPD {enemy.get('spd')}, Toughness {enemy.get('toughness')}"
            )
            lines.append(f"  弱点: {enemy.get('weaknesses')}")
            lines.append(f"  抗性: {enemy.get('resistances')}")
            lines.append(f"  Buffs: {enemy.get('buffs')}")

            # 如果 AI 有更详细文案
            if ai_text:
                lines.append("")
                lines.append("AI 详细策略：")
                lines.append(ai_text)

            self.text_output.insert("1.0", "\n".join(lines))
        except Exception as e:
            messagebox.showerror("错误", f"生成策略失败：{e}")

    def on_start(self):
        # 将当前 UI 配置保存到内存，并基于该配置启动主循环
        try:
            # 先收集并应用最新配置
            self._gather_config()

            self.state.auto = StarRailAutoBattle()
            self.state.auto.config = self.state.config
            self.state.auto._setup_ai()
            self.state.auto._prepare_strategy()

            if self.state.config.get("run", {}).get("plan_only", False):
                messagebox.showinfo("提示", "当前为仅规划模式，已生成策略与记忆，不会启动自动战斗。")
                return

            # 在后台线程启动，以免阻塞 UI
            def run():
                try:
                    self.state.auto.start_battle()
                except Exception as e:
                    messagebox.showerror("错误", f"自动战斗异常：{e}")

            threading.Thread(target=run, daemon=True).start()
            messagebox.showinfo("已启动", "自动战斗已启动。请确保游戏窗口在前台并已切换到目标模式。")
        except Exception as e:
            messagebox.showerror("错误", f"启动失败：{e}")


class FooterFrame(ttk.Frame):
    def __init__(self, master, state: AppState, frames: Dict[str, Any]):
        super().__init__(master)
        self.state = state
        self.frames = frames

        ttk.Button(self, text="保存为 config.json", command=self.save_config).pack(side=tk.LEFT, padx=8, pady=6)
        ttk.Button(self, text="从 config.json 载入", command=self.load_config).pack(side=tk.LEFT, padx=8, pady=6)
        ttk.Button(self, text="从示例载入", command=self.load_example).pack(side=tk.LEFT, padx=8, pady=6)

        self.label_tip = ttk.Label(self, text="提示：启动前请先在游戏内手动切换到目标模式界面（如刷材料/深渊）")
        self.label_tip.pack(side=tk.RIGHT, padx=8)

    def _gather_config(self) -> Dict[str, Any]:
        cfg = self.frames["config"].export_to_config()
        cfg = self.frames["prefs"].export_to_config(cfg)
        if "keybinds" in self.frames and hasattr(self.frames["keybinds"], "export_to_config"):
            cfg = self.frames["keybinds"].export_to_config(cfg)
        cfg = self.frames["data"].export_to_config(cfg)
        self.state.config = cfg
        return cfg

    def save_config(self):
        try:
            cfg = self._gather_config()
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", "已保存到 config.json")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{e}")

    def load_config(self):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.state.config.update(cfg)
            messagebox.showinfo("成功", "已从 config.json 载入。请重新打开窗口以刷新表单。")
        except Exception as e:
            messagebox.showerror("错误", f"载入失败：{e}")

    def load_example(self):
        try:
            with open("config.example.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.state.config.update(cfg)
            messagebox.showinfo("成功", "已从示例载入。请重新打开窗口以刷新表单。")
        except Exception as e:
            messagebox.showerror("错误", f"载入失败：{e}")


def run_app():
    state = AppState()
    state.ensure_ai()

    root = tk.Tk()
    root.title("星穹铁道 AI 战斗策略 - 控制台")
    root.geometry("960x720")

    notebook = ttk.Notebook(root)
    frames: Dict[str, Any] = {}

    frm_config = ConfigFrame(notebook, state)
    frames["config"] = frm_config
    frm_prefs = PrefsFrame(notebook, state)
    frames["prefs"] = frm_prefs
    frm_keybinds = KeybindsFrame(notebook, state)
    frames["keybinds"] = frm_keybinds
    frm_data = DataFrame(notebook, state)
    frames["data"] = frm_data
    frm_scan = ScanFrame(notebook, state, frames)
    frames["scan"] = frm_scan
    frm_plan = PlanFrame(notebook, state, frames)
    frames["plan"] = frm_plan

    notebook.add(frm_config, text="1. 配置与模式")
    notebook.add(frm_prefs, text="2. 偏好（凹本）")
    notebook.add(frm_keybinds, text="3. 键位设置")
    notebook.add(frm_data, text="4. 队伍与敌人")
    notebook.add(frm_scan, text="5. 识图 / 扫描")
    notebook.add(frm_plan, text="6. 生成策略 / 启动")
    notebook.pack(fill=tk.BOTH, expand=True)

    footer = FooterFrame(root, state, frames)
    footer.pack(fill=tk.X)

    root.mainloop()
