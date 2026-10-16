"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""


class TutorialScene:

    def __init__(self, on_back):
        raise NotImplementedError

    def create_tutorial_items(self):
        raise NotImplementedError

    def input(self, key):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def scroll_by(self, amount):
        raise NotImplementedError

    def go_back(self):
        raise NotImplementedError

    def on_destroy(self):
        raise NotImplementedError
