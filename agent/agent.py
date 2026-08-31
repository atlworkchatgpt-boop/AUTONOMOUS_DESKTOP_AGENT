from agent.fast_router import FastRouter
from agent.executor import ToolExecutor


class AutonomousAgent:

    def __init__(self):
        self.router = FastRouter()
        self.executor = ToolExecutor()

    def handle(self, request):

        # First try deterministic fast actions.
        action = self.router.match(request)

        if action:

            result = self.executor.execute(
                action["tool"],
                **action["args"]
            )

            return {
                "mode": "tool",
                "action": action,
                "result": result
            }

        return {
            "mode": "chat",
            "message":
                "This request needs the AI reasoning layer. "
                "No desktop action was executed."
        }
