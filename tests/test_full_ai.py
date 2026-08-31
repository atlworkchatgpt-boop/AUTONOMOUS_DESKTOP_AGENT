import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from agent.ai_controller import AIController
from agent.tools import list_tools


print("=" * 70)
print(" AUTONOMOUS DESKTOP AI - FULL INTELLIGENCE TEST")
print("=" * 70)

print()
print("[1] AVAILABLE TOOLS")
print()

for tool in list_tools():
    print("  -", tool)

print()
print("[2] PLANNER")
print()

ai = AIController()

plan = ai.plan(
    "Inspect my project and explain what files are present."
)

for step in plan:
    print(
        step["step"],
        "->",
        step["description"]
    )

print()
print("[3] RAG MEMORY")
print()

context = ai.knowledge.build_context(
    "What is this autonomous desktop AI?"
)

if context:
    print(context[:1000])
else:
    print("No knowledge found.")

print()
print("[4] LOCAL LLM")
print()

answer = ai.think(
    "Explain the four intelligence layers of this autonomous desktop AI."
)

print(answer)

print()
print("=" * 70)
print(" FULL TEST COMPLETE")
print("=" * 70)
