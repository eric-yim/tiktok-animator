### Overview
A python tool for creating 2-D animations from sequences of images.

### Installation
Requires python3. Created on Ubuntu.
```
pip3 install opencv-python
pip3 install omegaconf
pip3 install matplotlib
```
### Constructing an animation
```
python3 builder.py --out_name MY_PROJECT
```
The main image is displayed on top axis. The newly added layers will be displayed on the bottom axis.
#### Add Layer (add an image directory)
1. Specify name of image directory
1. LeftClick on lower image to specify a center
1. LeftClick on main image to specify a target location
1. Scroll while hovering over main image to change the size of the imported layer
1. RightClick on a location on the bottom image to specify a color for chroma key
1. MiddleClick to save newly added layer
#### Edit Layer
1. Specify which existing layer
1. Controls are the same as Add Layer
#### Add Camera
1. LeftClick to start a rectangle (Top left, first)
1. Release LeftClick to end a rectangle  (Release at bottom right)
#### Change Frame
1. Enter frame number to add layers/camera to

### Animating
```
python3 render.py --out_name MY_PROJECT
```
This will render the animation specified during the construction phase. The builder phase specifies key frames, and in between frames are interpolated key frames.




