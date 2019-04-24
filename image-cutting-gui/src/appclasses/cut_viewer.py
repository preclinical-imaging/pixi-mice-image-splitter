from .dependencies import *

"""
 THIS CLASS IS DEPRECATED
"""

class CutViewer(tk.Frame):

    def __init__(self, parent, controller):

        raise Exception('Deprecated!')
        
        tk.Frame.__init__(self, parent)
        self.__name__ = 'CutViewer'
        self.controller = controller
        self.view_ax = 'z'

        self.img_info = None
        

        label = tk.Label(self, text="Review", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)

        # back, next
        nbbx,nbby = 135,400
        tk.Button(self, text="Back",command=self.back).place(x=nbbx,y=nbby)
        tk.Button(self, text="Next",command=self.next).place(x=nbbx+180,y=nbby)

        # view axes
        vbx, vby = 200,220
        tk.Button(self,text="View collapsed x-axis",command=lambda:self.change_ax('x')).place(x=vbx,y=vby)
        tk.Button(self,text="View collapsed y-axis",command=lambda:self.change_ax('y')).place(x=vbx,y=vby+30)
        tk.Button(self,text="View collapsed z-axis",command=lambda:self.change_ax('z')).place(x=vbx,y=vby+60)
        
        # exposure scale
        self.escale_label = None
        self.escale_apply = None
        self.escaler = None
        self.controller.init_escaler(self)

        self.controller.init_img_info(self)
        self.controller.init_escaler(self)
        self.init_ani()
        


    def init_ani(self):
        self.animate_cuts()

    def back(self):
        if self.controller.nmice == 1:
            self.controller.show_frame('ImageRotator')
        else:
            self.controller.show_frame('ImageCutter')

    def next(self):
        self.controller.show_frame('HeaderUI')

    def animate_cuts(self):
        if self.controller.nmice == 1:
            self.controller.animate_collapse(self.controller.view_ax)
        else:
            self.controller.animate_cuts(view_ax=self.controller.view_ax)

    def change_ax(self,ax):
        self.controller.view_ax = ax
        self.animate_cuts()