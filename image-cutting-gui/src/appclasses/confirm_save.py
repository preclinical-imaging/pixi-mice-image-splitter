from .dependencies import *
from .smallscreens import YesNoPopup,SplashScreen

class ConfirmSave(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.__name__ = 'ConfirmSave'

        # title
        title = tk.Label(self, text="Confirm", font=self.controller.title_font)
        

        # display header info
        main_frame = tk.Frame(self)
        params_to_display = ['animal_number','subject_weight','out_filename']
        if self.controller.image.type == 'pet':
            params_to_display += ['injection_time','dose']
        for i, cut in enumerate(self.controller.image.cuts):
            cut_frame = tk.Frame(main_frame)
            for param in params_to_display:
                if param == 'out_filename':
                    val = cut.out_filename
                else:
                    val = getattr(cut.params,param)
                tk.Label(cut_frame,text='{0} : {1}'.format(get_label(param),val,justify='left')).pack()
            frame_col = i%2 
            frame_row = i//2
            cut_frame.grid(row=frame_row,column=frame_col,pady=(20,20),padx=(20,20))


        # add save and back buttons
        row = len(self.controller.image.cuts)//2+1
        nbframe = tk.Frame(main_frame)
        save = tk.Button(nbframe,text='Save',command=self.save)
        back = tk.Button(nbframe,text='Back',command=self.back)
        save.pack(side=tk.RIGHT,padx=(100,30),pady=(30,30))
        back.pack(side=tk.LEFT,padx=(30,100),pady=(30,30))
        nbframe.grid(row=row,column=0,columnspan=4,pady=(40,0))

        # make figure
        self.make_figure()

        # grid to master frame
        title.pack(side="top", fill="x", pady=10,expand=False)
        main_frame.pack(side="right",fill='y',expand=False,pady=30)
        self.figframe.pack(side="left",fill='both',expand=True,padx=(30,30),pady=30)

        



    def make_figure(self):

        # make figure in tkinter
        self.figframe = tk.Frame(self)
        self.figure = Figure()
        self.canvas = FigureCanvasTkAgg(self.figure, self.figframe)

        self.controller.show_confirm_figure(figure=self.figure)

        self.canvas.show()
        self.canvas_widget = self.canvas.get_tk_widget()
        
        self.canvas_widget.pack(side="top",fill='both',expand=True)

        tbframe = tk.Frame(self.figframe)
        toolbar = NavigationToolbar2TkAgg(self.canvas, tbframe)
        toolbar.update()
        self.canvas._tkcanvas.pack()  
        tbframe.pack(side="top",expand=False)


    def back(self):
        self.controller.show_frame('HeaderUI')



    def check_path(self, path):
        overwrite = [tf for tf in (path,path+'.hdr') if os.path.exists(tf)]
        if overwrite:
            ow_msg = '\n'.join(['The following files will be overwritten:']+overwrite+['Do you want to continue?'])
            ynpopup = self.controller.make_splash(SplashObj=YesNoPopup,text=ow_msg)
            yes_no = ynpopup.get_ans()
            self.controller.stop_splash(ynpopup)
            print('Returning {}'.format(yes_no))
            return yes_no
        else:
            return True




    def save(self):
        Tk().withdraw()
        save_path = askdirectory()
        if save_path:
            '''
            I think order should be preserved here.  
            That is important for the ok_save check to match which file we are saving
            '''
            not_saved = []
            new_files = [os.path.join(save_path,cut.out_filename) for cut in self.controller.image.cuts]
            for i,filepath in enumerate(new_files):
                ok_save = self.check_path(filepath)
                if ok_save:
                    savescreen = self.controller.make_splash(SplashObj=SplashScreen,text='Saving image...')
                    self.controller.image.save_cut(index=i,path=save_path)
                    self.controller.stop_splash(savescreen)
                else:
                    not_saved.append(1)

            # if any not saved, might need to revise filepath, don't reset.
            if not_saved:
                pass
            else:
                ynpopup = self.controller.make_splash(SplashObj=YesNoPopup,text="Apply same process to other image?")
                apply_to_other = ynpopup.get_ans()
                self.controller.stop_splash(ynpopup)
                if apply_to_other:
                    Tk().withdraw()
                    fpath = askopenfilename(initialdir=os.path.split(self.controller.image.filepath)[0])
                    if not fpath:
                        self.start_over()
                    else:
                        if fpath.endswith('.hdr'):
                            fpath = '.'.join(fpath.split('.')[:-1])
                        fname = ntpath.basename(fpath)
                        if is_pet(fname):
                            img = PETImage(fpath)
                            self.controller.collapse = 'sum'
                        else:
                            img = CTImage(fpath)
                            self.controller.collapse = 'max'
                        self.controller.process_other(img)
                else:
                    self.start_over()


    def start_over(self):
        self.controller.clean_up_data()
        self.controller.show_frame('ImageSelector')