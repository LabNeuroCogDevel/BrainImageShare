# Brain Image Share
A python3 library/script to create a sharable jpeg out of a nifti image with a contact template overlay.

![screeshot](screenshot.png)

## Install and run

```
# install
python3 -m pip install git+http://github.com/LabNeuroCogDevel/BrainImageShare --user

# run
python3 -m brainimageshare
# OR if e.g. ~/.local/bin is in $PATH (see ~/.bashrc or ~/.profile)
brainimageshare 
```

Debian note: pil does not include imagetk; `apt install python3-pil.imagetk`

## Modifying contact template

`gimp` layered image `overlay.xcf` is exported to `brainimageshare/templates/overlay.png`.

To change or add images
 - clone the code
 - modify and save overlay.png
 - (re)install the module

```
git clone http://github.com/LabNeuroCogDevel/BrainImageShare
cd BrainImageShare.py
gimp overlay.xcf # save to brainimageshare/templates/overlay.png
pip3 install -e .
```
