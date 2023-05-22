class rectangle:
    count = 0  # 클래스 변수

    # 초기자(initializer)
    def __init__(self, width, height):  # self.* : 인스턴스변수
        self.width = width
        self.height = height
        rectangle.count += 1

    # 메서드
    def CalcArea(self):
        area = self.width * self.height
        return area
