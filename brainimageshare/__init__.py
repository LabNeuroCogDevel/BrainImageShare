#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# USAGE:
#  ./BrainImageShare.py mprage.nii.gz output.jpeg
#  ./BrainImageShare.py # interactive
#

#
# optimize share image for facebook cover
# 820x312 (computer) 640x360 (mobile)
# https://www.facebook.com/help/125379114252045

import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfile
from PIL import Image, ImageEnhance, ImageTk
import numpy as np
import nibabel as nib
import sys
import os.path


# ### jpeg background image
def overlay_defaults():
        return({'height': 50, 'scale': 1.2})


def overlay_image():
    pkgdir = os.path.dirname(__file__)
    img_path = os.path.join(pkgdir, "templates", "overlay.png")
    return(img_path)


# -- functions
def ni_to_img(ni_mat, i=None, j=None, k=None, ratio=1):
    """
    make a PIL image from a nifti
    opitonally given an i j k slice (otherwise middle)
    """
    if i is None: i=int(ni_mat.shape[0]/2)
    if j is None: j=int(ni_mat.shape[1]/2)
    if k is None: k=int(ni_mat.shape[2]/2)
    ni, nj, nk = ni_mat.shape
    s = max(ni_mat.shape)
    axl = np.zeros([s,s])
    sag = np.zeros([s,s])
    cor = np.zeros([s,s])

    sag[0:nj,0:nk] = np.squeeze(ni_mat[i, :, :])
    cor[0:ni,0:nk] = np.squeeze(ni_mat[:, j, :])
    axl[0:ni,0:nj] = np.squeeze(ni_mat[:, :, k])

    # sag is special
    sag = np.fliplr(np.rot90(sag,2))
    # plt.imshow(sag); plt.show()
    
    rot = [np.rot90(x) for x in [axl, sag, cor]]
    img3 = np.concatenate(rot ,axis=1)
    # plt.imshow(img3); plt.show()
    # get image -- gray goes from 1 to 256
    adjusted = img3*(256/np.max(img3))
    # adjusted[adjusted>255] = 0 # kill high values, bad idea
    pil_img = Image.fromarray(adjusted)

    if ratio != 1.0:
        new_res = [ int(x * ratio) for x in pil_img.size]
        pil_img = pil_img.resize(new_res)
    #pil_img.show()
    return(pil_img)

def mk_image_overlay(nii_jpg, lncd_template, h_offset):
    w_offset = (lncd_template.size[0] - nii_jpg.size[0])//2
    total_size = lncd_template.size

    full_img = Image.new("RGBA", total_size)
    full_img.paste(nii_jpg.convert("RGBA"),(w_offset,h_offset))
    full_img.paste(lncd_template,(0,0),lncd_template)
    full_img = full_img.convert("RGB") # replace alpha w/black
    return(full_img)

def mk_image_stack(nii_jpg, lncd_template):
    # center nii in top
    # TODO: if w_offset is negative? -- leave it up to scaling?
    w_offset = (lncd_template.size[0] - nii_jpg.size[0])//2
    h_offset = lncd_template.size[1]

    # total size: max of widths, sum of heights
    total_size = (max(lncd_template.size[0],nii_jpg.size[0]),
                  lncd_template.size[1]+nii_jpg.size[1])

    # combine images
    full_img = Image.new("RGBA", total_size)
    full_img.paste(lncd_template,(0,0))
    full_img.paste(nii_jpg.convert("RGBA"),(w_offset,h_offset))
    full_img = full_img.convert("RGB") # remove alpha
    # self.full_img.show()
    return(full_img)


def mk_image(mprage_file, output_file):
    if os.path.isfile(output_file):
        print("already have output. To continue:\n\trm %s"%output_file)
        return()
    # load settings, mprage, and overlay image
    settings = overlay_defaults()
    lncd_template = Image.open(overlay_image())
    ni  = nib.load(t1_file)
    # how to put the images together
    ni_mat = ni.get_fdata()
    middle = [ x//2 for x in ni_mat.shape ]
    nii_jpg = ni_to_img(ni_mat, *middle, settings['scale'])
    # do it
    full_img = mk_image_overlay(nii_jpg, lncd_template, settings['height'])
    full_img.save(output_file)

# -- GUI
class BrainImage(tk.Frame):
    def mk_scale(self, lim, side="left"):
        s = tk.Scale(self.bframe,from_=0, to=lim-1,orient="horizontal")
        s.set(lim//2)
        s.bind("<ButtonRelease-1>", self.update_image)
        #s.pack(side=side)
        return(s)

    def __init__(self, t1_file="mprage.nii.gz", master=None):

        # ### template image

        #lncd_template = Image.open('top_only.png')
        self.lncd_template = Image.open(overlay_image())

        # ### brain image
        ni  = nib.load(t1_file)
        # nib.aff2axcodes(ni.affine) # RAS -- always? is LPI outside of nipy
        # http://nipy.org/nibabel/coordinate_systems.html
        self.ni_mat = ni.get_fdata()

        # default nii image settings
        self.default = overlay_defaults()

        tk.Frame.__init__(self,master)
        # -- interface
        self.bframe = tk.Frame()

        # slice position
        self.scale_k = self.mk_scale(self.ni_mat.shape[2]) # ax
        self.scale_i = self.mk_scale(self.ni_mat.shape[0]) # sag(NB out of place)
        self.scale_j = self.mk_scale(self.ni_mat.shape[1]) # cor
        # - buttons
        # reset
        self.b_reset = tk.Button(self.bframe,text="reset",command=self.reset)
        # save
        self.b_save = tk.Button(self.bframe,text="save",command=self.save)
        # rerender
        self.b_rend = tk.Button(self.bframe,text="force-render",
                                command=lambda: self.update_image(None))

        # -- image display settings
        # height offset 
        self.scale_ho = self.mk_scale(260) 
        self.scale_ho.configure(orient="vertical")
        self.scale_ho.set(self.default['height'])
        # image scaling
        self.scale_s = self.mk_scale(3) 
        self.scale_s.configure(resolution=0.1)
        self.scale_s.set(self.default['scale'])

        # -- the image
        self.full_img = self.lncd_template
        self.full_img_tk = ImageTk.PhotoImage(self.full_img)
        self.img_disp = tk.Label(image=self.full_img_tk)
        self.img_disp.image = self.full_img_tk

        # -- configure display
        self.scale_k.grid( row=0,column=0)
        self.scale_j.grid( row=1,column=0)
        self.scale_i.grid( row=2,column=0)
        self.scale_ho.grid(row=0,column=1,rowspan=2)
        self.scale_s.grid( row=2,column=1)
        self.b_reset.grid( row=0,column=2)
        self.b_save.grid(  row=1,column=2)
        self.b_rend.grid(  row=2,column=2)

        # button organization
        self.bframe.pack(side="top")
        self.img_disp.pack(side="bottom", fill="both", expand="yes")

        # update image display
        self.update_image(None)

        # -- bindings
        master.bind("<Return>", lambda x: self.save())
        master.bind("i",lambda x: self.mv_scale(self.scale_i, 1))
        master.bind("I",lambda x: self.mv_scale(self.scale_i, -1))
        master.bind("j",lambda x: self.mv_scale(self.scale_j, 1))
        master.bind("J",lambda x: self.mv_scale(self.scale_j, -1))
        master.bind("k",lambda x: self.mv_scale(self.scale_k, 1))
        master.bind("K",lambda x: self.mv_scale(self.scale_k, -1))
        master.bind("s",lambda x: self.mv_scale(self.scale_s, 1))
        master.bind("S",lambda x: self.mv_scale(self.scale_s, -1))
        master.bind("h",lambda x: self.mv_scale(self.scale_ho, 1))
        master.bind("h",lambda x: self.mv_scale(self.scale_ho, -1))
        master.bind("<Down>",lambda x: self.mv_scale(self.scale_ho, 1))
        master.bind("<Up>",lambda x: self.mv_scale(self.scale_ho, -1))
        master.bind("<Right>",lambda x: self.mv_scale(self.scale_s, 1))
        master.bind("<Left>",lambda x: self.mv_scale(self.scale_s, -1))


    def mv_scale(self,scale,inc):
        """
        move a scale slider by its resolution
        """
        res = scale.configure()['resolution'][4]
        val = float(scale.get())
        scale.set(val+(res*inc))
        self.update_image(None)

    def reset(self):
        self.scale_i.set(self.ni_mat.shape[0]//2)
        self.scale_j.set(self.ni_mat.shape[1]//2)
        self.scale_k.set(self.ni_mat.shape[2]//2)
        self.scale_ho.set(self.default['height'])
        self.scale_s.set(self.default['scale'])
        self.update_image(None)


    def save(self):
        f = asksaveasfile(mode='w', defaultextension=".jpg")
        if f is None:
            return
        self.full_img.save(f)
        

    def nii_to_jpg(self):
        ratio = float(self.scale_s.get())
        nii_jpg = ni_to_img(self.ni_mat,
                            self.scale_i.get(),
                            self.scale_j.get(),
                            self.scale_k.get(),
                            ratio)
        return(nii_jpg)


    def update_image(self,e):
        """ warpper: which update function to use """
        self.update_image_overlay(e)

        # update display
        self.full_img_tk = ImageTk.PhotoImage(self.full_img)
        self.img_disp.configure(image=self.full_img_tk)
        self.img_disp.image = self.full_img_tk

        
    def update_image_overlay(self,e):
        nii_jpg = self.nii_to_jpg()
        # todo change based on what image?
        h_offset = self.scale_ho.get() # 130
        self.full_img = mk_image_overlay(nii_jpg,
                                         self.lncd_template,
                                         h_offset)

    def update_image_stack(self,e):
        nii_jpg = self.nii_to_jpg()
        self.full_img = mk_image_stack(nii_jpg, self.lncd_template)


def brainimageshare():
    root = tk.Tk()
    root.title("LNCD Brain Image Creator")

    # get mprage
    if len(sys.argv) > 1:
        t1_file = sys.argv[1]
    else:
        root.update()
        t1_file = askopenfilename(
            defaultextension=".nii.gz",
            title="select subject mprage.nii.gz")
        root.update()

    # no gui if given input and output
    if len(sys.argv) == 3:
        save_as = sys.argv[2]
        mk_image(t1_file, save_as)
        sys.exit(0)

    # make sure it's at least a file, nibabel will error if not nii.gz
    if not t1_file or not os.path.isfile(t1_file):
        print("bad or no mprage give or selected!")
        sys.exit(1)

    app = BrainImage(t1_file=t1_file, master=root)
    app.mainloop()


# if not loading as a module
# launch gui if given no args or just an mprage
# if given both input mprage and output, just write the file
if __name__ == "__main__":
    brainimageshare()
