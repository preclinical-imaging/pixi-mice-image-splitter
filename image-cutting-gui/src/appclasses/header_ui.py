from .dependencies import *

class HeaderUI(tk.Frame):

    def __init__(self, parent, controller):

        self.__name__ = 'HeaderUI'
        
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.controller = controller

        self.cut = self.controller.image.cuts[self.controller.cutix]

        title = tk.Label(self, text="Header Information Cut {}".format(self.controller.cutix+1), font=controller.title_font, justify='center')

        # controls frame
        controls_frame = tk.Frame(self)

        # add next and back buttons
        nbframe = tk.Frame(controls_frame)
        nxt = tk.Button(nbframe,text='Next',command=self.next)
        back = tk.Button(nbframe,text='Back',command=self.back)
        nxt.pack(side=tk.RIGHT,padx=(100,30),pady=(30,30))
        back.pack(side=tk.LEFT,padx=(30,100),pady=(30,30))
        nbframe.grid(row=4,column=0,columnspan=4,pady=(40,0))


        # img info
        img_info = controller.get_img_info(controls_frame)
        img_info.grid(row=0,column=0,pady=(0,0))

        # exposure controls
        exp_frame = tk.Frame(controls_frame)
        self.controller.add_exposure_controls(exp_frame)
        ec,er = 0,1
        exp_frame.grid(row=0,column=3,rowspan=4)

        # input header information
        self.header_frame = tk.Frame(controls_frame)
        tk.Label(self.header_frame, text='Input New Headerfile Info', font=tkfont.Font(weight=tkfont.BOLD), justify='center').grid(row=0,columnspan=2)
        self.init_entries()
        self.header_frame.grid(row=2,column=0)

        # info frame (for displaying parent image header information)
        self.info_frame = tk.Frame(controls_frame)
        self.info_string = self.get_info_string()
        tk.Label(self.info_frame, text='Original File Info', font=tkfont.Font(weight=tkfont.BOLD), justify='center').pack()
        tk.Label(self.info_frame, text=self.info_string, justify='left').pack()

        self.info_frame.grid(row=1,column=0,pady=15)



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

        self.controller.show_cut(figure=self.figure,ix=self.controller.cutix)

        self.canvas.draw()
        self.canvas_widget = self.canvas.get_tk_widget()
        
        self.canvas_widget.pack(side="top",fill='both',expand=True) 

        tbframe = tk.Frame(self.figframe)
        toolbar = NavigationToolbar2Tk(self.canvas, tbframe)
        toolbar.update()
        self.canvas._tkcanvas.pack()  
        tbframe.pack(side="top",expand=False)

        

    def next(self):
        self.update_cut()
        if self.controller.cutix == len(self.controller.image.cuts)-1:
            self.controller.show_frame('ConfirmSave')
        else:
            self.controller.cutix += 1
            self.controller.show_frame(self.__name__)

    def back(self):
        self.update_cut()
        if self.controller.cutix == 0:
            self.controller.show_frame('ImageCutter')
        else:
            self.controller.cutix -= 1
            self.controller.show_frame(self.__name__)


    def init_entries(self):

        # figure which attributes are relevant for image type
        self.hdr_attrs = ['out_filename','animal_number','subject_weight']
        if self.controller.image.type == 'ct':
            pass
        elif self.controller.image.type == 'pet':
            self.hdr_attrs += ['dose','injection_time']
        else:
            raise ValueError('Unexpected image type: {}'.format(self.controller.image.type))

        # create and place tk entries and vars for each input item
        for i,attr in enumerate(self.hdr_attrs):
            setattr(self,attr,tk.StringVar(value=''))
            entry = tk.Entry(self.header_frame,textvariable=getattr(self,attr),width=40)
            entry_attr = attr+'_entry'
            setattr(self,entry_attr,entry)
            getattr(self,entry_attr).grid(row=i+1,column=1)
            label_attr = attr+'_label'
            setattr(self,label_attr,tk.Label(self.header_frame,text=get_label(attr)))
            getattr(self,label_attr).grid(row=i+1,column=0)

        # set the entry variables according to values in the cut params (may have been updated by previous input in this program)
        for attr in self.hdr_attrs:
            if (not attr=='out_filename'):
                _ = getattr(self.cut.params,attr)
                if _ is not None:
                    getattr(self,attr).set(_)
                else:
                    getattr(self,attr).set('')

        self.out_filename.set(self.cut.out_filename)


    def get_info_string(self):
        info_string = ''
        for attr in self.hdr_attrs:
            attr_val = getattr(self.controller.image.params, attr) if attr != 'out_filename' else self.controller.image.filename
            label = get_label(attr) if attr != 'out_filename' else 'Filename'
            info_string += "{} :  {}\n".format(label, attr_val)
        return info_string

    def update_cut(self):
        for attr in self.hdr_attrs:
            entry_attr = attr+'_entry'
            entry = getattr(self,entry_attr)
            val = entry.get().strip()
            if attr=='out_filename':
                self.cut.out_filename = val
            else:
                setattr(self.cut.params, attr, val)


