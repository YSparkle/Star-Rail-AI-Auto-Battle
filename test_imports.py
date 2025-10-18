#!/usr/bin/env python3
"""
测试所有模块是否能正确导入
Test if all modules can be imported correctly
"""

def test_imports():
    """测试模块导入"""
    print("开始测试模块导入...")
    print("-" * 50)
    
    # 测试 src 包
    try:
        import src
        print("✅ src 包导入成功")
        print(f"   版本: {src.__version__}")
    except ImportError as e:
        print(f"❌ src 包导入失败: {e}")
        return False
    
    # 测试决策引擎
    try:
        from src.decision_engine import BattleDecision, BattleState, CharacterRole
        print("✅ decision_engine 模块导入成功")
        print(f"   类: BattleDecision, BattleState, CharacterRole")
    except ImportError as e:
        print(f"❌ decision_engine 模块导入失败: {e}")
        return False
    
    # 测试图像识别（可能需要 DISPLAY 环境）
    try:
        from src.image_recognition import ImageRecognizer
        print("✅ image_recognition 模块导入成功")
        print(f"   类: ImageRecognizer")
    except (ImportError, KeyError) as e:
        print(f"⚠️  image_recognition 模块导入失败: {e}")
        print("   注意: 这可能是因为缺少图形环境（DISPLAY）")
    
    # 测试游戏控制（可能需要 DISPLAY 环境）
    try:
        from src.game_control import GameController
        print("✅ game_control 模块导入成功")
        print(f"   类: GameController")
    except (ImportError, KeyError) as e:
        print(f"⚠️  game_control 模块导入失败: {e}")
        print("   注意: 这可能是因为缺少图形环境（DISPLAY）")
    
    print("-" * 50)
    print("✅ 核心模块测试完成！")
    return True

def test_main_file():
    """测试主文件语法"""
    print("\n测试 main.py 语法...")
    print("-" * 50)
    
    try:
        import py_compile
        py_compile.compile('main.py', doraise=True)
        print("✅ main.py 语法正确")
    except py_compile.PyCompileError as e:
        print(f"❌ main.py 语法错误: {e}")
        return False
    
    print("-" * 50)
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("Star-Rail-AI-Auto-Battle 模块测试")
    print("=" * 50)
    print()
    
    success = True
    success = test_imports() and success
    success = test_main_file() and success
    
    print()
    if success:
        print("🎉 所有测试通过！项目结构设置正确。")
    else:
        print("⚠️  部分测试未通过，请检查错误信息。")
