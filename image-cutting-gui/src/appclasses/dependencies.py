import os, sys
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import math
import ntpath
import atexit
import gc
import tkinter as tk
import tempfile
import traceback
import inspect
import shutil
import numpy as np
from tkinter import Tk
from collections import defaultdict                
from tkinter import font  as tkfont 
from tkinter.filedialog import askopenfilename, askdirectory
from ..imgclasses.baseimage import PETImage, CTImage, SubImage
from ..imgclasses.imageviewer import ImageEditor

TEMPLOG = 'templog.txt'

# functions

def stack_report(page_name):
    print("stack size: {}".format(len(traceback.extract_stack())))
    tb = '\n'.join([str(r) for r in traceback.extract_stack()])
    txt = '\n'.join([
        '\n','\n','#'*50,
        'Showing frame: {}'.format(page_name),'\n'
        ])
    txt += tb
    with open('stack_report.txt','a') as myf:
        myf.write(txt)

def check_memmap(data):
    refs = gc.get_referrers(*[data])
    print("{} referrers: [{}]".format(len(refs),' ,'.join([str(type(r)) for r in refs])))
    for r in refs:
        if type(r) is type(sys._getframe()):
            print('FRAME: {}'.format(inspect.getframeinfo(r)))

def get_label(attr_name):
    if attr_name == 'dose':
        return 'Injection Dose'
    elif attr_name == 'injection_time':
        return 'Injection Datetime'
    else:
        return attr_name.replace('_',' ').title()


def is_pet(fname):
    if 'pet' in fname and '.ct' not in fname and fname.endswith('.img'):
        return True
    else:
        return False

def clean_temp_dirs():
    if os.path.exists(TEMPLOG):
        with open(TEMPLOG,'r') as tlog:
            tlog_txt = tlog.read()
        tdirs = list(set([d for d in tlog_txt.split('\n') if d]))
        for d in tdirs:
            try:
                shutil.rmtree(d)
                print('Removed tempdir: {}'.format(d))
                tdirs.remove(d)
            except Exception as e:
                if not os.path.exists(d):
                    tdirs.remove(d)
                else:
                    print('Failed to remove tempdir: {0}\n{1}'.format(d,e))
        with open(TEMPLOG,'w') as tlog:
            tlog.write('\n'.join(tdirs))

def stop_app():
    global app
    for frame in app.frames.values():
        frame.destroy()
    app.destroy()

def log_temp_dir(directory):
    if os.path.exists(TEMPLOG):
        ap_wr = 'a'
    else:
        ap_wr = 'w'

    tlog = open(TEMPLOG, ap_wr)
    tlog.write('\n{}'.format(directory))
    tlog.close()


def exit_fn(app):
    if app.image is not None:
        for i,cut in enumerate(app.image.cuts):
            del cut.img_data
        del app.image.img_data
    app.destroy()
    del app
    gc.collect()
    clean_temp_dirs()
    sys.exit(0)


def print_error(e):
    exc_info = sys.exc_info()
    exc_type, exc_obj, exc_tb = exc_info
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    traceback.print_exception(*exc_info)
    print('{}\n'.format(e),exc_type, fname, exc_tb.tb_lineno)
    
