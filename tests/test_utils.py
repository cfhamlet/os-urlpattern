from os_urlpattern.utils import Bag


def test_bag():
    bag01 = Bag()
    bag02 = Bag()
    for i in range(1, 3):
        bag01.add(i)
        bag02.add(2 + i)
    bag = Bag()
    bag.add(bag02)
    bag.add(bag01)
    assert bag01[0] == 1
    assert bag02[0] == 3
    assert bag[0] == bag02
    assert bag.pick() == bag02[0]

    for i, j in zip(bag01, range(1, 3)):
        assert i == j

    s = set(range(1, 5))
    b = set()
    for i in bag.iter_all():
        b.add(i)
    assert s == b
