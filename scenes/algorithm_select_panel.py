from ursina import Entity, Text, color, destroy
from ursina.models.procedural.quad import Quad

from ui.menu_button import MenuTextButton
from ui.theme import (
    FONT_BOLD,
    FONT_REGULAR,
    PRIMARY,
    WHITE,
    GRAY,
    DARK_PANEL,
)


class AlgorithmSelectPanel(Entity):

    def __init__(self, parent, on_algorithm_selected, on_close):
        super().__init__(parent=parent)

        self.on_algorithm_selected = on_algorithm_selected
        self.on_close = on_close

        font_kwargs = {"font": FONT_REGULAR} if FONT_REGULAR else {}
        font_bold_kwargs = {"font": FONT_BOLD or FONT_REGULAR} if (FONT_BOLD or FONT_REGULAR) else {}

        self.border = Entity(
            parent=self,
            model=Quad(radius=0.05, aspect=0.59 / 0.67),
            color=color.rgba32(0, 210, 255, 60),
            scale=(0.59, 0.67),
            position=(0, -0.04, -0.03),
        )

        self.background = Entity(
            parent=self,
            model=Quad(radius=0.05, aspect=0.58 / 0.66),
            color=color.rgba32(10, 16, 28, 240),
            scale=(0.58, 0.66),
            position=(0, -0.04, -0.04),
        )

        self.title = Text(
            parent=self,
            text="SELECT SOLVER ALGORITHM",
            origin=(0, 0),
            position=(0, 0.21, -0.08),
            scale=1.05,
            color=PRIMARY,
            **font_bold_kwargs,
        )

        self.subtitle = Text(
            parent=self,
            text="Choose an AI search strategy for this level",
            origin=(0, 0),
            position=(0, 0.15, -0.08),
            scale=0.62,
            color=GRAY,
            **font_kwargs,
        )

        algorithms = [
            ("BFS - Breadth First Search", "BFS"),
            ("IDS - Iterative Deepening", "IDS"),
            ("UCS - Uniform Cost Search", "UCS"),
            ("A* - A-Star Heuristic", "ASTAR"),
        ]

        self.algo_buttons = []
        for index, (display_name, algo_id) in enumerate(algorithms):
            btn_y = 0.06 - index * 0.095
            btn = MenuTextButton(
                text=display_name,
                font=FONT_REGULAR,
                parent=self,
                position=(0, btn_y, -0.08),
                text_scale=0.92,
                label_origin=(0, 0),
                hitbox_origin=(0, 0),
                hitbox_width=0.46,
                on_click=(lambda aid=algo_id: self.select_algorithm(aid)),
            )
            self.algo_buttons.append(btn)

        self.close_button = MenuTextButton(
            text="CANCEL",
            font=FONT_REGULAR,
            parent=self,
            position=(0, -0.31, -0.08),
            text_scale=0.85,
            label_origin=(0, 0),
            hitbox_origin=(0, 0),
            hitbox_width=0.22,
            on_click=self.on_close,
        )

    def select_algorithm(self, algorithm_name):
        if self.on_algorithm_selected:
            self.on_algorithm_selected(algorithm_name)
