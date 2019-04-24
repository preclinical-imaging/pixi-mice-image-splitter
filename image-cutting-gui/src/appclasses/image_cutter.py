from .dependencies import *

class ImageCutter(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.__name__ = 'ImageCutter'
        self.controller = controller
        self.img_info = None
        
        # title
        title = tk.Label(self, text="Cut Image", font=controller.title_font, justify='center')


        # controls frame
        controls_frame = tk.Frame(self)

        # number of cuts made
        ncuts = len(self.controller.image.cuts)

        # add next and back buttons
        nbframe = tk.Frame(controls_frame)
        nxt = tk.Button(nbframe,text='Next',command=self.next)
        back = tk.Button(nbframe,text='Back',command=self.back)
        nxt.pack(side=tk.RIGHT,padx=(100,30),pady=(30,30))
        back.pack(side=tk.LEFT,padx=(30,100),pady=(30,30))
        nbframe.grid(row=max([ncuts+1,4]),column=0,columnspan=4,pady=(70,0))
       
        # add cut to queued cuts
        cut_controls = tk.Frame(controls_frame)
        add_cut = tk.Button(cut_controls,text='Add cut',command=self.add_cut)
        add_cut.grid(row=0,column=1,padx=(30,0))
        undo_click = tk.Button(cut_controls,text='Undo click',command=self.undo_click)
        undo_click.grid(row=0,column=0)
        if self.controller.process_made:
            reset_process = tk.Button(cut_controls,text="Reset applied cuts",command=self.reset_process)
            reset_process.grid(row=1,column=0,columnspan=2,pady=(30,15))
        cut_controls.grid(row=3,column=2)

        # rm cut frame
        rm_button_frame = None
        if ncuts:
            rm_button_frame = tk.Frame(controls_frame)
            for ix,cut in enumerate(self.controller.image.cuts):
                rmbutton = tk.Button(rm_button_frame,text='Remove cut {} ({})'.format(ix+1,cut.linecolor),command=lambda ix=ix:self.remove_cut(ix),bg=cut.linecolor)
                rmbutton.pack(side="top")
            rm_button_frame.grid(row=1,column=0,rowspan=ncuts,padx=(30,30))

        # img info
        img_info = controller.get_img_info(controls_frame)
        img_info.grid(row=0,column=0,pady=(0,50))

        # exposure controls
        exp_frame = tk.Frame(controls_frame)
        self.controller.add_exposure_controls(exp_frame)
        ec,er = 3,1
        exp_frame.grid(row=0,column=3,rowspan=4)

        # make figure
        self.make_figure()

        # grid to master frame
        title.pack(side="top", fill="x", pady=10,expand=False)
        controls_frame.pack(side="right",fill='y',expand=False,pady=30)
        self.figframe.pack(side="left",fill='both',expand=True,padx=(30,30),pady=30)

        

    def make_figure(self):
        # make figure in tkinter
        self.figframe = tk.Frame(self)
        self.figure = Figure()
        self.canvas = FigureCanvasTkAgg(self.figure, self.figframe)

        self.controller.static_cutter(figure=self.figure)

        self.controller.static_cutter_controls(canvas=self.canvas)
        self.canvas.draw()
        self.canvas_widget = self.canvas.get_tk_widget()
        
        self.canvas_widget.pack(side="top",fill='both',expand=True) 

        tbframe = tk.Frame(self.figframe)
        self.canvas._tkcanvas.pack() 
        tbframe.pack(side="top",expand=False)


    def reset(self):
        self.controller.show_frame(self.__name__)

    def back(self):
        self.controller.show_frame('ImageRotator')

    def add_cut(self):
        self.controller.add_cut()
        self.reset()

    def remove_cut(self,ix):
        self.controller.remove_cut(ix)
        self.reset()

    def undo_click(self):
        if self.controller.current_cut:
            self.controller.current_cut.pop(-1)
            self.reset()

    def reset_process(self):
        self.controller.apply_process()
        self.reset()

    def next(self):
        if self.controller.image.cuts:
            self.controller.show_frame('HeaderUI')
        else:
            print('No cuts made yet')

