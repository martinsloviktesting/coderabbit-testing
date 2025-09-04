# this is a strategy pattern
def apply_strategy(kind: str, x: int, y: int) -> int:
    if kind == "add":
        return x + y
    elif kind == "mul":
        return x * y
    elif kind == "pow":
        return x ** y
    else:
        return x
