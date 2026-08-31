import json

from agent.llm import LocalBrain
from agent.memory.rag import KnowledgeBase
from agent.memory.conversation import ConversationMemory
from agent.executor import ToolExecutor
from agent.tools import list_tools


class AIController:

    def __init__(self):

        self.brain = LocalBrain()

        self.knowledge = KnowledgeBase()

        self.memory = ConversationMemory()

        self.executor = ToolExecutor()


    def think(self, message):

        context = self.knowledge.build_context(message)

        self.memory.add(
            "user",
            message
        )

        answer = self.brain.ask(
            message,
            context
        )

        self.memory.add(
            "assistant",
            answer
        )

        return answer


    def run_goal(self, goal, max_steps=8):

        """
        Real autonomous loop:

        goal
          ↓
        reason
          ↓
        choose action
          ↓
        execute
          ↓
        inspect result
          ↓
        continue or finish
        """

        tools = list_tools()

        history = []

        for step in range(1, max_steps + 1):

            context = self.knowledge.build_context(
                goal
            )

            prompt = f"""
You are controlling a desktop agent.

USER GOAL:
{goal}

AVAILABLE TOOLS:
{tools}

PREVIOUS ACTIONS:
{history}

RELEVANT KNOWLEDGE:
{context}

Decide the next action.

Return ONLY valid JSON.

If a tool is required:

{{
    "action": "tool",
    "tool": "TOOL_NAME",
    "arguments": {{}},
    "reason": "short reason"
}}

If no tool is required and the task is complete:

{{
    "action": "finish",
    "answer": "final answer"
}}

Rules:

- Never invent tool results.
- Only use tools from AVAILABLE TOOLS.
- Arguments must match the tool.
- Do not claim success before receiving a tool result.
"""

            raw = self.brain.ask(prompt)

            try:

                decision = json.loads(raw)

            except Exception:

                return {
                    "success": False,
                    "error": "AI returned invalid JSON.",
                    "raw": raw,
                    "history": history
                }


            action = decision.get("action")


            if action == "finish":

                return {
                    "success": True,
                    "answer": decision.get(
                        "answer",
                        ""
                    ),
                    "history": history
                }


            if action != "tool":

                return {
                    "success": False,
                    "error": "Invalid AI action.",
                    "decision": decision,
                    "history": history
                }


            tool_name = decision.get("tool")

            arguments = decision.get(
                "arguments",
                {}
            )


            result = self.executor.execute(
                tool_name,
                **arguments
            )


            history.append({

                "step": step,

                "tool": tool_name,

                "arguments": arguments,

                "result": result

            })


            verification_prompt = f"""
USER GOAL:
{goal}

TOOL EXECUTED:
{tool_name}

TOOL ARGUMENTS:
{arguments}

ACTUAL TOOL RESULT:
{result}

Determine what the actual result proves.

Do not invent anything.

If successful, continue toward the goal.

If unsuccessful, determine whether another available tool
or another attempt is appropriate.

Do not claim the task is complete unless the result supports it.
"""

            self.brain.ask(
                verification_prompt
            )


        return {

            "success": False,

            "error":
                "Maximum autonomous steps reached.",

            "history": history

        }
