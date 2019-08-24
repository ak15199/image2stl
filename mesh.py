import numpy as np
from stl import mesh

import imageio

from skimage.transform import rotate, rescale, resize, downscale_local_mean

from mpl_toolkits import mplot3d
from matplotlib import pyplot

from math import radians


class Cylinders(object):

    def __init__(self, pixels, height=1, sides=10):
        self.v_off = 0
        self.pixels = pixels
        self.height = height
        self.sides = sides
        self.model = self._model()

    def _model(self):
        c = np.linspace(0, 2*np.pi, self.sides)
        x = np.sin(c)
        y = np.cos(c)

        # -- calculate vertices
        vertices = np.zeros((2+2*self.sides, 3))

        # center top and bottom of cylinder
        vertices[2*self.sides] = (0, 0, 0)
        vertices[2*self.sides+1] = (0, 0, self.height)

        # side vertices
        for i in range(self.sides):
            vertices[i] = (x[i], y[i], 0)
            vertices[i+self.sides] = (x[i], y[i], self.height)

        # -- calculate faces
        faces = np.zeros((4*self.sides, 3), dtype=np.int)

        for i in range(self.sides):
            j = (i+1) % self.sides  # adjacent vertice
            faces[i] = (i+self.sides, j, i)  # mainly botton triangle
            faces[self.sides+i] = (i+self.sides, j+self.sides, j)  #mainly top
            faces[2*self.sides+i] = (2*self.sides, i, j)  # bottom slice
            faces[3*self.sides+i] = (1+2*self.sides, j+self.sides, i+self.sides)  # top slice

        return (vertices, faces)

    def add(self, radius, px, py):
        vertices, faces = self.model
        vertices = (vertices * radius) + (px, py, 1)
        
        # -- initalize superset first time around
        if not self.v_off:
            # this is way faster than rebuilding the array each time by
            # appending each new cylinder as it comes in
            self.v_off = 0
            self.f_off = 0
            self.v_len = len(vertices)
            self.f_len = len(faces)
            self.vertices = np.empty((self.pixels*self.v_len, 3))
            self.faces = np.empty((self.pixels*self.f_len, 3), dtype=np.int)

        # -- add these to superset, faces need to have their indexes bumped
        self.vertices[self.v_off:self.v_off+self.v_len] = vertices
        self.faces[self.f_off:self.f_off+self.f_len] = self.v_off+faces

        self.v_off += self.v_len
        self.f_off += self.f_len


class Halftone(object):

    def __init__(self):
        pass

    def load(self, filename, scale=1):
        print("loading...")

        img = imageio.imread('img.gif')
        img = np.dot(img[...,:3], [0.2989, 0.5870, 0.1140])
        img = 1-(img/255)
        img = rotate(img, 45, resize=True, cval=0, mode='constant')
        img = resize(img, (img.shape[0] // scale, img.shape[1] // scale),
                               anti_aliasing=True)


        w, h = np.shape(img)
        c = Cylinders(w*h, height=.3, sides=10)
        for y in range(h):
            for x in range(w):
                if x == 0:
                    print(img[x, y], end=" ")
                   
                c.add(img[x,y]*.75, y, w-x)

        self.vertices = c.vertices
        self.faces = c.faces

    def _mesh(self):
        # Create the mesh
        msh = mesh.Mesh(np.zeros(self.faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(self.faces):
            for j in range(3):
                msh.vectors[i][j] = self.vertices[f[j],:]

        #msh.rotate(axis=(0, 0, 0.5), theta=radians(45))

        if not (msh.is_closed() or msh.check()):
            print("There is a problem with the mesh")
            exit(1)

        return msh

    def save(self, filename):
        print("saving...")
        self._mesh().save(filename)

    def plot(self):
        print("ploting...")
        msh = self._mesh()

        # Create a new plot
        figure = pyplot.figure()
        axes = mplot3d.Axes3D(figure)

        # Load the STL files and add the vectors to the plot
        axes.add_collection3d(mplot3d.art3d.Poly3DCollection(msh.vectors))

        # Auto scale to the mesh size
        scale = msh.points.flatten(order='C')
        axes.auto_scale_xyz(scale, scale, scale)

        # Show the plot to the screen
        pyplot.show()


h = Halftone()
h.load("img.gif", scale=4)
h.save("mesh.stl")
#h.plot()
