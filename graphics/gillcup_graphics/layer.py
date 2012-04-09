
from __future__ import division

from gillcup_graphics.base import GraphicsObject


class Layer(GraphicsObject):
    def __init__(self, parent=None, **kwargs):
        super(Layer, self).__init__(parent, **kwargs)
        self.children = []

    def draw(self, transformation, **kwargs):
        transformation.translate(*self.anchor)
        self.children = [
                c for c in self.children if c.do_draw(
                        transformation=transformation,
                        **kwargs
                    )
            ]


class DecorationLayer(Layer):
    def do_hit_test(self, transformation, **kwargs):
        return ()
