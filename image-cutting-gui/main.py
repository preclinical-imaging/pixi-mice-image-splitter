from src.appclasses.image_gui import *

if __name__ == "__main__":
    gc.collect()
    clean_temp_dirs()
    data_folder = os.path.join('data','pcds')
    while True:
        app = ImageGUI(folder=data_folder)
        app.protocol("WM_DELETE_WINDOW", lambda app=app:exit_fn(app))
        app.mainloop()