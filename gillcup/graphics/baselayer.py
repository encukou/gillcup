
from contextlib import contextmanager

import pyglet
from pyglet.gl import *

from gillcup.animatedobject import AnimatedObject
from gillcup.graphics import helpers

class BaseLayer(AnimatedObject):
    getDrawContext = helpers.nullContextManager

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
        super(BaseLayer, self).__init__()
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
            while obj and not obj.timer:
                obj = obj.parent
            if obj is None:
                self.timer = DynamicTimer(self)
            else:
                self.timer = obj.timer
        if parent:
            if toBack:
                parent.children.insert(0, self)
            else:
                parent.children.append(self)
        self.children = ()
        self.dead = False

    def do_draw(self, **kwargs):
        # XXX: Make sure tree is never deeper than 32
        gl.glPushMatrix()
        try:
            self.changeMatrix()
            with self.getDrawContext(kwargs):
                rv = self.draw(**kwargs)
                return self.dead
        finally:
            gl.glPopMatrix()

    def changeMatrix(self):
        gl.glTranslatef(*helpers.extend_tuple(self.position))
        gl.glRotatef(self.rotation, 0, 0, 1)
        gl.glScalef(*helpers.extend_tuple(self.scale, default=1))
        gl.glTranslatef(*(
                -x for x in helpers.extend_tuple(self.anchorPoint)
            ))

    def draw(self, **kwargs):
        # Return a dict to modify kwargs passed to children
        pass

    def dump(self, indentLevel=0):
        print '  ' * indentLevel + ' '.join([
                type(self).__name__,
                "@{0}".format(self.position),
                "x{0}".format(self.scale),
                "o{0}".format(self.opacity),
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

    def scaleBy(self, width, height=None, **animargs):
        self.scaleTo(width, height, multiplicative=True, **animargs)

    def fadeTo(self, opacity, **animargs):
        self.animate('opacity', opacity, **animargs)

class DynamicTimer(object):
    # XXX: Untested
    def __init__(self, obj):
        self.obj = obj

    def _get_timer(self):
        obj = self.obj
        while obj and isinstance(obj.timer, DynamicTimer):
            obj = obj.parent
        if not obj:
            raise RuntimeError('%s has no timer' % self.obj)
        return obj.timer

    @property
    def time(self):
        return self._get_timer().time

    @property
    def schedule(self):
        return self._get_timer().schedule
