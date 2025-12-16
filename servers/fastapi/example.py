from manim import *

class Demo(Scene):
    def construct(self):
        d = Dot()
        self.play(GrowFromCenter(d))
        self.wait(0.1)