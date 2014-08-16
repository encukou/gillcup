# Private Sphinx extension for making special methods look better.
# The parts that Gillcup uses should work...

import io
from xml.etree import ElementTree

import sphinx.ext.autodoc
from docutils import nodes
from sphinx.util.compat import Directive

from matplotlib import pyplot

from gillcup import easings


class SpecialMethodDocumenter(sphinx.ext.autodoc.MethodDocumenter):
    objtype = 'specialmethod'

    def name_sig(self, name, sig):
        for funcname in ('repr str bytes len iter hash bool dir reversed abs '
                         'complex float int round index').split():
            if name == '__%s__' % funcname:
                return '%s(self)' % funcname
        for s in ('lt:< le:<= eq:== ne:!= gt:> ge:>= add:+ sub:- mul:* '
                  'truediv:/ floordiv:// mod:% lshift:<< rsift:>> and:& or:| '
                  'xor:^').split():
            funcname, op = s.split(':')
            if name == '__%s__' % funcname:
                return 'self %s %s' % (op, sig.strip('()'))
            if name == '__r%s__' % funcname:
                return '%s %s self' % (sig.strip('()'), op)
            if name == '__i%s__' % funcname:
                return 'self %s= %s' % (op, sig.strip('()'))
        for funcname in 'format divmod pow'.split():
            if name == '__%s__' % funcname:
                return '%s(self, %s)' % (funcname, sig.strip('()'))
        for s in ('neg:- pos:+ invert:~').split():
            funcname, op = s.split(':')
            if name == '__%s__' % funcname:
                return '%sself' % op
        for s in 'instancecheck:isinstance subclasscheck:issubclass'.split():
            funcname, func = s.split(':')
            if name == '__%s__' % funcname:
                return '%s(%s, cls)' % (func, sig.strip('()'))
        if name == '__getattr__':
            return 'self.attr'
        if name == '__getattribute__':
            return 'self.attribute'
        if name == '__setattr__':
            return 'self.attr = value'
        if name == '__delattr__':
            return 'del self.attr'
        # __call__: rendering this as 'self(...)' would make it look like a
        # method named "self". Let's just use "__call__" here.
        if name == '__getitem__':
            return 'self[%s]' % sig.strip('()')
        if name == '__setitem__':
            name_name, value_name = sig.strip('()').partition(',')
            return 'self[%s] = %s' % (name_name, value_name)
        if name == '__delitem__':
            return 'del self[%s]' % sig.strip('()')
        if name == '__contains__':
            return '%s in self' % sig.strip('()')
        if name == '__enter__':
            return 'with self:'

    def add_header_line(self, domain, directive, name, sig):
        name_sig = self.name_sig(self.name, sig) or '%s%s' % (name, sig)
        self.add_line('.. %s:%s:: %s' % (domain, directive, name_sig),
                      '<autodoc>')

    def add_directive_header(self, sig):
        # XXX: This is copied from sphinx.ext.autodoc, with the necessary line
        # made into a method. Ugh.

        domain = getattr(self, 'domain', 'py')
        directive = getattr(self, 'directivetype', self.objtype)
        name = self.format_name()
        self.add_header_line(domain, directive, name, sig)
        if self.options.noindex:
            self.add_line('   :noindex:', '<autodoc>')
        if self.objpath:
            # Be explicit about the module, this is necessary since .. class::
            # etc. don't support a prepended module name
            self.add_line('   :module: %s' % self.modname, '<autodoc>')

            if self.name_sig(self.name, sig) is not None:
                self.add_line('', '<autodoc>')
                self.add_line('   *a.k.a.* :token:`%s%s`' % (self.name, sig),
                              '<autodoc>')


class easing_graph(nodes.General, nodes.Element):
    pass


class EasingGraph(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0

    def run(self):
        node = easing_graph()
        node['name'] = self.content[0]
        return [node]


def html_visit_easing_graph(self, node):
    if node['name'] == 'large_overshoot':
        func = easings.partial(easings.back, amount=4)
    else:
        func = easings.easings[node['name']]
    overshoots = 0.4
    pyplot.figure(figsize=(5, (1 + overshoots * 2) * 5))
    xes = [n / 100 for n in range(101)]
    attrnames = [None, 'out', 'in_out', 'out_in']
    ref_plots = {n: [] for n in attrnames}
    for name in ['linear', 'quint']:
        otherfunc = easings.easings[name]
        for attrname in attrnames:
            if attrname:
                f = getattr(otherfunc, attrname)
            else:
                f = otherfunc
            ref_plots[attrname].append([f(n) for n in xes])
    for attrname in attrnames:
        self.body.append('<div style="width:24%;float:left;">')
        self.body.append('<div style="text-align:center;'
                         'margin-top:-{0}%;'
                         'margin-bottom:-{0}%">'.format(int(100 * overshoots)))
        if attrname:
            f = getattr(func, attrname)
            suffix = '.' + attrname
        else:
            f = func
            suffix = ''
        pyplot.cla()
        pyplot.axis('off')
        pyplot.ylim([-overshoots, 1 + overshoots])
        for i in range(1, 10):
            p = i / 10
            pyplot.plot([p, p], [0, 1], color=[0, 0, 1., 0.05])
            pyplot.plot([0, 1], [p, p], color=[0, 0, 1., 0.05])
        for p in ref_plots[attrname]:
            pyplot.plot(xes, p, color=[0, 0, 0, 0.1])
        pyplot.plot([0, 1], [0, 0], 'k')
        pyplot.plot([0, 1], [1, 1], 'k')
        pyplot.plot([0, 0], [0, 1], 'k')
        pyplot.plot([1, 1], [0, 1], 'k')
        pyplot.plot(xes, [f(n) for n in xes])
        sio = io.StringIO()
        pyplot.savefig(sio, format='svg', transparent=True)
        ElementTree.register_namespace('', "http://www.w3.org/2000/svg")
        et = ElementTree.fromstring(sio.getvalue())
        et.attrib['width'] = '100%'
        del et.attrib['height']
        self.body.append(ElementTree.tostring(et, encoding="unicode"))
        self.body.append('</div>')
        self.body.append('<div style="text-align:center;">')
        self.body.append('&nbsp;{}{}&nbsp;'.format(func.__name__, suffix))
        self.body.append('</div>')
        self.body.append('</div>')
    self.body.append('<br style="clear:both;">')
    raise nodes.SkipNode


def setup(app):
    app.add_autodocumenter(SpecialMethodDocumenter)
    app.add_node(easing_graph,
                 html=(html_visit_easing_graph, None))
    app.add_directive('easing_graph', EasingGraph)
