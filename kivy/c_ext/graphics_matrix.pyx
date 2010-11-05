from kivy.lib.transformations import matrix_multiply, identity_matrix

cdef class MatrixStack:
    def __init__(self, context):
        self.context = context
        self.stack = [identity_matrix()]

    def pop(self):
        self.stack.pop()
        self.context.set('modelview_mat', self.stack[-1])

    def push(self):
        mat = matrix_multiply(identity_matrix(), self.stack[-1])
        self.stack.append(mat)

    cpdef apply(self, mat):
        self.stack[-1] = matrix_multiply(mat, self.stack[-1])
        self.context.set('modelview_mat', self.stack[-1])

    def transform(self):
        return self.stack[-1]


