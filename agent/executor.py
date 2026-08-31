from agent.tools import get_tool


class ToolExecutor:

    def execute(
        self,
        tool_name,
        **kwargs
    ):

        tool = get_tool(tool_name)

        if tool is None:
            return {
                "success": False,
                "error":
                    f"Unknown tool: {tool_name}"
            }

        try:

            result = tool(**kwargs)

            if not isinstance(result, dict):
                return {
                    "success": False,
                    "error": "Tool returned invalid result."
                }

            # IMPORTANT:
            # Never convert a failed tool result into success.
            return result

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }
