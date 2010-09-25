
from gillcup.action import EffectAction

class AnimatedObject(object):
    """An objects whose attributes can be animated

    Animated attribute must be instance (not class) attribute in order to
    work.
    Every animated attribute must be assigned a normal value before it can be
    animated. Usually this is done in the constructor.

    Each AnimatedObject needs a timer to animate. This can be either
    through an argument to the animate method, or in an instance attribute.
    The constructor takes a timer value to set the instance attribute to.
    """
    def __init__(self, timer=None):
        super(AnimatedObject, self).__init__()
        self._anim_data_ = {}
        self.timer = timer

    def _animate(self, attribute, animation):
        """Animate the given attribute by the given animation

        animation can be any object with a getValue method; but an Effect
        works best.
        """
        try:
            oldValue = self.__dict__[attribute]
            del self.__dict__[attribute]
        except KeyError:
            old = self._anim_data_[attribute]
        else:
            old = _Constant(oldValue)
        self._anim_data_[attribute] = animation
        return old

    def __getattr__(self, attr):
        try:
            effect = self._anim_data_[attr]
        except KeyError:
            raise AttributeError(attr)
        except RuntimeError:
            # Probably _anim_data_ doesn't exist => infinite recursion
            raise RuntimeError(
                    'Runtime error while getting attribute %s. '
                    'Likely the base __init__ method was not called'
                    % attr
                )
        return effect.getValue()

    def _replace_effect(self, attribute, oldEffect, newEffect):
        """ Replace the given effct by a new effect
        """
        try:
            currentEffect = self._anim_data_[attribute]
        except KeyError:
            return False
        else:
            if currentEffect is oldEffect:
                self._anim_data_[attribute] = newEffect
                return True
            else:
                try:
                    replaceMethod = currentEffect._replace_effect_
                except AttributeError:
                    return False
                else:
                    return currentEffect._replace_effect_(oldEffect, newEffect)

    def _dump_effects(self, indentLevel=0):
        for attr, effect in self._anim_data_.items():
            print '  ' * indentLevel + '.' + attr + ':' + str(getattr(self, attr))
            try:
                dump = effect.dump
            except AttributeError:
                print '  ' * (indentLevel + 1) + str(effect)
            else:
                effect.dump(indentLevel + 1)

    def animate(self, attribute, value, dt=0, timer=None, **options):
        """Animate the given attribute

        Calls self.apply(self.animation(...), dt=dt).
        Returns the resulting Action.
        """
        anim = self.animation(attribute, value, **options)
        return self.apply(anim, dt=dt, timer=timer)

    def animation(self, attribute, value, **options):
        """Return an animation Action for the given attribute.

        When this Action is run, the given attribute will be gradually set
        to the new value. The style of the animation is given by options.

        See :py:func:`gillcup.effect.animation` for what options are available.
        """
        from gillcup.effect import animation
        return animation(self, attribute, value, **options)

    def apply(self, action, dt=0, timer=None):
        """Schedule action on this object's timer

        dt is the time in which the Action is to be executed (measured from the
        timer's current time).
        timer can be given to specify the timer to use; if None, self's timer
        will be used
        """
        timer = timer or self.timer
        timer.schedule(dt, action)
        return action

    def dynamicAttributeSetter(self, attribute, getter):
        """Returns an Action to set an attribute getter

        After the returned Action runs, the given getter function will be used
        to provide values for the given attribute.
        """
        return EffectAction(_GetterObject(getter), self, attribute)

    def setDynamicAttribute(self, attribute, getter, dt=0, timer=None):
        """Set a getter for an attribute

        If dt==0, sets getter as the attribute getter for the given attribute.

        Otherwise, calls
        self.apply(self.dynamicAttributeSetter(attribute, getter), dt=dt).
        """
        if not dt:
            self._animate(attribute, _GetterObject(getter))
        else:
            setter = self.dynamicAttributeSetter(attribute, getter)
            self.apply(setter, dt, timer)


class _Constant(object):
    def __init__(self, value):
        self.value = value

    def getValue(self):
        return self.value

    def dump(self, indentationLevel):
        o = str(self.value)
        print '  ' * indentationLevel + type(self).__name__ + ': ' + o


class _GetterObject(object):
    def __init__(self, getValue):
        self.getValue = getValue

    def dump(self, indentationLevel):
        print '  ' * indentationLevel + type(self).__name__
