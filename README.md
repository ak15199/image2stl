This code is a weekend project (so far), and something I've been
thinking about doing for a couple of months. AS such, please consider
it to be experimental, but I'd love to hear what you think and get
pull requests on improving it.

Printing at 0.15mm layer height, with black and white PLA worked
really well, with the default parameters and no scaling in Cura, this
printed three layers of substrate and one layer of halftone mask.

As with everything in 3D printing, your mileage will vary. There are
a number of tunable parameters, most common if which might be `density`
(which defines how much plastic is extruded for a given shade of
gray), and `scale` (which defines how many pixels in the original
image are averaged to determine one halftone dot).

You may need to to tune, and there are almost certainly things thatr
 I hadn't considered!


```
alexk$ python3 mesh.py --density 0.65 lena.jpg 
loading 'lena.jpg'...
building halftone...
saving 'lena-mask.stl'...
building substrate...
saving 'lena-subs.stl'...
alexk$ 
```
