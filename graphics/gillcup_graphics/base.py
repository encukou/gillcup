
from __future__ import division

import gillcup

class GraphicsObject(object):
    """Base class for gillcup_graphics objects
    """
    def __init__(self,
            parent=None,
            position=(0, 0, 0),
            anchor=(0, 0, 0),
            scale=(1, 1, 1),
            size=(1, 1),
            opacity=1,
            rotation=0,
            color=(1, 1, 1),
            to_back=False,
            name=None,
        ):
        super(GraphicsObject, self).__init__()
        self.position = position
        self.anchor = anchor
        self.rotation = rotation
        self.scale = scale
        self.parent = None
        self.reparent(parent, to_back)
        self.color = color
        self.size = size
        self.opacity = opacity
        self.name = name
        self.children = ()
        self.dead = False

    x, y, z = position = gillcup.TupleProperty(0, 0, 0)
    anchor_x, anchor_y, anchor_z = anchor = gillcup.TupleProperty(0, 0, 0)
    scale_x, scale_y, scale_z = scale = gillcup.TupleProperty(1, 1, 1)
    width, height = size = gillcup.TupleProperty(1, 1)
    rotation = gillcup.AnimatedProperty(0)
    opacity = gillcup.AnimatedProperty(1)
    color = gillcup.TupleProperty(1, 1, 1)

    @property
    def _hidden(self):
        return self.dead or self.opacity <= 0 or not any(self.scale)

    def do_draw(self, transformation, **kwargs):
        """Draw this object

        This method sets up the transformation matrix and calls draw().

        Subclasses will usually want to override draw(), not this method.
        """
        # XXX: Make sure tree is never deeper than 32
        if self.dead:
            return False
        elif self._hidden:
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
        if not self._hidden:
            with transformation.state:
                if self.hit_test(transformation=transformation, **kwargs):
                    for child in self.children:
                        for res in child.do_hit_test(transformation, **kwargs):
                            yield res
                    yield self

    def hit_test(self, **kwargs):
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
