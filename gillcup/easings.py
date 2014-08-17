"""A collection of functions that add flavor to motion.

The functions are based on Robert Penner's `Motion, Tweening, and Easing
<http://robertpenner.com/easing/>`_.
See his page for more background.

Each of the functions defined here can be used directly for an
“ease in” animation (one that speeds up over time).
For other types, use attributes: **out** (slows down over time), **in_out**
(speeds up, then slows down), and **out_in** (slows down, then speeds up).
The ease-in is also available in **in_**. For example,
``gillcup.easing.quad.in_out`` gives a nice natural-looking tween.

.. note:: Some formulas in this documentation use
          the circular unit :math:`τ ≈ 6.283185`.

Reference
---------

.. autofunction:: get

.. attribute:: standard_easings

    A dictionary mapping the names of built-in easings to the corresponding
    functions

Power easing functions
......................

.. autofunction:: linear(t)

    .. easing_graph:: linear

.. autofunction:: quad(t)

    .. easing_graph:: quad

.. autofunction:: cubic(t)

    .. easing_graph:: cubic

.. autofunction:: quart(t)

    .. easing_graph:: quart

.. autofunction:: quint(t)

    .. easing_graph:: quint

Other simple easing functions
.............................

.. autofunction:: sine(t)

    .. easing_graph:: sine

.. autofunction:: circ(t)

    .. easing_graph:: circ

Parametrized easing functions
.............................

Use keyword arguments to override the defaults.

.. ::
    .. autofunction:: expo(t)

        .. easing_graph:: expo

.. autofunction:: power(t)

    .. easing_graph:: power

.. autofunction:: elastic(t)

    .. easing_graph:: elastic

.. autofunction:: back(t)

    .. easing_graph:: back

.. autofunction:: bounce(t)

    .. easing_graph:: bounce

.. autofunction:: cubic_bezier(t)

    .. easing_graph:: cubic_bezier

Helpers for creating new easing functions
.........................................

.. autofunction:: easing

Presentation helpers
....................

.. autofunction:: plot
.. autofunction:: format_svg
.. autofunction:: gallery_html

"""

import io
import functools
import math
import inspect

from gillcup.util.decorator import reify

tau = math.pi * 2  # http://www.tauday.com/


standard_easings = {}


def get(key):
    """Look up an easing function

    If :token:`key` is a string, it will be looked up
    in the :data:`standard_easings`.
    The key can be e.g. ``quad``, ``expo.out``, or ``bounce.in_out``.

    If :token:`key` is callable, it is simply returned.
    """
    if isinstance(key, str):
        return standard_easings[key]
    if callable(key):
        return key
    raise LookupError(key)


def _ease_out_func(func):
    def _ease_out(t, **kwargs):
        return 1 - func(1 - t, **kwargs)
    return _ease_out


def _ease_in_out_func(func):
    def _ease_in_out(t, **kwargs):
        if t < 0.5:
            return func(2 * t, **kwargs) / 2
        else:
            return 1 - func(1 - 2 * (t - .5), **kwargs) / 2
    return _ease_in_out


def _ease_out_in_func(func):
    def _ease_out_in(t, **kwargs):
        if t < 0.5:
            return (1 - func(1 - 2 * t, **kwargs)) / 2
        else:
            return func(2 * (t - .5), **kwargs) / 2 + .5
    return _ease_out_in


def _normalize(func):
    start_value = func(0)
    stop_value = func(1)
    if start_value == stop_value:
        raise ValueError(
            'bad easing function: f(0) == f(1) == %s' % start_value)
    if (abs(start_value - 0) > 0.0000001 or
            abs(stop_value - 1) > 0.0000001):
        scale = 1 / (stop_value - start_value)
        denorm_func = func

        def _normalized(t):
            return (denorm_func(t) - start_value) * scale

        return _normalized
    else:
        return func


class _Easing:
    def __init__(self, func, *, filters=(_normalize,), kwargs=None):
        orig_func = func
        if kwargs:
            func = functools.partial(func, **kwargs)
        kwargs = kwargs or {}
        for filt in filters:
            func = filt(func)
        self.filters = filters
        self.orig_func = orig_func
        self.func = func
        self.kwargs = kwargs

        name_parts = [orig_func.__name__]
        if kwargs:
            name_parts.append('.p(')
            name_parts.append(', '.join('{}={}'.format(*i)
                                        for i in kwargs.items()))
            name_parts.append(')')
        self.__name__ = ''.join(name_parts)

        self.__doc__ = self.orig_func.__doc__

    def __repr__(self):
        r = ('<{mod}.{qn}: t → {fmod}.{fqn}(t, {kwa}), at 0x{id:x}>')
        return r.format(
            mod=self.__module__,
            qn=type(self).__qualname__,
            fmod=self.orig_func.__module__,
            fqn=self.orig_func.__qualname__,
            kwa=', '.join('{}={}'.format(*i) for i in self.kwargs.items()),
            id=id(self),
        )

    def __call__(self, t):
        return self.func(t)

    @reify
    def in_(self):
        return self

    @reify
    def out(self):
        rval = _Easing(self.orig_func, kwargs=self.kwargs,
                       filters=self.filters + (_ease_out_func,))
        rval.out = self
        return rval

    @reify
    def in_out(self):
        return _Easing(self.orig_func, kwargs=self.kwargs,
                       filters=self.filters + (_ease_in_out_func,))

    @reify
    def out_in(self):
        return _Easing(self.orig_func, kwargs=self.kwargs,
                       filters=self.filters + (_ease_out_in_func,))

    def _repr_svg_(self):
        return format_svg(self)

    def parametrized(self, **kwargs):
        """Returns an easing with new parameters

        For example, a large overshoot tween can be created as:

        .. easing_graph:: large_overshoot

            >>> large_overshoot = back.parametrized(amount=4)
            >>> large_overshoot.out(0.4)
            1.3...

        """
        new_kwargs = dict(self.kwargs)
        new_kwargs.update(kwargs)
        return _Easing(self.orig_func, kwargs=new_kwargs)


def easing(func):
    """Decorator for easing functions.

    Adds the :token:`in_`, :token:`out`, :token:`in_out` and :token:`out_in`
    functions to an easing function.

    .. easing_graph:: staircase

        >>> @easing
        ... def staircase(t, steps=5):
        ...     '''Discontinuous tween (to demonstrate @easing)'''
        ...     return ((t * steps) // 1) / steps

    Functions decorated as an ``@easing`` will display as a graph
    when printed out in IPython Notebook.

    """
    return _Easing(func)


def _easing(func=None):
    func = easing(func)
    standard_easings[func.__name__] = func
    for variant in ['in_', 'out', 'in_out', 'out_in']:
        name = '{}.{}'.format(func.__name__, variant)
        standard_easings[name] = getattr(func, variant)
    return func


@_easing
def linear(t):
    r"""Linear interpolation

    .. math:: \mathrm{linear}(t) = t
    """
    return t


@_easing
def quad(t):
    r"""Quadratic easing

    .. math:: \mathrm{quad}(t) = t ^ 2
    """
    return t * t


@_easing
def cubic(t):
    r"""Cubic easing

    .. math:: \mathrm{cubic}(t) = t ^ 3
    """
    return t ** 3


@_easing
def quart(t):
    r"""Quartic easing

    .. math:: \mathrm{quart}(t) = t ^ 4
    """
    return t ** 4


@_easing
def quint(t):
    r"""Quintic easing

    .. math:: \mathrm{quint}(t) = t ^ 5
    """
    return t ** 5


@_easing
def power(t, exponent=2):
    r"""Power interpolation

    .. math:: \mathrm{power}(t, r) = t ^ r

    The :func:`linear`, :func:`quad`, :func:`cubic`, :func:`quart` and
    :func:`quint` are special cases of this.
    """
    return t ** exponent


@_easing
def sine(t):
    r"""Sinusoidal easing: Quarter of a cosine wave

    .. math:: \mathrm{sine}(t) = \cos\left(\frac{tτ}{4}\right)
    """
    return 1 - math.cos(t * tau / 4)


@_easing
def expo(t, exponent=10):
    r"""Exponential easing

    .. math:: \mathrm{expo}^\prime(t, x) = 2 ^ {x (t - 1)}

    The result is normalized to the proper range using :func:`normalized`.
    """
    return 2 ** (exponent * (t - 1))


@_easing
def circ(t):
    r"""Circular easing: Quarter of a circle

    .. math:: \mathrm{circ}(t) = 1 - \sqrt{1 - t ^ 2}
    """
    if t >= 1:
        return 1
    return 1 - math.sqrt(1 - t * t)


@_easing
def elastic(t, period=0.3, amplitude=1):
    r"""Elastic easing

    .. math::
        \begin{aligned}
            &\mathrm{elastic}(t, p, a) =
                -2A ^ {10t}
                \sin\left(
                        \left(
                            t - \frac{p}{τ}\arcsin\frac{1}{A}
                        \right)
                        \frac{τ}{p}
                    \right)\\
            &\text{where:} \\
            &A = \begin{cases}
                    1                   & \text{if } a < 1 \\
                    a                   & \text{otherwise} \\
                \end{cases} \\
        \end{aligned}
    """
    if not t:
        return 0
    if t == 1:
        return 1

    if amplitude < 1:
        amplitude = 1
        s = period / 4
    else:
        s = period / tau * math.asin(1 / amplitude)

    t -= 1
    return -amplitude * 2 ** (10 * t) * math.sin((t - s) * tau / period)


@_easing
def back(t, amount=1.70158):
    r"""Overshoot easing

    .. math:: \mathrm{back}(t, x) =
              t^2 (t(x + 1) - x)

    The default :token:`amount` results in 10% overshoot.
    """
    return t * t * ((amount + 1) * t - amount)


@_easing
def bounce(t, amplitude=1):
    r"""Bouncy easing

    .. math::

        \mathrm{bounce}(t, a) = \begin{cases}
            \frac{\;11^2}{16} t^2  & \text{if } t < \frac{4}{11} \\
            1 - a \left(1 - \frac{\;11^2}{16} \left(t-\frac{6}{11}\right)^2 -
                            \frac{3}{4}\right)
                                & \text{if } t < \frac{8}{11} \\
            1 - a \left(1 - \frac{\;11^2}{16} \left(t-\frac{9}{11}\right)^2 -
                            \frac{15}{16}\right)
                                & \text{if } t < \frac{10}{11} \\
            1 - a \left(1 - \frac{\;11^2}{16} \left(t-\frac{21}{22}\right)^2 -
                            \frac{63}{64}\right)
                                & \text{if } t < 1 \\
            1                   & \text{otherwise} \\
        \end{cases}
    """
    if t < 4 / 11:
        return 121 / 16 * t * t
    if t < 8 / 11:
        t -= 6 / 11
        return 1 - amplitude * (1 - 121 / 16 * t * t - 3 / 4)
    if t < 10 / 11:
        t -= 9 / 11
        return 1 - amplitude * (1 - 121 / 16 * t * t - 15 / 16)
    elif t < 1:
        t -= 21 / 22
        return 1 - amplitude * (1 - 121 / 16 * t * t - 63 / 64)
    else:
        return 1


@_easing
def cubic_bezier(t, x1=1, y1=0.5, x2=0, y2=0.5):
    r"""Cubic Bézier easing

    The *x1* and *x2* parameters must be in the interval [0, 1].

    .. math::
        \mathtt{cubic\_bezier}(t, x₁, y₁, x₂, y₂) = y

    where *y* is the solution of:

    .. math::

        \begin{align}
            y &= 3p (1-p)^2 y₁ + 3p^2 (1-p) y₂ + p^3 \\
            t &= 3p (1-p)^2 x₁ + 3p^2 (1-p) x₂ + p^3 \\
        \end{align}

    Cubic béziers are used for animation in newer versions of CSS,
    so there are many Web-based tools for visualizing them.
    One example is `cubic-bezier.com`_.

    .. _cubic-bezier.com: http://cubic-bezier.com/
    """

    if not 0 <= x1 <= 1:
        raise ValueError('x1 out of range')
    if not 0 <= x2 <= 1:
        raise ValueError('x2 out of range')
    if t <= 0:
        return 0
    if t >= 1:
        return 1

    # Solve for p

    # 0 = 3p (1-p)² x₁              + 3p² (1-p) x₂      + p³ - t
    # 0 = 3p (1-2p+p²) x₁           + 3p² (1-p) x₂      + p³ - t
    # 0 = 3p x₁ - 6p² x₁ + 3p p² x₁ + 3p² x₂ - 3p² p x₂ + p³ - t
    # 0 = 3p x₁ - 6p² x₁ + 3p³ x₁   + 3p² x₂ - 3p³ x₂   + p³ - t

    # 0 = (3x₁ - 3x₂ + 1) p³ + (-6x₁ + 3x₂) p² + (3x₁) p + (-t)

    a = 3 * x1 - 3 * x2 + 1
    b = -6 * x1 + 3 * x2
    c = 3 * x1
    d = -t

    def generalized_cuberoot(x):
        if x < 0:
            return -((-x) ** (1/3))
        else:
            return x ** (1/3)

    def cubic_roots(a, b, c, d):
        if not a:
            yield from quadratic_roots(b, c, d)
        else:
            b /= a
            c /= a
            d /= a

            q = (3 * c - b**2) / 9
            r = (-27 * d + b * (9 * c - 2 * b**2)) / 54
            Δ = q**3 + r**2
            t1 = b / 3

            if Δ > 0:
                s = generalized_cuberoot(r + math.sqrt(Δ))
                t = generalized_cuberoot(r - math.sqrt(Δ))
                yield -t1 + s + t
            elif not Δ:
                rr = generalized_cuberoot(r)
                yield -t1 + 2 * rr
                yield -rr - t1
            else:
                q = -q
                d1 = math.acos(r / math.sqrt(q**3))
                r13 = 2 * math.sqrt(q)

                yield -t1 + r13 * math.cos(d1 / 3)
                yield -t1 + r13 * math.cos((d1 + tau) / 3)
                yield -t1 + r13 * math.cos((d1 + 2 * tau) / 3)

    def quadratic_roots(a, b, c):
        Δ = math.sqrt(b**2 - 4 * a * c)
        yield (-b + Δ) / (2 * a)
        yield (-b - Δ) / (2 * a)

    for p in cubic_roots(a, b, c, d):
        if 0 <= p <= 1:
            break
    else:
        raise ValueError('could not find cubic roots')

    return 3 * p * (1-p)**2 * y1 + 3 * p**2 * (1-p) * y2 + p**3


def plot(func, *, overshoots=None, figsize=5, sampling_frequency=110,
         reference=None, grid_frequency=10, kwarg_variations=None):
    """Plot an easing function using matplotlib

    Requires numpy and matplotlib installed.

    :param func: The function to plot. Looked up by :func:`get`, so it can
                 be a name of one of the standard easings.
    :param overshoots: Extra vertical space for the graph; None means automatic
    :param figsize: Size of the figure
    :param sampling_frequency:
        Sampling frequency to use.
        The default is divisible by 11 to show the discontinuities
        of :func:`bounce`.
    :param reference: Two easing functions to show as reference, or None
    :param grid_frequency: Frequency of grid lines, or None for no grid
    :param kwarg_variations: For every keyword argument of the function,
                             extra graphs are drawn with that argument
                             multiplied by each variation factor

    Returns a pyplot graph. Use its ``show()`` method to show it,
    or ``savefig(filename)`` to save.
    See `pyplot docs`_ for more info.

    .. _pyplot docs: http://matplotlib.org/contents.html
    """
    from matplotlib import pyplot
    import numpy

    def set_next_gid(patch):
        nonlocal counter
        counter += 1
        gid = 'tooltipped-patch-%s' % counter
        patch.set_gid(gid)
        return gid
    counter = 0

    fig = pyplot.figure(figsize=(figsize,
                                 (1 + (overshoots or 0) * 2) * figsize))
    fig.set_canvas(pyplot.gcf().canvas)
    fig._gillcup_tooltips = {}
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_xlim([0, 1])
    if overshoots is not None:
        ax.set_ylim([-overshoots, 1 + overshoots])
    xes = tuple(n / sampling_frequency for n in range(sampling_frequency + 1))

    if reference:
        ref1, ref2 = [numpy.array(_get_points(n, xes))
                      for n in reference]
        ax.fill_between(xes, ref1, ref2,
                        facecolor=[0, 0.01, 0, 0.05],
                        linewidth=0.0)
    if grid_frequency:
        for i in list(range(grid_frequency + 1)) + [0]:
            p = i / grid_frequency
            color = 'k' if p in (0, 1) else [0.9, 0.9, 0.9]
            ax.plot([p, p], [0, 1], color=color)
            ax.plot([0, 1], [p, p], color=color)
    if kwarg_variations:
        try:
            parametrized = func.parametrized
        except AttributeError:
            pass
        else:
            for arg in inspect.signature(parametrized).parameters.values():
                if arg.kind == inspect.Parameter.KEYWORD_ONLY:
                    for variation_factor in kwarg_variations:
                        value = arg.default * variation_factor
                        part = parametrized(**{arg.name: value})
                        try:
                            pts = _get_points(part, xes)
                        except ValueError:
                            continue
                        patches = ax.plot(xes, pts, color=[0, 0, 1, 0.2])
                        for patch in patches:
                            gid = set_next_gid(patch)
                            fig._gillcup_tooltips[gid] = part.__name__
    patches = ax.plot(xes, _get_points(func, xes), 'b')
    for patch in patches:
        gid = set_next_gid(patch)
        fig._gillcup_tooltips[gid] = func.__name__

    pyplot.close(fig)
    return fig


@functools.lru_cache()
def _get_points(func, xes):
    func = get(func)
    return [func(x) for x in xes]


def format_svg(func, css_width="13em", **kwargs):
    """Plot an easing function as an SVG file.

    Returns an Unicode string.

    See :func:`plot` for arguments and dependencies.
    """
    from xml.etree import ElementTree

    fig = plot(func, **kwargs)
    sio = io.StringIO()
    fig.savefig(sio, format='svg', transparent=True)
    ElementTree.register_namespace('', "http://www.w3.org/2000/svg")
    ElementTree.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
    et, by_id = ElementTree.XMLID(sio.getvalue())
    et.attrib['width'] = css_width
    del et.attrib['height']
    for gid, tooltip in fig._gillcup_tooltips.items():
        by_id[gid].attrib['class'] = 'tooltipped'
        by_id[gid].attrib['title'] = tooltip
    css = et.getchildren()[0][0]
    css.text = css.text + """
        .tooltipped:hover path {
            stroke-width:10px;
            stroke:#000088;
        }"""
    return ElementTree.tostring(et, encoding="unicode")


def gallery_html(func, kwarg_variations=(0.5, 1.5), overshoots=0.5,
                 css_width='100%', **kwargs):
    """Format a family of easing functions as a HTML gallery of inline SVGs.

    :token:`func` is a function that was decorated with :func:`easing`.

    Returns an Unicode string with the SVG file.

    See :func:`plot` for the arguments and dependencies.
    For gallery_html, :token:`reference` is not currently customizable.
    """
    import markupsafe

    func = get(func)

    result = []

    for attrname in ['in_', 'out', 'in_out', 'out_in']:
        f = getattr(func, attrname)

        reference = ('linear.' + attrname, 'quint.' + attrname)
        svg = markupsafe.Markup(format_svg(f,
                                           reference=reference,
                                           overshoots=overshoots,
                                           css_width=css_width,
                                           kwarg_variations=kwarg_variations,
                                           **kwargs))

        result.append(markupsafe.Markup("""
            <div style="width:24%;float:left;">
                <div style="text-align:center;
                            margin-top:-{overshoots}%;
                            margin-bottom:-{overshoots}%">
                    {svg}
                </div>
                <div style="text-align:center;">
                    &nbsp;{func_name}&nbsp;
                </div>
            </div>
        """).format(
            overshoots=int(100 * (overshoots or 0)),
            svg=svg,
            func_name=f.__name__,
        ))

    result.append('<br style="clear:both;">')
    return '\n'.join(result)
