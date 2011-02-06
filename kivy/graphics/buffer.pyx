include "common.pxi"

cdef class Buffer:
    '''Buffer class is designed to manage very fast a list of fixed size block.
    You can easily add and remove data from the buffer.
    '''
    def __cinit__(self):
        self.data = NULL
        self.block_size = 0
        self.block_count = 0
        self.l_free = []


    def __del__(self):
        if self.data != NULL:
            free(self.data)
            self.data = NULL
        self.block_count = 0
        self.block_size = 0
        self.l_free = []


    def __init__(self, int block_size):
        self.block_size = block_size


    cdef grow(self, int block_count):
        '''Automaticly realloc the memory if they are no enough block.
        Work only for "grow" operation, not the inverse.
        '''
        cdef void *newptr = NULL

        # set block_count to the nearest 8 block
        diff = block_count % 8
        if diff != 0:
            block_count = (8 - (block_count % 8)) + block_count

        if block_count < self.block_count:
            return

        # Try to realloc
        newptr = realloc(self.data, self.block_size * block_count)
        if newptr == NULL:
            raise SystemError('Unable to realloc memory for buffer')

        # Realloc work, put the new pointer
        self.data = newptr

        # Create the free blocks
        diff = block_count - self.block_count
        self.l_free.extend(range(self.block_count, self.block_count + diff))

        # Update how many block are allocated
        self.block_count = block_count


    cdef void add(self, void *blocks, int *indices, int count):
        '''Add a list of block inside our buffer
        '''
        cdef int i, block
        cdef void *p

        # Ensure that our buffer is enough for having all the elements
        if count > len(self.l_free):
            self.grow(self.block_count + count)

        # Add all the block inside our buffer
        for i in xrange(count):
            p = blocks + (self.block_size * i)

            # Take a free block
            block = self.l_free.pop(0)

            # Copy content
            memcpy(self.data + (block * self.block_size), p, self.block_size)

            # Push the current block as indices
            if indices != NULL:
                indices[i] = block


    cdef void remove(self, int *indices, int count):
        '''Remove block from our list
        '''
        cdef int i, m, value
        m = 0
        if self.l_free:
            m = max(self.l_free)

        for i in xrange(count):
            value = indices[i]

            # if the current indice is lower than the maximum
            # we'll have a hole. so, flag the buffer as needed for packing
            if value < m:
                self.need_pack = 1

            # Append the new indice as free block
            self.l_free.append(value)

    cdef void update(self, int index, void* blocks, int count):
        '''Update count number of blocks starting at index with the data in blocks
        '''
        memcpy(self.data + (index * self.block_size), blocks, self.block_size * count)


    cdef void pack(self):
        '''Ensure the memory is packed
        '''
        if not self.need_pack:
            return

        # Allocate a memory block that can contain the whole list
        cdef void *memory, *p
        cdef int i, j

        memory = p = malloc(self.block_count * self.block_size)
        if memory == NULL:
            raise SystemError('Unable to allocate memory for packing')

        j = 0
        for i in xrange(self.block_count):
            if i in self.l_free:
                continue
            memcpy(p, self.data + i * self.block_size, self.block_size)
            j += 1
            p += self.block_size

        # Replace the current memory buffer with new one
        if self.data:
            free(self.data)
        self.data = memory

        # Replace the free list
        self.l_free = range(j, self.block_count)


    cdef int count(self):
        '''Return how many block are currently used
        '''
        return self.block_count - len(self.l_free)


    cdef int size(self):
        '''Return the size of the allocated buffer
        '''
        return self.block_size * self.block_count


    cdef void *pointer(self):
        '''Return the data pointer
        '''
        return self.data

    cdef void *offset_pointer(self, int offset):
        return self.data + (offset * self.block_size)


'''
def run():
    cdef float a[6]
    cdef Buffer b

    a[0] = 1
    a[1] = 1
    a[2] = 1
    a[3] = 1
    a[4] = 1
    a[5] = 1

    b = Buffer(sizeof(float))
    print 'size=', b.size(), 'count=', b.count()
    f1 = b.add(a, 1)
    print 'indices', f1
    print 'size=', b.size(), 'count=', b.count()
    f2 = b.add(a, 1)
    print 'indices', f2
    print 'size=', b.size(), 'count=', b.count()
    f3 = b.add(a, 4)
    print 'indices', f3
    print 'size=', b.size(), 'count=', b.count()

    print 'remove====='
    b.remove(f2)
    print 'size=', b.size(), 'count=', b.count()
    f2 = b.add(a, 4)
    print 'indices', f2
    print 'size=', b.size(), 'count=', b.count()

    b.remove(f1)
    b.remove(f2)
    b.remove(f3)
    print 'size=', b.size(), 'count=', b.count()


if __name__ == '__main__':
    run()
'''
