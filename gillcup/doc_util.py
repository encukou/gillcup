# Private Sphinx extension for making special methods look better.
# The parts that Gillcup uses should work...

import sphinx.ext.autodoc
from docutils import nodes
from sphinx.util.compat import Directive

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
        content = self.content[1:]
        node['content'] = '\n'.join(content)
        node['code'] = '\n'.join(l[4:] for l in content
                                 if l.startswith(('>>> ', '... ')))

        if node['content']:
            code_node = nodes.literal_block(node['content'], node['content'])
            code_node['language'] = 'py3'
            code_node['linenos'] = False
            node.children = [code_node]
        return [node]


def html_visit_easing_graph(self, node):
    print(node['name'], '  ', end='\r')
    if node['code']:
        environ = {n: getattr(easings, n) for n in dir(easings)}
        exec(node['code'], environ)
        func = environ[node['name']]
    else:
        func = easings.standard_easings[node['name']]
    self.body.append(easings.gallery_html(func))
    return []


def setup(app):
    app.add_autodocumenter(SpecialMethodDocumenter)
    app.add_node(easing_graph,
                 html=(lambda s, n: [], html_visit_easing_graph))
    app.add_directive('easing_graph', EasingGraph)
