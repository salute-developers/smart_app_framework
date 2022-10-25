class A:
    def __init__(self):
        self.a=2

class B(A):
    __slots__ = ['b']
    def __init__(self):
        super(B, self).__init__()
        self.b=2

b=B()
b.c=2
print(b.__dict__)