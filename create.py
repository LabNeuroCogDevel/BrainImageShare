#!/usr/bin/env python3
# -*- coding: utf-8 -*-


#
# optimize share image for facebook cover
# 820x312 (computer) 640x360 (mobile)
# https://www.facebook.com/help/125379114252045

import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfile
from PIL import Image, ImageEnhance, ImageTk
import numpy as np
import nibabel as nib
import sys # for exit


# ### jpeg background image

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
    adjusted = img3*(256/np.max(img3))
    # adjusted[adjusted>255] = 0 # kill high values, bad idea
    pil_img = Image.fromarray(adjusted)
    #pil_img.show()
    return(pil_img)


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
        self.lncd_template = Image.open('overlay.png')

        # ### brain image
        ni  = nib.load(t1_file)
        # nib.aff2axcodes(ni.affine) # RAS -- always? is LPI outside of nipy
        # http://nipy.org/nibabel/coordinate_systems.html
        self.ni_mat = ni.get_fdata()

        # default nii image settings
        self.default = {'height': 50, 'scale': 1.2}

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
        nii_jpg = ni_to_img(self.ni_mat,
                            self.scale_i.get(),
                            self.scale_j.get(),
                            self.scale_k.get())
        ratio = float(self.scale_s.get())
        if ratio != 1.0:
            new_res = [ int(x * ratio) for x in nii_jpg.size]
            nii_jpg = nii_jpg.resize(new_res)
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
        w_offset = (self.lncd_template.size[0] - nii_jpg.size[0])//2
        # todo change based on what image?
        h_offset = self.scale_ho.get() # 130
        total_size = self.lncd_template.size

        self.full_img = Image.new("RGBA", total_size)
        self.full_img.paste(nii_jpg.convert("RGBA"),(w_offset,h_offset))
        self.full_img.paste(self.lncd_template,(0,0),self.lncd_template)
        self.full_img = self.full_img.convert("RGB") # replace alpha w/black

    def update_image_stack(self,e):
        nii_jpg = self.nii_to_jpg()
        # center nii in top
        # TODO: if w_offset is negative?
        w_offset = (self.lncd_template.size[0] - nii_jpg.size[0])//2
        h_offset = self.lncd_template.size[1]

        # total size: max of widths, sum of heights
        total_size = (max(self.lncd_template.size[0],nii_jpg.size[0]),
                      self.lncd_template.size[1]+nii_jpg.size[1])

        # combine images
        self.full_img = Image.new("RGBA", total_size)
        self.full_img.paste(self.lncd_template,(0,0))
        self.full_img.paste(nii_jpg.convert("RGBA"),(w_offset,h_offset))
        self.full_img = self.full_img.convert("RGB") # remove alpha
        # self.full_img.show()


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
