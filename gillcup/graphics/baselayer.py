
from contextlib import contextmanager

import pyglet
from pyglet.gl import *

from gillcup.animatedobject import AnimatedObject
from gillcup.action import FunctionAction
from gillcup.graphics import helpers

class BaseLayer(AnimatedObject):
    getDrawContext = helpers.nullContextManager

    def __init__(self,
            parent=None,
            position=(0, 0, 0),
            anchorPoint=(0, 0, 0),
            scale=(1, 1, 1),
            size=(1, 1),
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
        self.parent = None
        self.reparent(parent)
        self.size = size
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
        print '  ' * indentLevel + ' '.join(x for x, c in [
                (type(self).__name__, True),
                ("@{0}".format(self.position), self.position != (0, 0, 0)),
                ("x{0}".format(self.scale), self.scale != (1, 1, 1)),
                ("a{0}".format(self.anchorPoint), self.anchorPoint != (0,0,0)),
                ("s{0}".format(self.size), self.size != (1, 1)),
                ("o{0}".format(self.opacity), self.opacity != 1),
            ] if c)
        for child in self.children:
            child.dump(indentLevel + 1)

    def die(self):
        self.dead = True
        self.parent = None
        for child in self.children:
            if child.parent is self:
                child.die()

    def reparent(self, newParent, toBack=False):
        if self.parent:
            self.parent.children = [
                    c for c in self.parent.children if c is not self
                ]
            self.parent = None
        if newParent:
            if toBack:
                newParent.children.insert(0, self)
            else:
                newParent.children.append(self)
            self.parent = newParent

    def reparenting(self, newParent, toBack=False):
        return FunctionAction(self.reparent, newParent, toBack)

    def _applyFunc(func):
        def wrapped(self, *args, **kwargs):
            dt = kwargs.pop('dt', 0)
            return self.apply(func(self, *args, **kwargs), dt=dt)
        return wrapped

    def _addMoreArgs(func, **moreKwargs):
        def wrapped(*args, **kwargs):
            kwargs.update(moreKwargs)
            return func(*args, **kwargs)
        return wrapped

    @property
    def width(self):
        return helpers.extend_tuple(self.size)[0]

    @property
    def height(self):
        return helpers.extend_tuple(self.size)[1]

    def rotationTo(self, value, **animargs):
        return self.animation('rotation', value, **animargs)

    rotateTo = _applyFunc(rotationTo)
    rotationBy = _addMoreArgs(rotationTo, additive=True)
    rotateBy = _applyFunc(rotationBy)

    def scalingTo(self, width, height=None, **animargs):
        if height is None:
            height = width
        return self.animation('scale', (width, height), **animargs)

    scaleTo = _applyFunc(scalingTo)
    scalingBy = _addMoreArgs(scaleTo, multiplicative=True)
    scaleBy = _applyFunc(scalingBy)

    def fadingTo(self, opacity, **animargs):
        return self.animation('opacity', opacity, **animargs)

    fadeTo = _applyFunc(fadingTo)
    fadingBy = _addMoreArgs(fadingTo, multiplicative=True)
    fadeBy = _applyFunc(fadingBy)

    def movementTo(self, x, y, **animargs):
        return self.animation('position', (x, y), **animargs)

    moveTo = _applyFunc(movementTo)
    movementBy = _addMoreArgs(movementTo, additive=True)
    moveBy = _applyFunc(movementBy)

    def anchorMovementTo(self, x, y, **animargs):
        return self.animation('position', (x, y), **animargs)

    moveAnchorTo = _applyFunc(anchorMovementTo)
    anchorMovementBy = _addMoreArgs(anchorMovementTo, additive=True)
    moveAnchorBy = _applyFunc(anchorMovementBy)

    def resizingTo(self, w, h, **animargs):
        return self.animation('size', (w, h), **animargs)

    resizeTo = _applyFunc(resizingTo)
    resizingBy = _addMoreArgs(resizingTo, multiplicative=True)
    resizeBy = _applyFunc(resizingBy)

    _applyFunc = classmethod(_applyFunc)
    _addMoreArgs = classmethod(_addMoreArgs)


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
