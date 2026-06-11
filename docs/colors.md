# Colors

!!! danger "All credits go to Barney"
    This page is a copy of Barney Potter's colors page. If in doubt of the right colors, ask him!

    _'And never use a rainbow color schema'~ Barney Potter_

Picking good colors is important for both scientific clarity and aesthetics.
Poorly chosen colors may misrepresent data because of color palette artifacts, or make people disinclined to look at a figure because it is ugly.
To that end, I'm dumping color related stuff here so that it is easier to find in the future.

## Useful links

[Viz Palette](https://projects.susielu.com/viz-palette): I use this a lot. Gives you a very quick look at how a set of colors work together. Gives each one a qualitative name, does colorblindness comparisons (that are easy to look at), and lets you tweak the colors pretty easily.

![Viz Palette](images/viz-palette.png)

### Papers

Here is a paper on [The misuse of color in science communication](https://www.nature.com/articles/s41467-020-19160-7?source=techstories.org) (Crameri et al. 2020).

### Color palette generators

[i want hue](https://medialab.github.io/iwanthue/): a (semi-random) palette generator for n-colors. They let you determine the parameters of your palette, then use an algorithm to draw colors from those parameters. They give you lots of useful tutorials and examples for how to generate palettes, and have a colorblindness comparison that is a bit hard to parse, but quite helpful.

[colorpicker](https://tristen.ca/hcl-picker/#/clh/7/289/520156/EFB8CB): an easy way to export a palette of n perceptually uniform colors based on the HSLuv palette; it just interpolates between two chosen colors. Super easy to use. They also let you visualize the palette on a choropleth.

[colorbrewer2](https://colorbrewer2.org/#type=sequential&scheme=BuGn&n=3): doesn't give you much control, but it does let you quickly select a good palette among several presets, filtered by things like colorblind friendliness, print friendliness and nature of the data.

[hclwizard](https://hclwizard.org/): has a _lot_ of finicky (though not secure SSL'd) tools for picking colors, visualizing colorblindness, and selecting HCL colors.

[HSLuv](https://www.hsluv.org/): billed as a "human friendly" alternative to HSL. It is designed as a perceputally uniform color space. This website gives some info on the palette, as well as lets you explore and pick a single value from the space. Probably nice for generating a seed hex.

## Discrete color palettes

Some good (and not-so-good) color palettes that I've used for either figures or for my computer setup.

### Gytis' colors

Color palette sent to me by Gytis Dudas that he really likes:
[link](https://projects.susielu.com/viz-palette?colors=[%22#4c72a5%22,%22#48a365%22,%22#d0694a%22,%22#e1c72f%22,%22#cc79a7%22,%22#77bedb%22,%22#7f6e85%22,%22#ccc197%22]&backgroundColor=%22white%22&fontColor=%22black%22&mode=%22normal%22)

-   ![#4c72a5](https://placehold.co/15x15/4c72a5/4c72a5.png) `#4c72a5`
-   ![#48a365](https://placehold.co/15x15/48a365/48a365.png) `#48a365`
-   ![#d0694a](https://placehold.co/15x15/d0694a/d0694a.png) `#d0694a`
-   ![#e1c72f](https://placehold.co/15x15/e1c72f/e1c72f.png) `#e1c72f`
-   ![#cc79a7](https://placehold.co/15x15/cc79a7/cc79a7.png) `#cc79a7`
-   ![#77bedb](https://placehold.co/15x15/77bedb/77bedb.png) `#77bedb`
-   ![#7f6e85](https://placehold.co/15x15/7f6e85/7f6e85.png) `#7f6e85`
-   ![#ccc197](https://placehold.co/15x15/ccc197/ccc197.png) `#ccc197`

### [Gruvbox](https://github.com/morhetz/gruvbox)

This [palette](https://projects.susielu.com/viz-palette?colors=[%22#cc241d%22,%22#98971a%22,%22#d79921%22,%22#458588%22,%22#b16286%22,%22#689d6a%22,%22#d65d0e%22,%22#282828%22]&backgroundColor=%22#fbf1c7%22&fontColor=%22#3c3836%22&mode=%22normal%22) makes up the "core" gruvbox palette.

-   ![#cc241d](https://placehold.co/15x15/cc241d/cc241d.png) `#cc241d`
-   ![#98971a](https://placehold.co/15x15/98971a/98971a.png) `#98971a`
-   ![#d79921](https://placehold.co/15x15/d79921/d79921.png) `#d79921`
-   ![#458588](https://placehold.co/15x15/458588/458588.png) `#458588`
-   ![#b16286](https://placehold.co/15x15/b16286/b16286.png) `#b16286`
-   ![#689d6a](https://placehold.co/15x15/689d6a/689d6a.png) `#689d6a`
-   ![#d65d0e](https://placehold.co/15x15/d65d0e/d65d0e.png) `#d65d0e`
-   ![#282828](https://placehold.co/15x15/282828/282828.png) `#282828`

### Dark gruvbox colors

The other option for the above ([link](https://projects.susielu.com/viz-palette?colors=[%22#9d0006%22,%22#79740e%22,%22#b57614%22,%22#076678%22,%22#8f3f71%22,%22#427b58%22,%22#af3a03%22]))

-   ![#9d0006](https://placehold.co/15x15/9d0006/9d0006.png) `#9d0006`
-   ![#79740e](https://placehold.co/15x15/79740e/79740e.png) `#79740e`
-   ![#b57614](https://placehold.co/15x15/b57614/b57614.png) `#b57614`
-   ![#076678](https://placehold.co/15x15/076678/076678.png) `#076678`
-   ![#8f3f71](https://placehold.co/15x15/8f3f71/8f3f71.png) `#8f3f71`
-   ![#427b58](https://placehold.co/15x15/427b58/427b58.png) `#427b58`
-   ![#af3a03](https://placehold.co/15x15/af3a03/af3a03.png) `#af3a03`

### Gruv candy

Spent some time working with Gytis on [these colors](https://projects.susielu.com/viz-palette?colors=[%22#ff241f%22,%22#79c563%22,%22#ffbb00%22,%22#b4bd00%22,%22#00929f%22,%22#ee759b%22,%22#ff7600%22,%22#b3d6c9%22]&backgroundColor=%22#ffffff%22&fontColor=%22#3c3836%22&mode=%22normal%22), so they are WIP.

-   ![#FF241F](https://placehold.co/15x15/FF241F/FF241F.png) `#FF241F`
-   ![#79C563](https://placehold.co/15x15/79C563/79C563.png) `#79C563`
-   ![#FFBB00](https://placehold.co/15x15/FFBB00/FFBB00.png) `#FFBB00`
-   ![#B4BD00](https://placehold.co/15x15/B4BD00/B4BD00.png) `#B4BD00`
-   ![#00929F](https://placehold.co/15x15/00929F/00929F.png) `#00929F`
-   ![#EE759B](https://placehold.co/15x15/EE759B/EE759B.png) `#EE759B`
-   ![#FF7600](https://placehold.co/15x15/FF7600/FF7600.png) `#FF7600`
-   ![#B3D6C9](https://placehold.co/15x15/B3D6C9/B3D6C9.png) `#B3D6C9`
