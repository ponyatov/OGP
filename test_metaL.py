############################################### pytest suite for metaL.py engine

import pytest

from metaL import *

class TestObject:

    def hello(self): return Object('Hello')
    def world(self): return Object('World')

    def test_hello(self):
        assert self.hello().test() == '\n<object:Hello>'

    def test_world(self):
        assert (self.hello() // self.world()).test() == (
            '\n<object:Hello>\n\t0 = <object:World>')
        self.test_hello()

    def test_operators(self):
        hello = self.hello()
        assert \
            (hello // self.world() << Object('left') >> Object('right')).test() == (
                '\n<object:Hello>\n\tobject = <object:left>\n\tright = <object:right>\n\t0 = <object:World>')
        with pytest.raises(KeyError):
            hello['left']
        assert \
            hello['right'].test() == '\n<object:right>'

    def test_stackops(self):
        st = Object('')
        assert st.test() == '\n<object:>'
        assert (st // Object(1) // Object(2)).test() == (
            '\n<object:>\n\t0 = <object:1>\n\t1 = <object:2>')
        assert st.dup().test() == (
            '\n<object:>\n\t0 = <object:1>\n\t1 = <object:2>\n\t2 = <object:2> _/')
        assert st.drop().test() == (
            '\n<object:>\n\t0 = <object:1>\n\t1 = <object:2>')
        assert st.swap().test() == (
            '\n<object:>\n\t0 = <object:2>\n\t1 = <object:1>')
        assert st.over().test() == (
            '\n<object:>\n\t0 = <object:2>\n\t1 = <object:1>\n\t2 = <object:2> _/')
        assert st.press().test() == (
            '\n<object:>\n\t0 = <object:2>\n\t1 = <object:2> _/')
        assert st.dropall().test() == '\n<object:>'

def test_vm(): assert vm.head(test=True) == '<vm:metaL>'

class TestInit:

    def test_nest(self):
        assert vm.nest

    def test_IP(self):
        assert vm['IP'].test() == (
            '\n<ip:127.0.0.1>')

    def test_PORT(self):
        assert vm['PORT'].test() == (
            '\n<port:12345>')
