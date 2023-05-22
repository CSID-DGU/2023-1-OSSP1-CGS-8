class Rectangle:
    count = 0  # 클래스 변수

    # 초기자(initializer)
    def __init__(self, width, height):  # self.* : 인스턴스변수
        self.width = width
        self.height = height
        Rectangle.count += 1

    # 메서드
    def cal__carea(self):
        area = self.width * self.height
        return area
