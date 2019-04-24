from .dependencies import *

class SplashScreen(tk.Toplevel):
    def __init__(self, parent, text):
        self.__name__ = 'LoadScreen'
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        w = 530 # width for the Tk root
        h = 250 # height for the Tk root

        # get screen width and height
        ws = self.winfo_screenwidth() # width of the screen
        hs = self.winfo_screenheight() # height of the screen

        # calculate x and y coordinates for the Tk root window
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)

        # set the dimensions of the screen 
        # and where it is placed
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.title("Image Preprocessing")

        # size buttons
        label = tk.Label(self, text=text, font=tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic"))
        label.pack(side="top", fill="x", pady=10)

        ## required to make window show before the program gets to the mainloop
        self.update()


class YesNoPopup(tk.Toplevel):
    def __init__(self, parent, text):
        self.__name__ = 'LoadScreen'
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        w = 530 # width for the Tk root
        h = 250 # height for the Tk root

        # get screen width and height
        ws = self.winfo_screenwidth() # width of the screen
        hs = self.winfo_screenheight() # height of the screen

        # calculate x and y coordinates for the Tk root window
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)

        # set the dimensions of the screen 
        # and where it is placed
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.title("Image Preprocessing")

        # text
        label = tk.Label(self, text=text, font=tkfont.Font(family='Helvetica', size=10))
        label.pack(side="top", fill="x", pady=10)

        # yes/no buttons
        self.ans = tk.BooleanVar()
        self.yes = tk.Button(self, text='Yes', command=lambda:self.ans.set(True))
        self.yes.pack(side="right", pady=10, padx=(0,100))
        self.no = tk.Button(self, text='No', command=lambda:self.ans.set(False))
        self.no.pack(side="left", pady=10, padx=(100,0))


        ## required to make window show before the program gets to the mainloop
        self.update()


    def get_ans(self):
        self.yes.wait_variable(self.ans)
        return self.ans.get()
