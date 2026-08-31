class Planner:

    def create_plan(self, goal):

        text = goal.lower()

        steps = []

        if any(
            x in text
            for x in [
                "file",
                "folder",
                "directory",
                "project"
            ]
        ):

            steps.append(
                "Inspect the relevant filesystem location."
            )

        if any(
            x in text
            for x in [
                "open",
                "launch",
                "start",
                "run"
            ]
        ):

            steps.append(
                "Determine the application or command required."
            )

        if any(
            x in text
            for x in [
                "create",
                "write",
                "make"
            ]
        ):

            steps.append(
                "Create the requested resource."
            )

        if any(
            x in text
            for x in [
                "read",
                "show",
                "inspect"
            ]
        ):

            steps.append(
                "Read and inspect the requested information."
            )

        if not steps:

            steps.append(
                "Understand the request and determine the required action."
            )

        steps.append(
            "Verify the result."
        )

        steps.append(
            "Report the verified result to the user."
        )

        return [
            {
                "step": index + 1,
                "description": description
            }
            for index, description
            in enumerate(steps)
        ]
