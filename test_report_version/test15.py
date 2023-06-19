# 같은 파일내에서 오버라이딩

class Parent:
    def functionName():
        print("hello parent")
        pass


class Child(Parent):
    def __init__(self) -> None:
        super().__init__()

    def functionName():
        print("hello child")
        pass
