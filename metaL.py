################################## metaL/kb: Knowledge Base engine /Python core/
############################# (c) Dmitry Ponyatov <dponyatov@gmail.com> 2020 MIT
######################################### github: https://github.com/ponyatov/kb

def comment(text, width=80):
    print('#' * (width - len(text) - 1) + ' ' + text)
# comment('documenting')#,65) ; sys.exit(-1)

################################################################# system modules

import os, sys
from markdown import markdown

############################################################# object graph types

################################################################ base node class

class Object: # ex. Frame

    def __init__(self, V):

        # scalar data value
        # mostly names the frame, but also can store things like numbers and strings
        self.val = V

        # named slots = attributes = string-keyed associative array
        self.slot = {}

        # ordered storage = program AST nested elemens = vector = stack
        self.nest = []

        # unique storage id (Redis,RDBMS,..)
        self.sid = '@%x' % id(self)

    ################################################## text dump

    # callback for print
    def __repr__(self): return self.dump(test=True)

    # special dump for tests
    def test(self): return self.dump(test=True)

    # full tree dump
    def dump(self, done=None, depth=0, prefix='', test=False):
        # subtree header
        tree = self.pad(depth) + self.head(prefix, test)
        # block infinitive recursion on graph cycles
        if not done:
            done = set()  # initialize in the recursion root
        if self in done:
            return tree + ' _/'
        else:
            done.add(self)
        # slot{}s
        for i in self.slot:
            tree += self.slot[i].dump(done, depth + 1, '%s = ' % i, test)
        # nest[]ed
        idx = 0
        for j in self.nest:
            tree += j.dump(done, depth + 1, '%s = ' % idx, test)
            idx += 1
        # resulting subtree
        return tree

    # short-form dump: <T:V> header only
    def head(self, prefix='', test=False):
        header = '%s<%s:%s>' % (prefix, self._type(), self._val())
        if not test:
            header += ' %s' % self.sid
        return header

    # tree padding
    def pad(self, depth): return '\n' + '\t' * depth

    # type/class tag
    def _type(self): return self.__class__.__name__.lower()

    # .val dump must be tunable for strings, numbers,..
    def _val(self): return '%s' % self.val

    ################################################## operators

    # A[key]
    def __getitem__(self, key): return self.slot[key]

    # A[key] = B
    def __setitem__(self, key, that):
        self.slot[key] = that
        return self

    # A << B --> A[B.type] = B
    def __lshift__(self, that):
        return self.__setitem__(that._type(), that)

    # A >> B --> A[B.val] = B
    def __rshift__(self, that):
        return self.__setitem__(that.val, that)

    # A // B
    def __floordiv__(self, that):
        self.nest.append(that)
        return self

    ########################################### stack operations

    # ( 1 2 3 -- 1 2 3 ) -> 3
    def top(self): return self.nest[-1]
    # ( 1 2 3 -- 1 2 3 ) -> 2
    def tip(self): return self.nest[-2]
    # ( 1 2 3 -- 1 2 ) -> 3
    def pop(self): return self.nest.pop(-1)
    # ( 1 2 3 -- 1 3 ) -> 2
    def pip(self): return self.nest.pop(-2)

    # ( 1 2 3 -- 1 2 3 3 )
    def dup(self): return self // self.top()
    # ( 1 2 3 -- 1 2 )
    def drop(self): self.pop(); return self
    # ( 1 2 3 -- 1 3 2 )
    def swap(self): return self // self.pip()
    # ( 1 2 3 -- 1 2 3 2 )
    def over(self): return self // self.tip()
    # ( 1 2 3 -- 1 3 )
    def press(self): self.pip(); return self
    # ( 1 2 3 -- )
    def dropall(self): self.nest = []; return self

    ########################################### pattern matching

    def __iter__(self):
        for j in self.nest:
            yield j

    ################################################ computation

    def eval(self, ctx):
        raise TypeError(Error('eval') // self // ctx)

    def apply(self, that, ctx):
        raise TypeError(Error('apply') // self // that // ctx)

    ########################################## represent in html form

    def html(self):
        return '<pre>\n%s</pre>\n' % self.dump()

############################################################### error processing

class Error(Object):
    pass

##################################################################### primitives

class Primitive(Object):
    def eval(self, ctx): return self

class Symbol(Primitive):
    def eval(self, ctx):
        return ctx[self.val]
        if isinstance(item, Command):
            return item.eval(ctx)
        else:
            return item

class String(Primitive):

    def _val(self):
        s = ''
        for c in self.val:
            if c == '\n':
                s += r'\n'
            elif c == '\t':
                s += r'\t'
            else:
                s += c
        return s

    def html(self): return markdown(self.val, extensions=['extra'])

class Number(Primitive):
    def __init__(self, V): Primitive.__init__(self, float(V))

class Integer(Number):
    def __init__(self, V): Primitive.__init__(self, int(V))

class Hex(Integer):
    def __init__(self, V): Primitive.__init__(self, int(V[2:], 0x10))
    def _val(self): return hex(self.val)

class Bin(Integer):
    def __init__(self, V): Primitive.__init__(self, int(V[2:], 0x02))
    def _val(self): return bin(self.val)

###################################################################### container

class Container(Object):
    def eval(self, ctx): return self

class Vector(Container):
    def html(self):
        ht = ''
        for j in self.nest:
            ht += j.html()
        return ht

class Dict(Container):
    pass
class Stack(Container):
    pass
class Queue(Container):
    pass
class Set(Container):
    pass

######################################################################### active

class Active(Object):
    pass

class Command(Active):
    def __init__(self, F):
        Active.__init__(self, F.__name__)
        self.fn = F

    def eval(self, ctx):
        return self.fn(ctx)

    def apply(self, that, ctx):
        return self.fn(that, ctx)

class Op(Active):
    def eval(self, ctx):
        if self.val == '`':
            return self.nest[0]
        lvalue = self.nest[0].eval(ctx)
        rvalue = self.nest[1].eval(ctx)
        if self.val == '=':
            ctx[lvalue.val] = rvalue
            return rvalue
        elif self.val == '//':
            return lvalue // rvalue
        elif self.val == '<<':
            return lvalue << rvalue
        elif self.val == '>>':
            return lvalue >> rvalue
        elif self.val == ':':
            return lvalue.apply(rvalue, ctx)
        else:
            raise SyntaxError(self)

class VM(Active):

    # vm[key] = command
    def __setitem__(self, key, F):
        if callable(F):
            return Active.__setitem__(self, key, Command(F))
        else:
            return Active.__setitem__(self, key, F)

    # vm >> command
    def __rshift__(self, F):
        if callable(F):
            Active.__rshift__(self, Command(F))
        else:
            Active.__rshift__(self, F)


vm = VM('metaL')
vm << vm

#################################################### stack manipulation commands

vm['dup'] = lambda ctx: ctx.dup()
vm['drop'] = lambda ctx: ctx.drop()
vm['swap'] = lambda ctx: ctx.swap()
vm['over'] = lambda ctx: ctx.over()
vm['press'] = lambda ctx: ctx.press()
vm['dropall'] = lambda ctx: ctx.dropall()

########################################################################### meta

class Meta(Object):
    pass

class Class(Meta):
    def __init__(self, C):
        Meta.__init__(self, C.__name__.lower())
        self.cls = C

    def apply(self, that, ctx):
        return self.cls(that.val)

############################################################################# io

class IO(Object):
    pass

class File(IO):
    pass


vm >> Class(File)

############################################################################ net

class Net(IO):
    pass

class IP(Net, Primitive):
    pass


vm >> Class(IP)

class Port(Net, Primitive):
    pass


vm >> Class(Port)

class URL(Net, Primitive):
    pass

class Email(Net, Primitive):
    pass

#################################################################### documenting

class Doc(Object):
    pass

class HTML(Doc):
    def html(self): return self.val

################################################################## web interface


import flask, flask_wtf, wtforms

application = app = flask.Flask(vm.val)
app.config['SECRET_KEY'] = os.urandom(32)

class Web(Net):

    def eval(self, ctx):

        class CLI(flask_wtf.FlaskForm):
            pad = wtforms.TextAreaField('pad',
                                        render_kw={'rows': 5, 'autofocus': 'true'},)
            go = wtforms.SubmitField('GO: Ctrl+Enter')

        @app.route('/', methods=['GET', 'POST'])
        def index():
            form = CLI()
            if form.validate_on_submit():
                parser.parse(form.pad.data)
            return flask.render_template('index.html', web=self, ctx=ctx, form=form)

        @app.route('/css.css')
        def css():
            return flask.Response(
                flask.render_template('css.css', web=self, ctx=ctx),
                mimetype='text/css')

        @app.route('/static/<path:path>')
        def statics(path):
            return app.send_static_file(path)

        @app.route('/<path:path>.html')
        def tohtml(path):
            item = vm
            for i in path.split('/'):
                item = item[i]
            return flask.render_template('html.html', web=self, ctx=item)

        @app.route('/<path:path>', methods=['GET', 'POST'])
        def path(path):
            item = vm
            for i in path.split('/'):
                item = item[i]
            form = CLI()
            if form.validate_on_submit():
                parser.parse(form.pad.data)
            return flask.render_template('index.html', web=self, ctx=item, form=form)

        return self

        # app.run(
        #     host=ctx['IP'].val, port=ctx['PORT'].val,
        #     debug=True, extra_files=['metaL.ini'])

def WEB(ctx):
    web = ctx['WEB'] = Web(ctx.val)
    web << ctx['IP'] << ctx['PORT']
    web['logo'] = ctx['LOGO']
    return web.eval(ctx)


vm >> WEB

########################################################################## lexer

import ply.lex as lex

tokens = ['symbol', 'string',
          'number', 'integer', 'hex', 'bin',
          'eq', 'tick', 'push', 'lshift', 'rshift', 'colon', 'semicol',
          'url', 'email', 'ip',
          'nl', 'end', 'q', 'qq',
          'lp', 'rp', 'lq', 'rq', 'lc', 'rc']

t_ignore = ' \t\r'
t_ignore_comment = r'\#.*'

states = (('str', 'exclusive'),)

t_str_ignore = ''

def t_str(t):
    r'\''
    t.lexer.push_state('str')
    t.lexer.string = ''
def t_str_string(t):
    r'\''
    t.lexer.pop_state()
    t.value = String(t.lexer.string)
    return t
def t_str_nl(t):
    r'\n'
    t.lexer.string += t.value
def t_str_escaped(t):
    r'\\.'
    t.lexer.string += t.value[1]
def t_str_char(t):
    r'.'
    t.lexer.string += t.value

def t_nl(t):
    r'\n'
    t.lexer.lineno += 1
    return t

def t_qq(t):
    r'\?\?'
    return t
def t_q(t):
    r'\?'
    return t
def t_end(t):
    r'\.end'
    return t


t_lp = r'\('
t_rp = r'\)'
t_lq = r'\['
t_rq = r'\]'
t_lc = r'\{'
t_rc = r'\}'

def t_tick(t):
    r'`'
    t.value = Op(t.value)
    return t
def t_eq(t):
    r'='
    t.value = Op(t.value)
    return t
def t_push(t):
    r'//'
    t.value = Op(t.value)
    return t
def t_lshift(t):
    r'<<'
    t.value = Op(t.value)
    return t
def t_rshift(t):
    r'>>'
    t.value = Op(t.value)
    return t
def t_colon(t):
    r':'
    t.value = Op(t.value)
    return t
def t_semicol(t):
    r';'
    # t.value = Op(t.value)
    return t

def t_url(t):
    r'https?://[^ \t\r\n]+'
    t.value = URL(t.value)
    return t
def t_email(t):
    r'[a-z]+@[^ \t\r\n]+'
    t.value = Email(t.value)
    return t
def t_ip(t):
    r'([0-9]{1,3}\.){3}[0-9]{1,3}'
    t.value = IP(t.value)
    return t

def t_number_dot(t):
    r'[+\-]?[0-9]+\.[0-9]+'
    t.type = 'number'
    t.value = Number(t.value)
    return t
def t_number_expint(t):
    r'[+\-]?[0-9]+[eE][+\-]?[0-9]+'
    t.type = 'number'
    t.value = Number(t.value)
    return t
def t_hex(t):
    r'0x[0-9a-fA-F]+'
    t.value = Hex(t.value)
    return t
def t_bin(t):
    r'0b[01]+'
    t.value = Bin(t.value)
    return t
def t_integer(t):
    r'[+\-]?[0-9]+'
    t.value = Integer(t.value)
    return t

def t_symbol(t):
    r'[^ \t\r\n\#\{\}\[\]:;]+'
    t.value = Symbol(t.value)
    return t

def t_ANY_error(t): raise SyntaxError(t)


lexer = lex.lex()

############################################################# parser/interpreter

import ply.yacc as yacc

precedence = (
    ('right', 'eq'),
    ('left', 'push'),
    ('left', 'lshift', 'rshift'),
    ('nonassoc', 'tick', 'colon'),
)


def p_REPL_none(p):
    ' REPL : '
def p_REPL_q(p):
    ' REPL : REPL q '
    print(vm)
def p_REPL_qq(p):
    ' REPL : REPL qq '
    print(vm)
    sys.exit(0)
def p_REPL_end(p):
    ' REPL : REPL end '
    sys.exit(0)
def p_REPL_nl(p):
    ' REPL : REPL nl '
def p_REPL_semicol(p):
    ' REPL : REPL semicol '
    vm.dropall()
def p_REPL_recursuve(p):
    ' REPL : REPL ex '
    result = p[2].eval(vm)
    if isinstance(result, Command):
        result = result.eval(vm)
    else:
        if result:
            vm // result
    # print(p[2])
    # print(p[2].eval(vm))
    # print(vm)
    # print('-' * 80)

def p_ex_symbol(p):
    ' ex : symbol '
    p[0] = p[1]
def p_ex_string(p):
    ' ex : string '
    p[0] = p[1]
def p_ex_number(p):
    ' ex : number '
    p[0] = p[1]
def p_ex_integer(p):
    ' ex : integer '
    p[0] = p[1]
def p_ex_hex(p):
    ' ex : hex '
    p[0] = p[1]
def p_ex_bin(p):
    ' ex : bin '
    p[0] = p[1]
def p_ex_url(p):
    ' ex : url '
    p[0] = p[1]
def p_ex_email(p):
    ' ex : email '
    p[0] = p[1]
def p_ex_ip(p):
    ' ex : ip '
    p[0] = p[1]

def p_ex_tick(p):
    ' ex : tick ex '
    p[0] = p[1] // p[2]
def p_ex_colon_ex(p):
    ' ex : ex colon ex '
    p[0] = p[2] // p[1] // p[3]
def p_ex_eq(p):
    ' ex : ex eq ex '
    p[0] = p[2] // p[1] // p[3]
def p_ex_push(p):
    ' ex : ex push ex '
    p[0] = p[2] // p[1] // p[3]
def p_ex_lshift(p):
    ' ex : ex lshift ex '
    p[0] = p[2] // p[1] // p[3]
def p_ex_rshift(p):
    ' ex : ex rshift ex '
    p[0] = p[2] // p[1] // p[3]

def p_ex_parens(p):
    ' ex : lp ex rp '
    p[0] = p[2]


def p_ex_vector_named(p):
    ' ex : symbol lq vector rq '
    p[3].val = p[1].val
    p[0] = p[3]
def p_ex_vector(p):
    ' ex : lq vector rq '
    p[0] = p[2]
def p_vector(p):
    ' vector : '
    p[0] = Vector('')

def p_error(p): raise SyntaxError(p)


parser = yacc.yacc(debug=False, write_tables=False)

#################################################################### system init


with open(__file__[:-3] + '.ini') as ini:
    parser.parse(ini.read())


try:
    import uwsgi
    # https://uwsgi-docs.readthedocs.io/en/latest/PythonModule.html
    web = vm['WEB']

    def uwsgi_stop(ctx): uwsgi.stop()
    vm['BYE'] = Command(uwsgi_stop)

    opt = Dict('uwsgi.opt')
    web >> opt
    for i in uwsgi.opt:
        opt[i] = String(uwsgi.opt[i].decode())

    try:
        ip, port = uwsgi.opt['socket'].decode().split(':')
        web['ip'].val = ip
        web['port'].val = port
    except:
        pass

except ModuleNotFoundError:
    pass


if __name__ == '__main__':
    for srcfile in sys.argv[2:]:
        with open(srcfile) as src:
            parser.parse(src.read())
    app.run(
        host=vm['IP'].val, port=vm['PORT'].val,
        debug=True, extra_files=['metaL.ini']
    )
