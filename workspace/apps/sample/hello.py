"""サンプルプロジェクト。AIエージェントの読み書き・編集・検証の動作確認用。"""


def greet(name: str) -> str:
    """名前を受け取って挨拶を返す。"""
    return f"こんにちは、{name}さん！"


def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    print(greet("とも"))
    print("1 + 2 =", add(1, 2))
