The Gillcup Magic: Animations
=============================

So, you've gone throught the first part of the tutorial, and you stull think
you can take more? Yes? Then here we go.


Revive the Rectangle
--------------------

Again, let's start with some simple code::

    from gillcup.graphics import mainwindow
    from gillcup.graphics.layer import Layer
    from gillcup.graphics.colorrect import ColorRect
    rootLayer = Layer(timer=mainwindow.getMainTimer())

    rect = ColorRect(rootLayer, color=(1, 1, 0))
    rect.scale = (0.5, 0.5)
    rect.anchorPoint = (0.5, 0.5)
    rect.position = (0.5, 0.5)

    rect.rotateTo(45)

    mainwindow.run(rootLayer)

This might seem very familiar to you – it's very similar to the code from
the first part of the tutorial. What is different now is that it's using
animation API for the rotation in the lines::

    rootLayer = Layer(timer=mainwindow.getMainTimer())

    rect.rotateTo(45)

If we want to animate, the layers need to know the current time; the first line
says that we are using a normal timer that reflects the system clock's seconds
and starts when the main window is displayed. This is great for interactive
animations; but other timers are possible: if we wanted to render a movie, we'd
use a timer that advances by a fixed amount after we're drawing each frame.

The second line applies a very uninteresting animation to the rectangle,
rotating it instantly by 45°. This is abous as disappointing as the blank
window from the previous part of the tutorial; let's fix that.


Animations
----------

Change the rotation line to::

    rect.rotateTo(45, time=3)

If you can't see anything new, make sure that you're running this as a
script, the run() convenience function doesn't like to be called multiple
times.

If you saw movement, congratulations! You've made your first Gillcup animation.
As you can see, the setting of the rotation took 3 seconds[#] to complete,
smoothly transitioning from the previous value (0°) to 45°.


Tuple Animations
................

Try adding the following line::

    rect.moveTo(0.25, 0.25, time=2)

As you can see, it's not only numbers that can be animated: tuples of numbers
can, too. 

Be aware, however, that Gillcup's default animations only animates numbers and
tuples of numbers. Don't set a property you want to animate to a list, for
example.


Going Lower: the Animate Method
...............................

Now, replace the animation lines with this::

    rect.animate('rotation', 45, time=3)
    rect.animate('position', (0.25, 0.25), time=3)

As you can see, it does the same thing. In fact, the rotateTo and moveTo
methods are just a shortcut for “animate”.

The animate method can be used on any instance attribute of an AnimatedObject
(of which Layer & co. are subclasses).
The animation system doesn't know that “rotation” and “position” have some
meaning when the object is drawn. What this means for you is that you can
animate your own attributes, even on your own objects (as long as you subclass
them from gillcup.animatedobject.AnimatedObject). Remember this, for it will
be useful later.


Delayed Actions
...............

Now, delete your animation lines once again and put in the following instead::

    rect.rotateTo(45, time=3, dt=1)

This time, the animation starts a second after the window is shown.


Actions and Effects
-------------------

Once again replace the animation line, this time with:

    action = rect.rotationTo(45, time=3)
    rect.apply(action, dt=1)

It should do the same thing as last time.

What we are doing here is first obtaining an animation object, and then
applying it later. This approach has the advantage that you can keep the
animation around, and use it at a later time.

The animation object is the only thing you need to keep; any AnimatedObject
can be used to apply it, as long as it shares the same timer [#].

Note that the “dt” (delay) argument is passed to apply().

To make this a bit less confusing, let's introduce a bit of terminology.
We have been using the term “animation” somewhat vaguely for a combination of
two different concepts that Gillcup calls Actions and Effects.

Actions
.......

An Action is something that can be scheduled for the future: think of it as
a delayed function call. The object that the rotationTo method returns is such
an action; in this case, it starts an animation.

You can use any function as an action. Try putting the following before your
mainwindow.run call::

    def printMessage():
        print "Starting to turn!"
    rect.apply(printMessage, dt=1)

Of course, an Action can be more than just a packaged function call.
EffectAction, which rotationTo and friends return, knows about the Effect
it's going to apply, and it can use this knowledge to its advantage.


Effects
.......

Effects are, in essence, attribute modifiers. They change an AnimatedObject's
attribute, usually based on the time and the attribute's previous value.

Effects “last” for a longer time, as opposed to Actions which are instantaneous
(in the sense that the timer doesn't advance).

The simplest useful effect, which we have been using, just linearly
interpolates between the old value and a new value. There are, of course,
lots of other behaviors for effects, which we'll cover later. But even the
simplest effects have one useful functionality: chaining.


Chaining Effects and Actions
----------------------------

Just to make sure we're on the same ground, I'll give the whole code for this
example::

    from gillcup.graphics import mainwindow
    from gillcup.graphics.layer import Layer
    from gillcup.graphics.colorrect import ColorRect
    rootLayer = Layer(timer=mainwindow.getMainTimer())

    rect = ColorRect(rootLayer, color=(1, 1, 0))
    rect.scale = (0.5, 0.5)
    rect.anchorPoint = (0.5, 0.5)
    rect.position = (0.5, 0.5)

    action = rect.movementTo(0, 0, time=1)
    action.chain(rect.movementTo(0.5, 0.5, time=1))
    rect.apply(action)

    mainwindow.run(rootLayer)

What happens here? Our yellow friend moves to a corner, and then goes back.

As you can see, we called the chain() method to get this behavior. What an
Effect's chain() method does is simple: it schedules the given Action to happen
when the Effect is done.

We have, however, been using an Action's chain(). This does pretty much the
same: it chains the scheduled actions on the Effect it applies. Or, if it's
not an EffectAction, runs them just after it's done.

The chain method will also take a “dt” parameter to delay the new Action.

If you are using plain functions, you can wrap them in
gillcup.action.FunctionAction to get the chain() method. Or, just schedule
whatever you're chaining for the same time as your function.



The Rainbow Cycle
-----------------

Disclaimer: Sit in a well-lit room, a good distance from the screen.
If you fear epileptic seizures, stop reading and forget about making
animations.

Please note that Actions and Effects are intended for one-time use. Don't
schedule the same Action, or apply the same Effect more times. If you need to,
create an equivalent Action and Effect.

This doesn't apply to plain functions, since when they're scheduled, a new
Action is always made. So, you can do the following for an infinite loop::

    def rainbow():
        # Cycle through the colors...
        action = rect.animate('color', (1, 0, 0), time=0.2)
        action = action.chain(rect.animation('color', (1, 1, 0), time=0.2))
        action = action.chain(rect.animation('color', (0, 1, 0), time=0.2))
        action = action.chain(rect.animation('color', (0, 1, 1), time=0.2))
        action = action.chain(rect.animation('color', (0, 0, 1), time=0.2))
        action = action.chain(rect.animation('color', (1, 0, 1), time=0.2))
        # ... then go one more time
        action.chain(rainbow)

    rect.apply(rainbow)

Try it! If you haven't deleted your movement animation, you get to see that
the color cycle and the movement co-exist with each other peacefully.

You also get to see that you have to be a bit careful when using Gillcup's
methods: there's “animate”, which makes an animation and applies it
immediately, and “animation”, which creates an animation and gives you an
Action that starts it. The graphic object convenience functions also come in
such pairs: rotateTo/rotationTo, moveTo/movementTo, and so on. Be sure you
know which one you're using.

Another thing you might have noticed is that both flavors of animation methods
and chain() all return an Action object. Notice the above pattern of chaining
and setting the chain's end; it may useful to you.


Infinite Effects
----------------

Replace your animation by the following:

    rect.rotateTo(90, time=1, infinite=True)

This shows how you can make an infinite effect. It rotates out rectangle by
90° in 1 second, then instead of ending, it goes on rotating.

It doesn't make much sense to chain anything to such an animation, but if you
do, the chained Action will run at the time specified by the “time” argument,
not when the effect is done.


What Was Before Us
------------------

This section's animation code will look like this::

    rect.rotateTo(90, time=1, infinite=True)
    rect.rotateTo(0, time=5, dt=2)
    rect.animate('color', (1, 0, 0), dt=2)

What happens here? The rectangle is rotating happily at the speed of 90°/s,
and 2 seconds later it changes to red and starts rotating back to its original
position.

You might notice, though, that when the rectangle turns red, it doesn't
suddenly start rotating back. The transition is smooth. Why is that?

When I said earlier that a simple Effect interpolates between an old value
and a new value, I was only telling half of the truth. The “old value” includes
any effect that was on the attribute before. Effectively, an Effect
interpolates between a *dynamic value* and the given endpoint.


Dynamic Attributes
------------------

Try this::

    import math
    def sinOfTime():
        return math.sin(rect.timer.time) * 90
    rect.setDynamicAttribute('rotation', sinOfTime)

As you can see, you can set any function you want to work as an attribute
getter for AnimatedObjects. It will play along nicely with other effects, too.

Also, the rect.timer.time construction is new. I hope it doesn't need much
explanation, though. You can use mainwindow.getMainTimer().time for the same
effect.


Effects Can Be Animated
-----------------------

Now, try this::

    import math
    def blueCyan():
        sinOfTime = math.sin(rect.timer.time * 5)
        return 0, 0.5 + sinOfTime / 2, 1
    def redYellow():
        sinOfTime = math.sin(rect.timer.time * 10)
        return 1, 0.5 + sinOfTime / 2, 0
    rect.setDynamicAttribute('color', blueCyan)

Try both color schemes, but then put blueCyan back and add::

    action = rect.animate('color', (1, 1, 0), time=2, dt=1, keep=True)
    action.effect.setDynamicAttribute('value', redYellow)

Effects are AnimatedObjects, and can be themselves animated. You just have to
know what attributes to look for. One useful attribute, “value”, represents
the effect's “goal”; it is the value set by the animation method that created
the effect.

What we did above is animate this “goal”, thus making the effect interpolate
towards an animation. And since there was an animation in the beginning too,
we interpolated between two animations!

You can build arbitrarily complex animations by using this scheme.

If you are not dead tired by now, you might have noticed the “keep” attribute
above. Read on to know what it does.


When Effects end
................

When a simple effect ends, it is replaced by a much simpler effect that always
gives a constant value. This is done to prevent long “chains” of effects
from using up memory and the processor, because, as shown above, effects are
not replaced when animating.

The animation functions try to be smart and detect when you are doing advanced
stuff and disable this behavior if you are not applying just a simple effect.
For example, the infinite rotation above is not killed in this way.

However, it is not always possible to detect when you're going to need the
effect after it ends, so to be on the safe side add a keep=True argument
to the animation method when you manipulate the Effect later.


Dummy effects
-------------

[XXX]
























..  [#] The default time timer happens to be in seconds; the actual animations
    don't care about what the unit of time is.


..  [#] The timer of the applying object will be used for the animation; you
    can theoretically use this for interesting results.
