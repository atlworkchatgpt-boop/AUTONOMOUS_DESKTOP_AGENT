import time

from agent.ai_controller import AIController
from agent.tools import list_tools


print("=" * 70)
print(" FAST AUTONOMOUS DESKTOP AI TEST")
print("=" * 70)

print()
print("TOOLS:")

for tool in list_tools():

    print(" -", tool)

print()

start = time.time()

ai = AIController()

print("AI initialization:",
      round(time.time() - start, 2),
      "seconds")

print()

start = time.time()

answer = ai.think(
    "Explain what this autonomous desktop AI is designed to do."
)

elapsed = time.time() - start

print(answer)

print()
print(
    "LLM response time:",
    round(elapsed, 2),
    "seconds"
)

print()
print("=" * 70)
print(" TEST COMPLETE")
print("=" * 70)
