import sphinx.ext.autodoc


def setup(app):
    app.add_autodocumenter(SpecialMethodDocumenter)


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
        if name == '__call__':
            return 'self()'
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
