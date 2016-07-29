nlzss taken from https://github.com/magical/nlzss

article [here](https://medium.com/@mmmulani/creating-a-game-size-world-map-of-pok%C3%A9mon-fire-red-614da729476a#.1ruzb9nwl)

# Installing pygame

`pygame` is annoying to install for Python 3.
The easiest way to do it is to actually build from source:

(Taken from http://www.pygame.org/wiki/CompileUbuntu)
```
# install dependencies
sudo apt-get install mercurial python3-dev python3-numpy python3-opengl \
    libav-tools libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsmpeg-dev \
    libsdl1.2-dev libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev \
    libtiff5-dev libx11-6 libx11-dev fluid-soundfont-gm timgm6mb-soundfont \
    xfonts-base xfonts-100dpi xfonts-75dpi xfonts-cyrillic fontconfig fonts-freefont-ttf
 
# Grab source
hg clone https://bitbucket.org/pygame/pygame
 
# Finally build and install
cd pygame
python3 setup.py build
sudo python3 setup.py install
 
# Run some tests
python3 -m pygame.tests
python3 -m pygame.examples/aacircle
python3 -m pygame.examples/aliens
python3 -m pygame.examples/freetype_misc
python3 -m pygame.examples/glcube
python3 -m pygame.examples/sound
python3 -m pygame.examples/stars
```

