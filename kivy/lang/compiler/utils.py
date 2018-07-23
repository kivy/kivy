from itertools import chain

__all__ = ('StringPool', )


class StringPool(object):
    '''
    A pool of strings that we can borrow from. Strings can be reused or
    borrowed permanently. It just keeps incrementing and adding more items to
    the pool as needed, but reuses first. E.g. ::

        >>> obj1 = object()
        >>> obj2 = object()
        >>> pool = StringPool()
        >>> pool.borrow(obj1, 3)
        'var_0'
        >>> pool.borrow(obj2, 1)
        'var_1'
        >>> pool.borrow_persistent()
        'var_2'
        >>> pool.borrow_persistent()
        'var_3'
        >>> pool.return_back(obj1)
        2
        >>> pool.return_back(obj1)
        1
        >>> pool.borrow_persistent()
        'var_4'
        >>> pool.return_back(obj1)
        0
        >>> pool.borrow_persistent()
        'var_0'
        >>> pool.return_back(obj2)
        0
        >>> pool.borrow_persistent()
        'var_1'
        >>> pool.borrow_persistent()
        'var_5'
    '''

    pool = []

    prefix = 'var'

    tokens = {}

    def __init__(self, prefix='var'):
        super(StringPool, self).__init__()
        self.pool = []
        self.prefix = prefix
        self.tokens = {}

    def borrow(self, token, count=1):
        '''
        Borrows a item for the token.
        :param token: The token that is borrowing the item.
        :param count: The number of times the item will be borrowed.
        :return: A value from the pool.
        '''
        if not count:
            raise ValueError('Count cannot be zero')

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
        '''
        Borows a items from the pool permanently (will never be returned).
        :return: The item from the pool.
        '''
        return self.borrow(object())

    def return_back(self, token):
        '''
        Returns a an item borrowed from the pool by the token. The token must
        return the items for as many times as it borrowed it.
        :param token: The token that borrowed an item.
        :return: The number of times the token still borrowed the item from the
            pool, after the current return.
        '''
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

    def get_num_borrowed(self):
        '''
        :return: The number of items currently borrowed.
        '''
        return len([item for item in self.pool if item is None])

    def get_available_items(self):
        '''
        :return: The list of items currently available to be borrowed by the
            pool, that has been borrowed previously (obviously we have an
            infinite list if we also include items not yet borrowed).
        '''
        return [item for item in self.pool if item is not None]

    def get_all_items(self):
        '''
        :return: all the items that has been borrowed or are currently
            borrowed.
        '''
        return set(chain(
            (item for item in self.pool if item is not None),
            (item[0] for item in self.tokens.values())))
