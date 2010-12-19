The First Steps: Drawing a Rectangle
====================================

This section is for beginner animators (although Python knowledge is required).
If you have some experience with object-oriented graphics, skip to the last
section and see if you understand the code there.

Running Code
------------

Let's get some results! Create a Python file and paste the following into it::

    from gillcup.graphics import mainwindow
    from gillcup.graphics.layer import Layer
    rootLayer = Layer()


    mainwindow.run(rootLayer)

When you run it, you will get a blank window.

Let's see what those four lines mean::

    from gillcup.graphics import mainwindow

This imports the :doc:`mainwindow <pygraphicsmainwindow>` module, which has
convenience functions for displaying animations you might create.
You can use them as-is, or look at the code for an example of how to write your
own.

Next up::

    from gillcup.graphics.layer import Layer
    rootLayer = Layer()

Here we use the :doc:`Layer <pygraphicslayer>` class. Think of a Layer as the
term is used in image processing application: a transparent sheet on which
objects can be drawn. In this case, we initialize an empty Layer and nothing
more. That's why our window was empty!

On to the last line::

    mainwindow.run(rootLayer)

This is where we call a convenience function to “run” our Layer, that is,
display it and any animations that are on it. There's not much to see now,
but that's about to change in the next section!


Displaying Things
-----------------

In this section, we will draw a rectangle in the middle of the window.

Modify your Python file to read::

    from gillcup.graphics import mainwindow
    from gillcup.graphics.layer import Layer
    from gillcup.graphics.colorrect import ColorRect
    rootLayer = Layer()

    rect = ColorRect(rootLayer)

    mainwindow.run(rootLayer)

When you run this, you will see that the window is now grey.

There are two added lines: an import and an instantiation of a ColorRect class.
As the name suggests, the ColorRect class represents a colored rectangle.
In this case, the rectangle is grey, and completely covers the window.
We'll change that later; first we need to explain a debugging call that will
be useful later.


Scene Trees
-----------

The argument we gave to our ColorRect is the “parent”. Every Gillcup graphics
object can have a parent layer, which is given as the first argument to the
constructor. This makes the object attach to its parent.

Of course, Layers themselves are also such objects, which can lead to complex
structures called “scene trees”. If you're ever confused about the structure
of what is displayer on the screen, you can call::

    rootLayer.dump()

This will print out the scene tree to standard output. In our case, we have::

    Layer x(768, 576)
      ColorRect

This is a very simple scene tree consisting of a Layer scaled to 768x576
(the size of the window), and a ColorRect. The indentation shows the ColorRect
is contained in the Layer.


Color
-----

I don't know about you, but I don't like grey too much. It would be much more
interesting to color our screen, say, blue. Of course I wouldn't say that if
it wasn't ridiculously easy to do; just change the ColorRect call to::

    rect = ColorRect(rootLayer, color=(0, 0, 1))

and run the script again. Looking at the output, maybe this particular hue
wasn't such a good idea, but keep with me.

This example shows us two things:

-   We can give named arguments to constructors of Gillcup graphics objects to
    set attributes such as color.
-   Colors in Gillcup are given as RGB triples of floats in the 0..1 range.

These are true generally, although I might add that setting attributes also
works the Python way, as you can test by adding the following line just above
the mainwindow.run() call::

    rect.color = (1, 1, 0)  # No! Yellow!


Position and Scale
------------------

There are more attributes that you can set than colors, of course. For
animations, we will want to make ourselves familiar with three of these:
position, scale, and anchorPoint.

First, an introduction to Gillcup's geometry: The “x” axis points right,
and the “y” axis points up (i.e. not down as you may be used to from GUI
toolkits). The origin — that is, the (0, 0) point – is in the lower left
of the window. This is standard in math, OpenGL and Pyglet.

The mainwindow.run() scales (resizes) its root layer so that the (1, 1) point
is in the upper right corner of the window.

The ColorRect class introduced earlier has the same geometry as the screen:
(0, 0) is in the lower left corner, (1, 1) in the upper right. It's easy to see
now why our rectangle covers the screen.

Let's now make the rectangle a bit smaller, so we can see that it is actually
a rectangle. Change the ColorRect call to this::

    rect = ColorRect(rootLayer, scale=(0.5, 0.5))

This will resize the rectangle by 1/2 in each direction, so that it rectangle
only covers a quarter of the screen. But, the resize is relative to the origin,
the lower left corner of the window. Wouldn't it be better to have the
rectangle centered?

To change the point a graphict object scales around, we set the anchorPoint
property. You can change our call to::

    rect = ColorRect(rootLayer, scale=(0.5, 0.5), anchorPoint=(0.5, 0.5))

As you can see, that didn't work. This is because anchorPoint is not just
the central point for scaling, but also for rotations, and, most importantly,
for the position of the object.

So, we will also need to set the position attribute. The position specifies
where, relative to the parent, an object's anchorPoint is. We would like
it to be in the middle of the layer.

Our instantiation line is getting longer and longer, so we may want to split
it in seeral pieces. (In real life, if you find out you are reusing the
same arguments over and over, you're encouraged to subclass or make a factory
function.)::

    rect = ColorRect(rootLayer)
    rect.scale = (0.5, 0.5)
    rect.anchorPoint = (0.5, 0.5)
    rect.position = (0.5, 0.5)

And now, we have a nice rectangle centered on the screen!


Rotation and Opacity
--------------------

The final two attributes I want to cover are rotation and opacity. These
are straightforward to use, as they are just numbers. Just keep in mind that
the rotation is in degrees. (Radians are, unfortunately, a bit unwieldy for
animation use.) So, for a see-through rectangle on its side, add these::

    rect.rotation = 45
    rect.opacity = 0.75

What is this?, I hear you say. It's not a rectangle any more! Read the next
section for an explanation (or excuse, rather).

A Note on Aspect Ratio
----------------------

Gillcup does not care about the spect ratio. It is your own
responsibility to scale your layers to the correct size, or use a rectangular
window (using the width and height arguments to mainwindow.run()).

The reason is that there is no universally right solution to this problem;
letting you fix it hovewer you want is better than having you undo Gillcup's
fix first and then aply your own.


This Lesson's Code
------------------

Here is the complete code we've come up with, commented for those that skipped
to here::

    # Boilerplate
    from gillcup.graphics import mainwindow
    from gillcup.graphics.layer import Layer
    from gillcup.graphics.colorrect import ColorRect
    rootLayer = Layer()


    # Create a rectangle and set various attributes on it
    rect = ColorRect(rootLayer)
    rect.scale = (0.5, 0.5)  # Resize to 1/2
    rect.anchorPoint = (0.5, 0.5)  # Move origin to the center
    rect.position = (0.5, 0.5)  # Move to the center of the screen

    rect.rotation = 45  # Rotate 45°
    rect.opacity = 0.75  # Make it see-through a bit

    rect.color = (1, 1, 0)  # Make it yellow


    # Show the result
    mainwindow.run(rootLayer)  



