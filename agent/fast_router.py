import re


class FastRouter:

    def match(self, text):

        t = text.strip()

        # OPEN
        m = re.match(
            r"^(?:open|launch|start)\s+(.+)$",
            t,
            re.I
        )

        if m:
            target = m.group(1).strip()

            known = {
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "calc": "calc.exe",
                "paint": "mspaint.exe",
                "explorer": "explorer.exe"
            }

            command = known.get(
                target.lower(),
                target
            )

            return {
                "tool": "open_application",
                "args": {
                    "command": command
                }
            }

        # CLOSE
        m = re.match(
            r"^(?:close|stop|kill)\s+(.+)$",
            t,
            re.I
        )

        if m:
            process = m.group(1).strip()

            if not process.lower().endswith(".exe"):
                process += ".exe"

            return {
                "tool": "close_application",
                "args": {
                    "process_name": process
                }
            }

        # DELETE
        m = re.match(
            r"^(?:delete|remove)\s+(.+)$",
            t,
            re.I
        )

        if m:
            return {
                "tool": "delete_path",
                "args": {
                    "path": m.group(1).strip()
                }
            }

        return None
