import sys, pathlib
sys.path.append(pathlib.Path(__file__).parent.parent.as_posix())

from library.overload import overload

class A:
    def __init__(self) -> None:
        pass

    @overload
    def exe(self, a: int):
        print(a)
    @overload
    def exe(self, a:int ,b: int):
        print(a, b)

def main():
    c = 'hello'
    d = 'world'
    # a = A()
    # a.exe(c)
    # a.exe(c, d)
    exec(c)
    exec(c, d)
    pass


if __name__ == '__main__':
    main()