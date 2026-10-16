"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""


class AlgorithmSelectPanel:

    def __init__(self, parent, on_algorithm_selected, on_close):
        raise NotImplementedError

    def select_algorithm(self, algorithm_name):
        raise NotImplementedError
