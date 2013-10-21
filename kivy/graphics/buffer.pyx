include "common.pxi"

cdef class Buffer:
    '''Buffer class is designed to manage very fast a list of fixed size block.
    You can easily add and remove data from the buffer.
    '''
    def __cinit__(self):
        self.data = NULL
        self.i_free = 0
        self.block_size = 0
        self.block_count = 0
        self.l_free = NULL

    def __dealloc__(self):
        if self.data != NULL:
            free(self.data)
            self.data = NULL
        self.block_count = 0
        self.block_size = 0
        if self.l_free != NULL:
            free(self.l_free)

    def __init__(self, long block_size):
        self.block_size = block_size

    cdef void grow(self, long block_count):
        '''Automaticly realloc the memory if they are no enough block.
        Work only for "grow" operation, not the inverse.
        '''
        cdef void *newptr = NULL
        cdef long i
        cdef int l_free_tmp
        cdef long diff

        # set block_count to the nearest 8 block
        diff = block_count % 8
        if diff != 0:
            block_count = (8 - (block_count % 8)) + block_count

        if block_count <= self.block_count:
            return

        # Try to realloc
        newptr = realloc(self.data, self.block_size * block_count)
        if newptr == NULL:
            raise SystemError('Unable to realloc memory for buffer')

        # Realloc work, put the new pointer
        self.data = newptr

        # Create the free blocks
        newptr = realloc(self.l_free, sizeof(int) * block_count)
        if newptr == NULL:
            raise SystemError('Unable to realloc memory for free list')
        self.l_free = <int *>newptr

        # Initialize the list with index of free block
        for i in xrange(self.block_count, block_count):
            self.l_free[i] = <int>i

        # Update how many block are allocated
        self.block_count = block_count

    cdef void clear(self):
        '''Clear the whole buffer, and mark all blocks as available.
        '''
        cdef long i
        for i in xrange(self.block_count):
            self.l_free[i] = <int>i
        self.i_free = 0

    cdef void add(self, void *blocks, unsigned short *indices, int count):
        '''Add a list of block inside our buffer
        '''
        cdef int i, block
        cdef void *p

        # Ensure that our buffer is enough for having all the elements
        if count > self.block_count - self.i_free:
            self.grow(self.block_count + count)

        # Add all the block inside our buffer
        for i in xrange(count):
            p = <void *>(<char *>blocks + (self.block_size * i))

            # Take a free block
            block = self.l_free[self.i_free]
            self.i_free += 1

            # Copy content
            memcpy(<char *>(self.data) + (block * self.block_size), p, self.block_size)

            # Push the current block as indices
            if indices != NULL:
                indices[i] = block

    cdef void remove(self, unsigned short *indices, int count):
        '''Remove block from our list
        '''
        cdef int i

        for i in xrange(count):
            # Append the new indice as free block
            self.i_free -= 1
            self.l_free[self.i_free] = indices[i]

    cdef void update(self, int index, void* blocks, int count):
        '''Update count number of blocks starting at index with the data in blocks
        '''
        memcpy(<char *>(self.data) + (index * self.block_size), blocks, self.block_size * count)

    cdef int count(self):
        '''Return how many block are currently used
        '''
        return self.i_free

    cdef long size(self):
        '''Return the size of the allocated buffer
        '''
        return self.block_size * self.block_count

    cdef void *pointer(self):
        '''Return the data pointer
        '''
        return self.data

    cdef void *offset_pointer(self, int offset):
        return <char *>(self.data) + (offset * self.block_size)

