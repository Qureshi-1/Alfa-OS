from prototype.common import Goal


class GoalInterpreter:
    def interpret(self, user_input: str) -> Goal:
        user_input = user_input.strip()
        
        if not user_input:
            return Goal(name="EMPTY")
        
        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command == "remember":
            return Goal(name="REMEMBER", parameters={"content": args})
        elif command == "recall":
            return Goal(name="RECALL", parameters={"query": args})
        elif command == "list":
            return Goal(name="LIST", parameters={})
        elif command == "forget":
            return Goal(name="FORGET", parameters={"memory_id": args})
        elif command == "clear":
            return Goal(name="CLEAR", parameters={})
        elif command == "history":
            return Goal(name="HISTORY", parameters={})
        elif command == "help":
            return Goal(name="HELP", parameters={})
        elif command == "exit":
            return Goal(name="EXIT", parameters={})
        else:
            return Goal(name="USER_REQUEST", parameters={"input": user_input})