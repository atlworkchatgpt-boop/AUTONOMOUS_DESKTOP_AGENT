from agent.tools.computer import TOOLS


def get_tools():
    return list(TOOLS.keys())


def run_tool(name, **kwargs):

    if name not in TOOLS:

        return {
            "success": False,
            "error": "Unknown tool: " + name
        }

    try:
        return TOOLS[name](**kwargs)

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }
