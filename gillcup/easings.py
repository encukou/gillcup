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

Reference
---------

.. attribute:: standard_easings

    A dictionary mapping the names of built-in easings to the corresponding
    functions


Polynomial easing functions
...........................

.. autofunction:: linear

    .. easing_graph:: linear

.. autofunction:: quad

    .. easing_graph:: quad

.. autofunction:: cubic

    .. easing_graph:: cubic

.. autofunction:: quart

    .. easing_graph:: quart

.. autofunction:: quint

    .. easing_graph:: quint

Other simple easing functions
.............................

.. autofunction:: sine

    .. easing_graph:: sine

.. autofunction:: circ

    .. easing_graph:: circ

Parametrizable easing functions
...............................

Use keyword arguments to override the defaults.

.. autofunction:: expo

    .. easing_graph:: expo

.. autofunction:: elastic

    .. easing_graph:: elastic

.. autofunction:: back

    .. easing_graph:: back

.. autofunction:: bounce

    .. easing_graph:: bounce

.. note:: Use :func:`partial` to make easing
          functions with different parameters.

Helpers for creating new easing functions
.........................................

.. autofunction:: easing
.. autofunction:: normalized
.. autofunction:: partial

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

tau = math.pi * 2


standard_easings = {}


def _wraps_easing(decorated, orig, postfix):
    decorated.__signature__ = inspect.signature(orig)
    if postfix:
        postfix = '.' + postfix
    else:
        postfix = ''
    try:
        decorated.__name__ = str(orig.__name__ + postfix)
    except AttributeError:
        pass
    decorated._repr_svg_ = lambda: format_svg(decorated)
    return decorated


def _ease_out(func):
    """Given an "in" easing function, return corresponding "out" function"""
    def _ease_out(t, **kwargs):
        return 1 - func(1 - t, **kwargs)
    return _wraps_easing(_ease_out, func, 'out')


def _ease_out_in(func):
    """Given an "in" easing function, return corresponding "out-in" function"""
    def _ease_out_in(t, **kwargs):
        if t < 0.5:
            return (1 - func(1 - 2 * t, **kwargs)) / 2
        else:
            return func(2 * (t - .5), **kwargs) / 2 + .5
    return _wraps_easing(_ease_out_in, func, 'out_in')


def _ease_in_out(func):
    """Given an "in" easing function, return corresponding "in-out" function"""
    def _ease_in_out(t, **kwargs):
        if t < 0.5:
            return func(2 * t, **kwargs) / 2
        else:
            return 1 - func(1 - 2 * (t - .5), **kwargs) / 2
    return _wraps_easing(_ease_in_out, func, 'in_out')


def _ease_in(func):
    """Create an "in" easing function. Adds presentation-related attributes.

    Note that :token:`func` is modified in-place.
    """
    func._repr_svg_ = lambda: format_svg(func)
    return func


def easing(func):
    """Decorator for easing functions.

    Adds the :token:`in_`, :token:`out`, :token:`in_out` and :token:`out_in`
    functions to an easing function.

    .. easing_graph:: staircase

        >>> @easing
        ... def staircase(t, *, steps=5):
        ...     '''Discontinuous tween (to demonstrate @easing)'''
        ...     return ((t * steps) // 1) / steps

    Functions decorated as an ``@easing`` will display as a graph
    when printed out in IPython Notebook.

    """
    func.in_ = _ease_in(func)
    func.out = _ease_out(func)
    func.in_out = _ease_in_out(func)
    func.out_in = _ease_out_in(func)
    return func


def normalized(func, *, default_kwargs=None):
    """Decorator that normalizes an easing function

    Normalizing is done so that func(0) == 0 and func(1) == 1.

    .. easing_graph:: wiggly

        >>> @easing
        ... @normalized
        ... def wiggly(t):
        ...     '''Wiggly tween (to demonstrate @normalized)'''
        ...     return (t + 10) ** 2 + math.cos(t * 50)

    If func(0) == func(1), :exc:`ZeroDivision` is raised.
    """
    if not default_kwargs:
        default_kwargs = {}

    minimum = func(0, **default_kwargs)
    maximum = func(1, **default_kwargs)
    scale = 1 / (maximum - minimum)

    def _normalized(t, **kwargs):
        if kwargs == default_kwargs:
            return (func(t, **kwargs) - minimum) * scale
        else:
            i_minimum = func(0, **kwargs)
            i_maximum = func(1, **kwargs)
            i_scale = 1 / (i_maximum - i_minimum)
            return (func(t, **kwargs) - i_minimum) * i_scale
    _wraps_easing(_normalized, func, None)
    _normalized.__doc__ = func.__doc__

    return _normalized


def partial(func, **kwargs):
    """Combines :func:`functools.partial` and :func:`easing`.

    For example, a large overshoot tween can be created as:

    .. easing_graph:: large_overshoot

        >>> from gillcup import easings
        >>> large_overshoot = easings.partial(easings.back, amount=4)
        >>> large_overshoot.out(0.4)
        1.3...

    """
    partl = functools.wraps(func)(functools.partial(func, **kwargs))
    partl.__name__ = '<{}:{}>'.format(
        func.__name__,
        ', '.join('{}={}'.format(k, v) for k, v in kwargs.items())
    )
    return easing(partl)


def _easing(func):
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
def sine(t):
    r"""Sinusoidal easing: Quarter of a cosine wave

    .. math:: \mathrm{sine}(t) = \cos\left(\frac{tτ}{4}\right)
    """
    return 1 - math.cos(t * tau / 4)


@_easing
@normalized
def expo(t, *, exponent=10):
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
def elastic(t, *, amplitude=1, period=0.3):
    r"""Elastic easing

    .. math::
        \begin{aligned}
            &\mathrm{elastic}(t, a, p) = -2A ^ {10t}
                                   \sin\frac{sτ}{p} \\
            &\text{where:} \\
            &A = \begin{cases}
                    1                   & \text{if } a < 1 \\
                    a                   & \text{otherwise} \\
                \end{cases} \\
            &s = \begin{cases}
                    (t - \frac{p}{4}    & \text{if } a < 1 \\
                    (t - \frac{p}{τ} \arcsin\frac{1}{a})
                                        & \text{otherwise}  \\
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
def back(t, *, amount=1.70158):
    r"""Overshoot easing

    .. math:: \mathrm{back}(t, x) =
              t^2 (t(x + 1) - x)

    The default :token:`amount` results in 10% overshoot.
    """
    return t * t * ((amount + 1) * t - amount)


@_easing
def bounce(t, *, amplitude=1):
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


def plot(func, *, overshoots=None, figsize=5, sampling_frequency=110,
         reference=None, grid_frequency=10, kwarg_variations=None):
    """Plot an easing function using matplotlib

    Requires numpy and matplotlib installed.

    :param func: The function to plot,
                 or a string which is looked up in :data:`known_easings`
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
        for arg in inspect.signature(func).parameters.values():
            if arg.kind == inspect.Parameter.KEYWORD_ONLY:
                for variation_factor in kwarg_variations:
                    value = arg.default * variation_factor
                    part = partial(func, **{arg.name: value})
                    patches = ax.plot(xes, _get_points(part, xes),
                                      color=[0, 0, 1, 0.2])
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
    if isinstance(func, str):
        func = standard_easings[func]
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
    For gallery_html, :token:`func` may not be a string,
    and :token:`reference` is not currently customizable.
    """
    import markupsafe

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
