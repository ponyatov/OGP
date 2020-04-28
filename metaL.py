################################## metaL/kb: Knowledge Base engine /Python core/
############################# (c) Dmitry Ponyatov <dponyatov@gmail.com> 2020 MIT
######################################### github: https://github.com/ponyatov/kb

def comment(text, width=80):
    print('#' * (width - len(text) - 1) + ' ' + text)
# comment('kb: Knowledge Base engine /Python core/')#pattern matching', 60) ; sys.exit(-1)

################################################################# system modules


import os, sys

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

    ########################################### pattern matching

    def __iter__(self):
        for j in self.nest:
            yield j

    ################################################ computation

    def eval(self, ctx):
        raise TypeError(Error('eval') // self // ctx)

    def apply(self, that, ctx):
        raise TypeError(Error('apply') // self // that // ctx)

############################################################### error processing

class Error(Object):
    pass

##################################################################### primitives

class Primitive(Object):
    def eval(self, ctx): return self

class Symbol(Primitive):
    def eval(self, ctx): return ctx[self.val]

class String(Primitive):
    pass

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
    pass
class Vector(Container):
    pass
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
    pass


vm = VM('metaL')
vm << vm

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

################################################################## web interface


import flask

application = app = flask.Flask(vm.val)
app.config['SECRET_KEY'] = os.urandom(32)

class Web(Net):

    def eval(self, ctx):

        @app.route('/')
        def index():
            #, form=form)
            return flask.render_template('index.html', web=self, ctx=ctx)

        @app.route('/css.css')
        def css():
            return flask.Response(
                flask.render_template('css.css', web=self, ctx=ctx),
                mimetype='text/css')

        @app.route('/static/<path:path>')
        def statics(path):
            return app.send_static_file(path)

        # app.run(
        #     host=ctx['IP'].val, port=ctx['PORT'].val,
        #     debug=True, extra_files=['metaL.ini'])

def WEB(that, ctx):
    web = ctx['WEB'] = Web(that.val)
    web << ctx['IP'] << ctx['PORT'] << ctx['LOGO']
    return web.eval(ctx)


vm >> Command(WEB)

########################################################################## lexer

import ply.lex as lex

tokens = ['symbol', 'string',
          'number', 'integer', 'hex', 'bin',
          'eq', 'tick', 'push', 'lshift', 'rshift', 'colon',
          'url', 'email', 'ip',
          'nl', ]

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
def t_str_char(t):
    r'.'
    t.lexer.string += t.value

def t_nl(t):
    r'\n'
    t.lexer.lineno += 1
    return t

def t_tick(t):
    r'`'
    t.value = Op(t.value)
    return t
def t_colon(t):
    r':'
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

def t_integer(t):
    r'[+\-]?[0-9]+'
    t.value = Integer(t.value)
    return t

def t_symbol(t):
    r'[^ \t\r\n\#\{\}\[\]:]+'
    t.value = Symbol(t.value)
    return t

def t_ANY_error(t): raise SyntaxError(t)


lexer = lex.lex()

######################################################################### parser

import ply.yacc as yacc

precedence = (
    ('right', 'eq'),
    ('left', 'push'),
    ('left', 'lshift', 'rshift'),
    ('nonassoc', 'tick', 'colon'),
)

def p_REPL_none(p):
    ' REPL : '
    pass
def p_REPL_nl(p):
    ' REPL : REPL nl '
    pass
def p_REPL_recursuve(p):
    ' REPL : REPL ex '
    print(p[2])
    print(p[2].eval(vm))
    # print(vm)
    print('-' * 80)

def p_ex_symbol(p):
    ' ex : symbol '
    p[0] = p[1]
def p_ex_string(p):
    ' ex : string '
    p[0] = p[1]
def p_ex_integer(p):
    ' ex : integer '
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
    ' ex : symbol colon ex '
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
