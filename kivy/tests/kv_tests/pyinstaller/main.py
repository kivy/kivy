
from project.widgets import MyWidget

if __name__ == '__main__':
    w = MyWidget()
    w.apply_kv()

    assert w.x == w.y
    w.y = 868
    assert w.x == 868
    w.y = 370
    assert w.x == 370
