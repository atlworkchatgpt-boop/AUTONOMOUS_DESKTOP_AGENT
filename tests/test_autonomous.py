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


print("=" * 70)
print(" AUTONOMOUS DESKTOP AI")
print("=" * 70)

print()
print("Starting local AI...")
print("No OpenAI API.")
print("No cloud AI.")
print("Ollama only.")
print()


ai = AIController()


print("[TEST 1] NORMAL QUESTION")
print("-" * 70)

answer = ai.think(
    "Explain what an autonomous desktop agent is."
)

print(answer)


print()
print("[TEST 2] AUTONOMOUS LOOP")
print("-" * 70)

result = ai.run_goal(
    "Inspect the current project directory and determine whether it exists."
)

print(result)


print()
print("=" * 70)
print(" TEST COMPLETE")
print("=" * 70)
