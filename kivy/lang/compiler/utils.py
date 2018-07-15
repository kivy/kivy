from itertools import chain


class StringPool(object):

    pool = []

    prefix = 'var'

    tokens = {}

    def __init__(self, prefix='var'):
        super(StringPool, self).__init__()
        self.pool = []
        self.prefix = prefix
        self.tokens = {}

    def borrow(self, token, count=1):
        if token in self.tokens:
            item = self.tokens[token]
            item[2] += count
            return item[0]

        name = None
        for i, name in enumerate(self.pool):
            if name is not None:
                break

        if name is None:
            name = '{}_{}'.format(self.prefix, len(self.pool))
            i = len(self.pool)
            self.pool.append(None)
        else:
            self.pool[i] = None

        self.tokens[token] = [name, i, count]
        return name

    def borrow_persistent(self):
        return self.borrow(object())

    def return_back(self, token):
        item = self.tokens[token]
        if item[2] == 1:  # last usage
            del self.tokens[token]
            self.pool[item[1]] = item[0]
            return 0
        else:
            item[2] -= 1
            if item[2] < 0:
                raise Exception('{} is negative'.format(token))
            return item[2]

    def get_used_items(self):
        return self.pool

    def get_all_items(self):
        return set(chain(
            (item for item in self.pool if item is not None),
            (item[0] for item in self.tokens.values())))
