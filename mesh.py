import click
import numpy as np
import os
from stl import mesh

import imageio

from skimage.transform import rotate, rescale, resize, downscale_local_mean

from mpl_toolkits import mplot3d
from matplotlib import pyplot

from math import radians

from abc import ABC, abstractmethod


class Objects(ABC):
    def __init__(self, instances, height=1, sides=10):
        self.v_off = 0
        self.instances = instances
        self.height = height
        self.sides = sides
        self.model = self._model()

    @abstractmethod
    def _model(self):
        pass

    def add(self, radius, px, py, pz):
        # don't draw zero diameter objects, they will screw up bounding box
        if not radius:
            return

        vertices, faces = self.model
        vertices = (vertices * (radius, radius, 1)) + (px, py, pz)

        # -- initalize superset first time around
        if not self.v_off:
            # this is way faster than rebuilding the array each time by
            # appending each new cylinder as it comes in... downside is
            # that we lose flexibility in # sides etc.
            self.v_off = 0
            self.f_off = 0
            self.v_len = len(vertices)
            self.f_len = len(faces)
            self.vertices = np.empty((self.instances * self.v_len, 3))
            self.faces = np.empty((self.instances * self.f_len, 3),
                                  dtype=np.int)

        # -- add these to superset, faces need to have their indexes bumped
        self.vertices[self.v_off:self.v_off + self.v_len] = vertices
        self.faces[self.f_off:self.f_off + self.f_len] = self.v_off + faces

        self.v_off += self.v_len
        self.f_off += self.f_len

    def rotated(self, angle):
        # https://en.wikipedia.org/wiki/Rotation_matrix
        theta = np.radians(angle)
        c, s = np.cos(theta), np.sin(theta)

        R = np.array(((c, -s, 0), (s, c, 0), (0, 0, 1)))

        return self.vertices.dot(R)


class Cylinders(Objects):
    def _model(self):
        c = np.linspace(0, 2 * np.pi, self.sides)
        x = np.sin(c)
        y = np.cos(c)

        # -- calculate vertices
        vertices = np.zeros((2 + 2 * self.sides, 3))

        # center top and bottom of cylinder
        vertices[2 * self.sides] = (0, 0, 0)
        vertices[2 * self.sides + 1] = (0, 0, self.height)

        # side vertices
        for i in range(self.sides):
            vertices[i] = (x[i], y[i], 0)
            vertices[i + self.sides] = (x[i], y[i], self.height)

        # -- calculate faces
        faces = np.zeros((4 * self.sides, 3), dtype=np.int)

        for i in range(self.sides):
            j = (i + 1) % self.sides  # adjacent vertice
            faces[i] = (i + self.sides, j, i)  # mainly botton triangle
            faces[self.sides + i] = (i + self.sides, j + self.sides, j
                                     )  #mainly top
            faces[2 * self.sides + i] = (2 * self.sides, i, j)  # bottom slice
            faces[3 * self.sides + i] = (1 + 2 * self.sides, j + self.sides,
                                         i + self.sides)  # top slice

        return (vertices, faces)


class Cuboids(Objects):
    def _model(self):
        # 12 triangles, 6 faces, 8 vertices
        vertices = np.array((
            (-1, -1, 0),
            (1, -1, 0),
            (1, 1, 0),
            (-1, 1, 0),
            (-1, -1, self.height),
            (1, -1, self.height),
            (1, 1, self.height),
            (-1, 1, self.height),
        ))

        faces = np.array((
            (0, 1, 4),
            (4, 1, 5),
            (1, 2, 5),
            (5, 6, 2),
            (2, 3, 6),
            (6, 3, 7),
            (3, 0, 7),
            (7, 0, 4),
            (7, 4, 6),
            (4, 5, 6),
            (2, 0, 3),
            (2, 1, 0),
        ))

        return (vertices, faces)


class Stl(ABC):
    def __init__(self, height=1, ox=0, oy=0, oz=0):
        self.height = height
        self.ox = ox
        self.oy = oy
        self.oz = oz

    def _mesh(self):
        # Create the mesh
        msh = mesh.Mesh(np.zeros(self.faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(self.faces):
            for j in range(3):
                msh.vectors[i][j] = self.vertices[f[j], :]

        # this might would work instead of Cylinders.rotated()
        # msh.rotate(axis=(0, 0, 0.5), theta=radians(45))

        if not (msh.is_closed() or msh.check()):
            click.echo("There is a problem with the mesh", err=True)
            exit(1)

        return msh

    def save(self, filename):
        name = os.path.basename(filename)
        click.echo(f"saving '{name}'...")
        self._mesh().save(filename)

    def show(self):
        click.echo("plotting...")
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

    def translate(self, x=0, y=0, z=0):
        self.vertices += (x, y, z)

    def bounds(self):
        msh = self._mesh()

        origin = msh.min_
        extent = msh.max_ - msh.min_

        return (origin, extent)

    def orient(self, x=0, y=0, z=0):
        # set axis flag to 1 in order to activate
        # orient (x,y,z) around the origin
        # for each, subtract offset and half of extent

        origin, extent = self.bounds()

        self.translate(
            -(origin[0] + extent[0] / 2) * x,
            -(origin[1] + extent[1] / 2) * y,
            -(origin[2] + extent[2] / 2) * z,
        )


class Halftone(Stl):
    def load(self, filename, scale=1):
        name = os.path.basename(filename)
        click.echo(f"loading '{name}'...")

        img = imageio.imread(filename)
        img = np.dot(img[..., :3], [0.2989, 0.5870, 0.1140])
        img = resize(img, (img.shape[0] // scale, img.shape[1] // scale),
                     anti_aliasing=True, mode='constant')
        shape = np.array(np.shape(img))
        img = 1 - (img / 255)

        # we rotate to give a 45 degree mask
        img = rotate(img, 45, resize=True, cval=0, mode='constant')

        click.echo("building halftone...")
        w, h = np.shape(img)
        c = Cylinders(w * h, height=self.height, sides=10)
        for y in range(h):
            for x in range(w):
                c.add(img[x, y] * .75, self.oy + y, self.ox + w - x, self.oz)

        # rotate back so it doesn't look weird
        self.vertices = c.rotated(45)
        self.faces = c.faces


class Substrate(Stl):
    def build(self, shape):
        click.echo("building substrate...")

        c = Cuboids(1, self.height)

        c.add(max(shape), self.ox, self.oy, self.oz)

        self.vertices = c.vertices
        self.faces = c.faces


@click.command()
@click.argument('filename', type=click.Path(exists=True))
@click.option('--substrate-height', default=1.0, help='Height of substrate')
@click.option('--halftone-height', default=0.2, help='Height of halftone')
@click.option('--scale', default=4, help='Scale-down factor')
@click.option('--show/--no-show',
              default=False,
              is_flag=True,
              help='Display halftone in pyplot instead of printing')
def main(filename, substrate_height, halftone_height, scale, show):

    target = os.path.splitext(filename)[0]

    halftone = Halftone(height=halftone_height)
    halftone.load(filename, scale=scale)
    halftone.orient(x=1, y=1, z=1)
    halftone.translate(z=substrate_height + halftone_height / 2)
    if show:
        halftone.show()
        exit(0)
    else:
        halftone.save(f"{target}-mask.stl")

    substrate = Substrate(height=substrate_height)

    origin, extent = halftone.bounds()

    substrate.build((extent[0] / 2, extent[1] / 2))
    substrate.orient(x=1, y=1, z=1)
    substrate.translate(z=substrate_height / 2)
    substrate.save(f"{target}-subs.stl")


if __name__ == "__main__":
    main()
