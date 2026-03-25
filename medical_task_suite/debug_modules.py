"""
调试模块选择问题
"""

from optimization.core.module_integrator import ModuleIntegrator
import json

print("Creating ModuleIntegrator...")
integrator = ModuleIntegrator()

print(f"\nModule definitions loaded: {len(integrator.module_definitions)}")
print(f"Scenario module map: {list(integrator.scenario_module_map.keys())}")

# 检查chest_pain场景
task_context = {
    "scenario_type": "chest_pain",
    "difficulty": "L2"
}

print(f"\n\nTesting with scenario_type: '{task_context['scenario_type']}'")

# 检查场景映射
if task_context['scenario_type'] in integrator.scenario_module_map:
    mapping = integrator.scenario_module_map[task_context['scenario_type']]
    print(f"Found in scenario_module_map:")
    print(f"  Primary: {mapping.get('primary_modules', [])}")
    print(f"  Secondary: {mapping.get('secondary_modules', [])}")
else:
    print(f"NOT found in scenario_module_map")
    print(f"Available scenarios: {list(integrator.scenario_module_map.keys())}")

# 尝试选择模块
print(f"\nCalling select_modules_for_task()...")
result = integrator.select_modules_for_task(task_context, max_modules=3)

print(f"\nResult type: {type(result)}")
print(f"Result length: {len(result)}")

if result:
    if isinstance(result[0], dict):
        print(f"First result keys: {result[0].keys()}")
        print(f"First result: {result[0]}")
    else:
        print(f"Result: {result}")
else:
    print("Result is empty!")

# 尝试其他场景类型
print("\n" + "="*80)
print("Testing different scenario types:")
for scenario in ["information_query", "symptom_based_diagnosis", "chest_pain", "fever"]:
    result = integrator.select_modules_for_task({"scenario_type": scenario}, max_modules=2)
    print(f"{scenario}: {len(result)} modules")
