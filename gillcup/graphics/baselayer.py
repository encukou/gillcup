
from contextlib import contextmanager

import pyglet
from pyglet.gl import *

from gillcup.animatedobject import AnimatedObject
from gillcup.action import FunctionAction
from gillcup.graphics import helpers

class BaseLayer(AnimatedObject):
    """Base class for Gillcup's graphics objects

    Provides with a common set of attributes and common options.

    All arguments except parent should be given as keyword arguments.

    :param parent: The parent Layer. Leave None for no parent. Note that only
            Layers, not just any graphics objects, can act as a parent.
    :param timer: The timer to use for animations. Leave None to use
            the parent's timer, or None if no parent
    :param toBack: If true, the object will be prepended to the parent's list
            of children, and will thus appear behind them. By default, it is
            appended.
    :param name: A name for the layer. Shows up in debug dumps.

    The following arguments become instance attributes, and can be then
    animated:

    :param position: The position of the anchorPoint , relative to the parent
    :param anchorPoint: The reference point, around which rotations and scaling
            is done. Also, position references the anchorPoint.
    :param scale: The scale of the object, relative to the default (1, 1).
            Affects all children.
    :param size: The size of the object. Is dependent on the object type, but
            usually has the same effect as scale, except it does not affect
            children. Conceptually, size is the inherent size of the object,
            while scale specifies how much it is stretched.
    :param rotation: The rotation of the object, in counterclockwise degrees.
    :param opacity: The opacity of the object, a float in the range [0..1]
    :param color: The color of the object.
    """
    getDrawContext = helpers.nullContextManager

    def __init__(self,
            parent=None,
            position=(0, 0, 0),
            anchorPoint=(0, 0, 0),
            scale=(1, 1, 1),
            size=(1, 1),
            rotation=0,
            opacity=1,
            color=(1, 1, 1),
            toBack=False,
            timer=None,
            name=None,
        ):
        super(BaseLayer, self).__init__()
        self.position = position
        self.anchorPoint = anchorPoint
        self.rotation = rotation
        self.scale = scale
        self.opacity = opacity
        self.parent = None
        self.reparent(parent, toBack)
        self.color = color
        self.size = size
        self.name = name
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

    @property
    def _hidden(self):
        return self.dead or self.opacity <= 0 or not any(self.scale)

    @contextmanager
    def _transformationManager(self, transformation):
        transformation.push()
        try:
            self.changeMatrix(transformation)
            yield
        finally:
            transformation.pop()

    def do_draw(self, transformation, **kwargs):
        """Draw this object

        This method sets up the transformation matrix and calls draw().

        Subclasses will usually want to override draw(), not this method.
        """
        # XXX: Make sure tree is never deeper than 32
        if self._hidden:
            return self.dead
        with self._transformationManager(transformation):
            with self.getDrawContext(kwargs):
                rv = self.draw(transformation=transformation, **kwargs)
                return self.dead

    def changeMatrix(self, transformation):
        """Set up the transformation matrix for object
        """
        transformation.translate(*helpers.extend_tuple(self.position))
        transformation.rotate(self.rotation, 0, 0, 1)
        transformation.scale(*helpers.extend_tuple(self.scale, default=1))
        transformation.translate(*(
                -x for x in helpers.extend_tuple(self.anchorPoint)
            ))

    def do_hitTest(self, transformation, **kwargs):
        if not self._hidden:
            with self._transformationManager(transformation):
                return self.hitTest(transformation=transformation, **kwargs)

    def hitTest(self, **kwargs):
        """Redefine to get hit test notifications. Return true to claim the hit.
        """
        pass

    def draw(self, **kwargs):
        """Draw this object. Overridden in subclasses.
        """
        pass

    def dump(self, indentLevel=0):
        """Dump this object to the standard output. A debugging tool.
        """
        print '  ' * indentLevel + ' '.join(x for x, c in [
                (type(self).__name__, True),
                (u'"{0}"'.format(self.name), self.name),
                (u"@{0}".format(self.position), self.position != (0, 0, 0)),
                (u"x{0}".format(self.scale), self.scale != (1, 1, 1)),
                (u"a{0}".format(self.anchorPoint), self.anchorPoint != (0,0,0)),
                (u"s{0}".format(self.size), self.size != (1, 1)),
                (u"o{0}".format(self.opacity), self.opacity != 1),
            ] if c)
        self._dump_effects(indentLevel + 1)
        for child in self.children:
            child.dump(indentLevel + 1)

    def die(self):
        """Destroy this object

        Sets up to detach from the parent on the next frame, and calls die()
        on all children.
        """
        self.dead = True
        self.parent = None
        for child in self.children:
            if child.parent is self:
                child.die()

    def reparent(self, newParent, toBack=False):
        """Set a new parent

        Remove this object from the current parent (if there is one) and
        attech to a new one. The toBack argument is the same as for __init__.
        """
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
        """Return an Action that calls raparent() when run"""
        return FunctionAction(self.reparent, newParent, toBack)

    def _applyFunc(func):
        def wrapped(self, *args, **kwargs):
            dt = kwargs.pop('dt', 0)
            return self.apply(func(self, *args, **kwargs), dt=dt)
        if func.func_name != 'wrapped':
            wrapped.__doc__ = "Call self.apply(self.%s(), dt=dt)" % (
                    func.func_name,
                )
        return wrapped

    def _addMoreArgs(func, **moreKwargs):
        def wrapped(*args, **kwargs):
            kwargs.update(moreKwargs)
            return func(*args, **kwargs)
        if func.func_name != 'wrapped':
            wrapped.__doc__ = "Call %s with %s" % (
                    func.func_name,
                    ', '.join('%s=%s' % (a, b) for a, b in moreKwargs.items())
                )
        return wrapped

    @property
    def width(self):
        """size[0]"""
        return helpers.extend_tuple(self.size)[0]

    @property
    def height(self):
        """size[1]"""
        return helpers.extend_tuple(self.size)[1]

    def rotationTo(self, value, **animargs):
        """Return Action for animating rotation to the given value
        """
        return self.animation('rotation', value, **animargs)

    rotateTo = _applyFunc(rotationTo)
    rotationBy = _addMoreArgs(rotationTo, additive=True)
    rotateBy = _applyFunc(rotationBy)

    def scalingTo(self, width, height=None, **animargs):
        """Return Action for animating scale to the given value
        """
        if height is None:
            height = width
        return self.animation('scale', (width, height), **animargs)

    scaleTo = _applyFunc(scalingTo)
    scalingBy = _addMoreArgs(scaleTo, multiplicative=True)
    scaleBy = _applyFunc(scalingBy)

    def fadingTo(self, opacity, **animargs):
        """Return Action for animating opacity to the given value
        """
        return self.animation('opacity', opacity, **animargs)

    fadeTo = _applyFunc(fadingTo)
    fadingBy = _addMoreArgs(fadingTo, multiplicative=True)
    fadeBy = _applyFunc(fadingBy)

    def movementTo(self, x, y, **animargs):
        """Return Action for animating position to the given value
        """
        return self.animation('position', (x, y), **animargs)

    moveTo = _applyFunc(movementTo)
    movementBy = _addMoreArgs(movementTo, additive=True)
    moveBy = _applyFunc(movementBy)

    def anchorMovementTo(self, x, y, **animargs):
        """Return Action for animating anchorPoint to the given value
        """
        return self.animation('position', (x, y), **animargs)

    moveAnchorTo = _applyFunc(anchorMovementTo)
    anchorMovementBy = _addMoreArgs(anchorMovementTo, additive=True)
    moveAnchorBy = _applyFunc(anchorMovementBy)

    def resizingTo(self, w, h, **animargs):
        """Return Action for animating size to the given value
        """
        return self.animation('size', (w, h), **animargs)

    resizeTo = _applyFunc(resizingTo)
    resizingBy = _addMoreArgs(resizingTo, multiplicative=True)
    resizeBy = _applyFunc(resizingBy)

    _applyFunc = classmethod(_applyFunc)
    _addMoreArgs = classmethod(_addMoreArgs)

    def getColor(self, kwargs):
        """Get color to draw with."""
        color = helpers.extend_tuple_copy(self.color)
        parentColor = kwargs.get('color', (1, 1, 1))
        return helpers.tuple_multiply(color, parentColor)

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
