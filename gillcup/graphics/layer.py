
import pyglet
from pyglet.gl import *

from gillcup.animatedobject import AnimatedObject
from gillcup.graphics import helpers

class Layer(AnimatedObject):
    handlesOpacity = False

    def __init__(self,
            parent=None,
            position=(0, 0),
            anchorPoint=(0, 0),
            scale=(1, 1, 1),
            rotation=0,
            opacity=1,
            toBack=False,
            timer=None,
        ):
        super(Layer, self).__init__()
        self.position = position
        self.anchorPoint = anchorPoint
        self.rotation = rotation
        self.scale = scale
        self.opacity = opacity
        self.parent = parent
        if timer:
            self.timer = timer
        else:
            obj = self.parent
            while not obj.timer:
                obj = obj.parent
            self.timer = obj.timer
        if parent:
            if toBack:
                parent.children.insert(0, self)
            else:
                parent.children.append(self)
        self.children = []
        self.dead = False

    def do_draw(self):
        # XXX: Make sure tree is never deeper than 32
        gl.glPushMatrix()
        try:
            self.changeMatrix()
            rv = self.draw()
            self.children = [c for c in self.children if not c.do_draw()]
            if rv is None:
                return self.dead
            else:
                return rv
        finally:
            gl.glPopMatrix()

    def changeMatrix(self):
        gl.glTranslatef(*helpers.extend_tuple(self.position))
        gl.glRotatef(self.rotation, 0, 0, 1)
        gl.glScalef(*helpers.extend_tuple(self.scale, default=1))
        gl.glTranslatef(*(
                -x for x in helpers.extend_tuple(self.anchorPoint)
            ))

    def draw(self):
        # Return a true value to delete this Layer from its parent
        pass

    def dump(self, indentLevel=0):
        print '  ' * indentLevel + ' '.join([
                type(self).__name__,
                "@{0}".format(self.position),
                "x{0}".format(self.scale),
            ])
        for child in self.children:
            child.dump(indentLevel + 1)

    def die(self):
        self.dead = True
        self.parent = None
        for child in self.children:
            if child.parent is self:
                child.die()

    def rotateBy(self, value, **animargs):
        self.animate('rotation', value, additive=True, **animargs)

    def scaleTo(self, width, height=None, **animargs):
        if height is None:
            height = width
        self.animate('scale', (width, height), **animargs)
