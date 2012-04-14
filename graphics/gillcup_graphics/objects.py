"""Drawable objects

This module provides basic objects you can draw and animate.

Perhaps the most important of these is the Layer, which does not have a
graphical representation but can contain other objects, such as Rectangles,
Sprites or other Layers.
The containing Layer is called the ``parent`` of the contained object.
Graphics objects are thus arranged in a scene tree.
The tree is rooted at a parent-less Layer[#f1]_, which will usually be shown in
a Window.

Each object has a lot of AnimatedProperties that control its position on the
screen (relative to its parent), and properties like color and opacity.

The objects are compatible with 3D transformations, but anything outside the
xy-plane needs custom OpenGL camera setup.

.. [#f1] To be precise, the root may also be another object. It's just not
    terribly useful that way.
"""

from __future__ import division

import sys
import pyglet
from pyglet import gl

import gillcup
from gillcup import properties
from gillcup.effect import Effect


class GraphicsObject(object):
    """Base class for gillcup_graphics objects
    """
    def __init__(self,
            parent=None,
            to_back=False,
            name=None,
            **kwargs):
        super(GraphicsObject, self).__init__()
        self.parent = None
        self.reparent(parent, to_back)
        self.name = name
        self.children = ()
        self.dead = False
        if 'anchor' not in kwargs:
            RelativeAnchor(self).apply_to(self, 'anchor')
        self.set_animated_properties(kwargs)

    x, y, z = position = properties.VectorProperty(3,
        docstring="""The object's position in space

        This is an offset between the parent's anchor and this object's own
        anchor, in the parent's coordinates.""")
    anchor_x, anchor_y, anchor_z = anchor = properties.VectorProperty(3,
        docstring="""A point that represents this object for positioning""")
    scale_x, scale_y, scale_z = scale = properties.ScaleProperty(3,
        docstring="""The object's scale""")
    width, height = size = properties.ScaleProperty(2,
        docstring="""The object's natural size""")
    rotation = gillcup.AnimatedProperty(0,
        docstring="""Rotation about the object's anchor""")
    opacity = gillcup.AnimatedProperty(1,
        docstring="""Opacity of the object""")
    color = red, green, blue = gillcup.TupleProperty(1, 1, 1,
        docstring="""Color or tint of the object""")
    relative_anchor = properties.VectorProperty(3,
        docstring="""Anchor of the object relative to the object's size

        When ``relative_anchor`` is (1, 1), the ``anchor`` is in the
        object's upper right corner. When ``relative_anchor`` is (0.5, 0.5),
        ``anchor`` will me in the middle.

        This property is only effective if ``anchor`` is not set by other
        means.
        """)
    relative_anchor_x, relative_anchor_y, relative_anchor_z = relative_anchor

    def set_animated_properties(self, kwargs):
        """Initializes animated properties with keyword arguments"""
        unknown = []
        for name, value in kwargs.items():
            try:
                prop = getattr(type(self), name)
            except AttributeError:
                unknown.append(name)
            else:
                if isinstance(prop, gillcup.AnimatedProperty):
                    setattr(self, name, value)
                else:
                    unknown.append(name)
        if unknown:
            raise TypeError('Unknown keyword arguments: %s' %
                    ', '.join(unknown))

    def is_hidden(self):
        """Return true if this layer shouldn't be shown"""
        return self.dead or self.opacity <= 0 or not any(self.scale)

    def do_draw(self, transformation, **kwargs):
        """Draw this object

        This method sets up the transformation matrix and calls draw().
        If this method returns false, the object is removed from its parent.

        Subclasses will usually want to override draw(), not this method.
        """
        # XXX: Make sure tree is never deeper than 32
        if self.dead:
            return False
        elif self.is_hidden():
            return True
        with transformation.state:
            self.change_matrix(transformation)
            self.draw(transformation=transformation, **kwargs)
        return True

    def draw(self, **kwargs):
        """Draw this object. Overridden in subclasses.
        """
        pass

    def change_matrix(self, transformation):
        """Set up the transformation matrix for object
        """
        transformation.translate(*self.position)
        transformation.rotate(self.rotation, 0, 0, 1)
        transformation.scale(*self.scale)
        transformation.translate(*(-x for x in self.anchor))

    def do_hit_test(self, transformation, **kwargs):
        """Perform a hit test on this object and any children"""
        if self.hit_test(transformation=transformation, **kwargs):
            yield self

    def hit_test(self, **kwargs):
        """Perform a hit test on this object only"""
        return True

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

    def reparent(self, new_parent, to_back=False):
        """Set a new parent

        Remove this object from the current parent (if there is one) and
        attech to a new one. The to_back argument is the same as for __init__.
        """
        assert new_parent is not self
        if self.parent:
            self.parent.children = [
                    c for c in self.parent.children if c is not self
                ]
            self.parent = None
        if new_parent:
            if to_back:
                new_parent.children.insert(0, self)
            else:
                new_parent.children.append(self)
            self.parent = new_parent


class RelativeAnchor(Effect):
    """Put on an ``anchor`` property to make it respect relative_anchor"""
    def __init__(self, text):
        super(RelativeAnchor, self).__init__()
        self.text = text

    @property
    def value(self):
        """Calculate the value"""
        return (self.text.width * self.text.relative_anchor_x,
            self.text.height * self.text.relative_anchor_y)


class Layer(GraphicsObject):
    """A container for GraphicsObjects"""
    def __init__(self, parent=None, **kwargs):
        super(Layer, self).__init__(parent, **kwargs)
        self.children = []

    def do_hit_test(self, transformation, **kwargs):
        if not self.is_hidden():
            with transformation.state:
                if self.hit_test(transformation=transformation, **kwargs):
                    for child in self.children:
                        for res in child.do_hit_test(transformation, **kwargs):
                            yield res
                    yield self

    def draw(self, transformation, **kwargs):
        transformation.translate(*self.anchor)
        self.children = [
                c for c in self.children if c.do_draw(
                        transformation=transformation,
                        **kwargs
                    )
            ]


class DecorationLayer(Layer):
    """A Layer that does not respond to hit tests

    Objects in this layer will not be interactive.
    """
    def do_hit_test(self, transformation, **kwargs):
        return ()


class Rectangle(GraphicsObject):
    """A box of color"""

    vertices = (gl.GLfloat * 8)(0, 0, 1, 0, 1, 1, 0, 1)

    def draw(self, transformation, **kwargs):
        transformation.scale(self.width, self.height, 1)
        color = self.color + (self.opacity, )
        gl.glColor4fv((gl.GLfloat * 4)(*color))
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glVertexPointer(2, gl.GL_FLOAT, 0, self.vertices)
        gl.glDrawArrays(gl.GL_QUADS, 0, 4)


class Sprite(GraphicsObject):
    """An image"""
    def __init__(self, parent, texture, **kwargs):
        self.sprite = pyglet.sprite.Sprite(texture.get_texture())
        kwargs.setdefault('size', (self.sprite.width, self.sprite.height))
        super(Sprite, self).__init__(parent, **kwargs)

    def draw(self, **kwargs):
        self.sprite.opacity = self.opacity * 255
        self.sprite.color = tuple(int(c * 255) for c in self.color)
        gl.glScalef(
                self.width / self.sprite.width,
                self.height / self.sprite.height,
                1,
            )
        self.sprite.draw()


class Text(GraphicsObject):
    """A text label"""
    def __init__(self,
            parent,
            text,
            font_name=None,
            **kwargs
        ):
        super(Text, self).__init__(parent, **kwargs)
        self.text = text
        self.font_name = font_name
        self.sprite = pyglet.text.Label(
                text,
                font_name=font_name,
                font_size=self.font_size,
            )

    font_size = gillcup.AnimatedProperty(72)
    characters_displayed = gillcup.AnimatedProperty(sys.maxint)

    def setup(self):
        """Assign the properties to the underlying Pyglet label"""
        if self.font_name:
            self.sprite.font_name = self.font_name
        self.sprite.font_size = self.font_size

    def draw(self, **kwargs):
        self.setup()
        color = self.color + (self.opacity, )
        self.sprite.color = [int(a * 255) for a in color]
        self.sprite.text = self.text[:int(self.characters_displayed)]
        self.sprite.draw()
        self.sprite.text = self.text

    @property
    def size(self):
        """The natural size of the text

        This property is not animated, and cannot be changed.

        Returns the size of the entire text, i.e. doesn't take
        ``characters_displayed`` into account.
        """
        self.text.setup()
        sprite = self.text.sprite
        sprite.text = self.text.text
        return (sprite.content_width, sprite.content_height)
