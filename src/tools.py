def to_hex(pack: bytes) -> str:
    return " ".join(f"{x:02X}" for x in pack)


def print_hex(msg: bytes):
    print(to_hex(msg))


def add_indent(text: str, indent: int = 4) -> str:
    return "\n".join(" " * indent + line for line in text.split("\n"))


def print_with_indent(values: object, indent: int = 4) -> None:
    text = add_indent(values.__str__(), indent)
    print(text)
