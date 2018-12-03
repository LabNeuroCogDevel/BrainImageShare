#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfile
from PIL import Image, ImageEnhance, ImageTk
import numpy as np
import nibabel as nib
import sys # for exit


# ### jpeg background image
background = Image.open('top_only.png')

# -- functions
def ni_to_img(ni_mat, i=None, j=None, k=None):
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
    pil_img = Image.fromarray(img3*(256/np.max(img3)))
    #pil_img.show()
    return(pil_img)


# -- GUI
class BrainImage(tk.Frame):
    def mk_scale(self, lim):
        s = tk.Scale(self.bframe,from_=0, to=lim-1)
        s.set(lim//2)
        s.bind("<ButtonRelease-1>", self.update_image)
        s.pack(side="left")
        return(s)

    def __init__(self, t1_file="mprage.nii.gz", master=None):

        # ### brain image
        ni  = nib.load(t1_file)
        # nib.aff2axcodes(ni.affine) # RAS -- always? is LPI outside of nipy
        # http://nipy.org/nibabel/coordinate_systems.html
        self.ni_mat = ni.get_fdata()

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
        self.b_reset.pack(side="bottom")
        # save
        self.b_save = tk.Button(self.bframe,text="save",command=self.save)
        self.b_save.pack(side="bottom")
        # rerender
        self.b_rend = tk.Button(self.bframe,text="force-render",
                                command=lambda: self.update_image(None))
        self.b_rend.pack(side="bottom")

        # -- the image
        self.full_img = background
        self.full_img_tk = ImageTk.PhotoImage(self.full_img)
        self.img_disp = tk.Label(image=self.full_img_tk)
        self.img_disp.image = self.full_img_tk

        # button organization
        self.bframe.pack(side="top")
        self.img_disp.pack(side="bottom", fill="both", expand="yes")

        # image. hold on for later


    def reset(self):
        self.scale_i.set(self.ni_mat.shape[0]//2)
        self.scale_j.set(self.ni_mat.shape[1]//2)
        self.scale_k.set(self.ni_mat.shape[2]//2)
        self.update_image(None)


    def save(self):
        f = asksaveasfile(mode='w', defaultextension=".jpg")
        if f is None:
            return
        self.full_img.save(f)
        

    def update_image(self,e):
        nii_jpg = ni_to_img(self.ni_mat,
                            self.scale_i.get(),
                            self.scale_j.get(),
                            self.scale_k.get())
        # center nii in top
        # TODO: if w_offset is negative?
        w_offset = (background.size[0] - nii_jpg.size[0])//2
        h_offset = background.size[1]

        # total size: max of widths, sum of heights
        total_size = (max(background.size[0],nii_jpg.size[0]),
                      background.size[1]+nii_jpg.size[1])

        # combine images
        self.full_img = Image.new("RGBA", total_size)
        self.full_img.paste(background,(0,0))
        self.full_img.paste(nii_jpg.convert("RGBA"),(w_offset,h_offset))
        self.full_img = self.full_img.convert("RGB") # remove alpha
        # self.full_img.show()

        self.full_img_tk = ImageTk.PhotoImage(self.full_img)
        self.img_disp.configure(image=self.full_img_tk)
        self.img_disp.image = self.full_img_tk


# -- start TK
root = tk.Tk()
root.title("LNCD Brain Image Creator")

# get mprage
root.update()
t1_file = askopenfilename(
    defaultextension=".nii.gz",
    title="select subject mprage.nii.gz")
root.update()
if not t1_file:
    sys.exit(1)

app = BrainImage(t1_file=t1_file,master=root)
root.bind("<Return>", app.update_image)
app.mainloop()
