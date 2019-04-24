from .dependencies import *
from .smallscreens import YesNoPopup

class ImageRotator(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.__name__ = 'ImageRotator'
        self.controller = controller
        self.img_info = None
        
        # title
        title = tk.Label(self, text="Rotate Image", font=controller.title_font, justify='center')

        # controls frame
        controls_frame = tk.Frame(self)

        # add next and back buttons
        nbframe = tk.Frame(controls_frame)
        nxt = tk.Button(nbframe,text='Next',command=self.next_page)
        back = tk.Button(nbframe,text='Back',command=self.back)
        nxt.pack(side=tk.RIGHT,padx=(100,30),pady=(30,30))
        back.pack(side=tk.LEFT,padx=(30,100),pady=(30,30))
        nbframe.grid(row=4,column=0,columnspan=4,pady=(40,0))


        # img info
        img_info = controller.get_img_info(controls_frame)
        img_info.grid(row=0,column=0,pady=(0,50))

        # exposure controls
        exp_frame = tk.Frame(controls_frame)
        self.controller.add_exposure_controls(exp_frame)
        ec,er = 3,1
        exp_frame.grid(row=0,column=3,rowspan=4)

        # rotation buttons
        rbr,rbc = 1,1 # rotbx,rotby = 200,220
        tk.Button(controls_frame, text="Rotate on x axis", command=lambda : self.rotate_on_axis('x')).grid(row=rbr,column=rbc,pady=(5,5))
        tk.Button(controls_frame, text="Rotate on y axis", command=lambda : self.rotate_on_axis('y')).grid(row=rbr+1,column=rbc,pady=(5,5))
        tk.Button(controls_frame, text="Rotate on z axis", command=lambda : self.rotate_on_axis('z')).grid(row=rbr+2,column=rbc,pady=(5,5))
        
        # make figure
        self.make_figure()

        # grid to master frame
        title.pack(side="top", fill="x", pady=10,expand=False)
        controls_frame.pack(side="right",fill='y',expand=False,pady=100)
        self.figframe.pack(side="left",fill='both',expand=True,padx=(30,30),pady=30)

        

    def make_figure(self):
        # make figure in tkinter
        self.figframe = tk.Frame(self)
        self.figure = Figure()
        self.canvas = FigureCanvasTkAgg(self.figure, self.figframe)

        self.controller.view_each_axis(figure=self.figure)

        self.canvas.show()
        self.canvas_widget = self.canvas.get_tk_widget()
        
        self.canvas_widget.pack(side="top",fill='both',expand=True) 

        tbframe = tk.Frame(self.figframe)
        toolbar = NavigationToolbar2TkAgg(self.canvas, tbframe)
        toolbar.update()
        self.canvas._tkcanvas.pack()  
        tbframe.pack(side="top",expand=False)



    def back(self):
        self.controller.show_frame('ImageSelector')


    def rotate_on_axis(self,ax):
        self.controller.image.clean_cuts()
        self.controller.image.rotate_on_axis(ax,log=True)
        self.controller.show_frame(self.__name__)

    def next_page(self):
        self.controller.show_frame('ImageCutter')

