This code is a weekend project (so far), and something I've been
thinking about doing for a couple of months. As such, please consider
it to be experimental, but I'd love to hear what you think and get
pull requests on improving it.

Printing at 0.15mm layer height, with black and white PLA worked
really well, with the default parameters and no scaling in Cura, this
printed three layers of substrate and one layer of halftone mask.

![alt text](https://github.com/ak15199/image2stl/blob/media/lena-original.png)
![alt text](https://github.com/ak15199/image2stl/blob/media/lena-preview.png)
![alt text](https://github.com/ak15199/image2stl/blob/media/lena-printed.png)

Once you have your mask (the halftone), and substrate STLs, you'll
need to load them into your slicer. For Cura, and assuming that
you're using a dual-extruder printer, the process is:

* Load both STL files
* For each of the models, select the correct extruder
* Choose Edit->Select All
* Choose Edit->Group Models
* Move the combined image to the center of the print bed
* Otherwise scale/adjust as you like
* Adjust your print settings: Normal 0.15mm seems fine, add a brim
* Oh. I also added a prime tower.

That's it! A 512x512 original reduced to a 128x128 mask takes
about 2 1/2 hours to print at 128mmx128mm on an Ultimaker S5.

As with everything in 3D printing, your mileage *will* vary. There are
a number of tunable parameters, most common of which are:

* `density` (which defines how much plastic is extruded for a given shade of gray),
* `scale` (which defines how many pixels in the original image are averaged to determine one halftone dot).
* `min-radius` which provides a cutoff point, below which smaller cylinders will not be drawn. If you find that the printer's nozzle is getting clogged, then this may be a good one to tune up.

You may need to to tune, and there are almost certainly things that
I haven't considered! Run with `--help` for more detail.

```
alexk$ pip3 install -r requirements.txt
alexk$
```

```
alexk$ python3 mesh.py --density 0.65 --scale 2 nopecat.gif 
loading 'nopecat.gif'...
building halftone...
saving 'nopecat-mask.stl'...
building substrate...
saving 'nopecat-subs.stl'...
alexk$ python3 mesh.py --density 0.65 lena.jpg 
loading 'lena.jpg'...
building halftone...
saving 'lena-mask.stl'...
building substrate...
saving 'lena-subs.stl'...
alexk$ 
```




