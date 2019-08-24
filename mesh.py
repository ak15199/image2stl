import numpy as np
from scipy import misc
from stl import mesh

import imageio
from skimage.transform import rescale, resize, downscale_local_mean

from mpl_toolkits import mplot3d
from matplotlib import pyplot


class Cylinders(object):

    def __init__(self, height=1, sides=10):
        self.vertices = np.empty((0, 3))
        self.faces = np.empty((0, 3), dtype=np.int)
        self.count = 0
        self.height = height
        self.sides = sides

    def add(self, radius, px, py):
        c = np.linspace(0, 2*np.pi, self.sides)
        x = px + radius * np.sin(c)
        y = py + radius * np.cos(c)

        # calculate vertices
        vertices = np.zeros((2+2*self.sides, 3))

        # center top and bottom of cylinder
        vertices[2*self.sides] = (px, py, 0)
        vertices[2*self.sides+1] = (px, py, self.height)

        for i in range(self.sides):
            vertices[i] = (x[i], y[i], 0)
            vertices[i+self.sides] = (x[i], y[i], self.height)
            # add two for center hi & low

        # calculate faces
        faces = np.zeros((4*self.sides, 3), dtype=np.int)

        for i in range(self.sides):
            j = (i+1) % self.sides
            faces[i] = (i+self.sides, j, i)
            faces[self.sides+i] = (i+self.sides, j+self.sides, j)
            faces[2*self.sides+i] = (2*self.sides, i, j)
            faces[3*self.sides+i] = (1+2*self.sides, j+self.sides, i+self.sides)

        self.vertices = np.vstack((self.vertices, vertices))
        self.faces = np.vstack((self.faces, self.count+faces))

        self.count += len(vertices)


class Halftone(object):

    def __init__(self):
        self.vertices = np.empty((0, 3))
        self.faces = np.empty((0, 3), dtype=np.int)

    def save(self, filename):
        # Create the mesh
        msh = mesh.Mesh(np.zeros(self.faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(self.faces):
            for j in range(3):
                msh.vectors[i][j] = self.vertices[f[j],:]

        # Create a new plot
        figure = pyplot.figure()
        axes = mplot3d.Axes3D(figure)

        # Load the STL files and add the vectors to the plot
        axes.add_collection3d(mplot3d.art3d.Poly3DCollection(msh.vectors))

        # Auto scale to the mesh size
        scale = msh.points.flatten(order='C')
        axes.auto_scale_xyz(scale, scale, scale)

        msh.save(filename)

        # Show the plot to the screen
        pyplot.show()


c = Cylinders(height=.1, sides=10)

img = imageio.imread('img.gif')
img = np.dot(img[...,:3], [0.2989, 0.5870, 0.1140])

scale= 1
img = resize(img, (img.shape[0] // scale, img.shape[1] // scale),
                       anti_aliasing=True)
img = 255-img

w, h = np.shape(img)

for y in range(h):
    for x in range(w):
        c.add(img[x,y]/400, y, w-x)


h = Halftone()
h.vertices = c.vertices
h.faces = c.faces
h.save("mesh.stl")
