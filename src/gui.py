import tkinter as tk
from tkinter import ttk
import threading
from tkinter import filedialog
from request_movie_site_data import get_letterboxd_user_ratings
from get_movie_info import load_movie_data, add_new_letterboxd_entries
import pandas as pd

HEIGHT = 600
WIDTH = 800

class App:
    
    def __init__(self):
        # data
        self.movie_data = None
        self.user_ratings = None
        self.filename = ''
        self.skip_checked_entries = True
        # instantiate and set up app
        self.ws = tk.Tk()
        self.button_font = ('Garamond', 15)
        self.load_screen = False
        self.setup_interface()
    
    
    def vague_load_screen(self):
        new, canvas = self.New_Window(height=100, width=200)
        new.title('Source Data')
        label = tk.Label(canvas, text='Loading in data...')
        label.pack()
        pb = ttk.Progressbar(
            canvas,
            orient='horizontal',
            mode='indeterminate',
            length=280
        )
        pb.pack()
        pb.start()

        new.protocol('WM_DELETE_WINDOW', lambda: new.destroy() if self.load_screen else False) # Close the window only if main window has shown up
        new.mainloop()

    def print_lb_ratings(self):
        window, canvas = self.New_Window(height=200, width=300)
        window.title('Letterboxd User Ratings')
        label = tk.Label(canvas, text='Loading in new Letterboxd entries...')
        label.pack()
        self.movie_data, missing_films = add_new_letterboxd_entries(self.movie_data, self.user_ratings)
        label1 = tk.Label(canvas, font=self.button_font, text=f"You've watched {len(missing_films)} new properties since last upload:")
        label1.pack()
        label2 = tk.Label(canvas, wraplength=500, justify='left', text=f"{', '.join([v['name'] for v in missing_films.values()])}\n")
        label2.pack()
        button = tk.Button(canvas, text='OK', padx=20, command=window.destroy)
        button.pack()

    def load_data(self, start_mode=False):
        threading.Thread(target=self.vague_load_screen)
        self.user_ratings = get_letterboxd_user_ratings("jigsaw4real")
        if start_mode:
            try:
                filename = filedialog.askopenfilename()
                self.movie_data = load_movie_data(start_mode=True, filepath=filename)
            except:
                pass
        else:
            try:
                self.movie_data = load_movie_data()
            except:
                pass
        self.load_screen = True
        
    def New_Window(self, height=HEIGHT, width=WIDTH):
        window = tk.Toplevel()
        canvas = tk.Canvas(window, height=height, width=width)
        canvas.pack()
        return window, canvas

    def add_main_menu(self, canvas):
        # creating a container
        container = tk.Frame(canvas, bg='black')
        container.rowconfigure(0,)
        container.pack(side = "top", fill = "both", expand = True) 

        b1 = tk.Button(container, text="Get Latest Letterboxd Logs", bg='#40bdf5')
        b1.config(command=self.print_lb_ratings)
        b1.config(font=self.button_font, width=30)

        b2 = tk.Button(container, text="Fill Missing Data", bg='#ff7d01')
        b2.config(command=self.print_lb_ratings)
        b2.config(font=self.button_font, width=14)

        b3 = tk.Button(container, text="Fill Latest Entries", bg='#ff7d01')
        b3.config(command=self.print_lb_ratings)
        b3.config(font=self.button_font, width=14)
        
        b4 = tk.Button(container, text="Export Data", bg='#00e155')
        b4.config(command=self.print_lb_ratings)
        b4.config(font=self.button_font, width=30)

        b1.grid(column=0, row=0, columnspan=2)
        b2.grid(column=0, row=1, sticky='W')
        b3.grid(column=1, row=1, sticky='e')
        b4.grid(column=0, row=2, columnspan=2)
        
    def setup_interface(self):
        
        icon = tk.PhotoImage(file="assets\cinefiles_icon.png")
        self.ws.iconphoto(True, icon)
        
        self.ws.config(background="black")
        self.ws.title("CineFiles")
        
        canvas = tk.Canvas(self.ws, height=HEIGHT, width=WIDTH)
        canvas.config(bg='black', highlightbackground='black')
        canvas.pack()

        label_title = tk.Label(canvas, 
            text="CineFiles", 
            font=("Cooper Black", 40, 'bold'), 
            fg="red", 
            bg="black",
            image=icon, 
            compound='top',
            pady=15)
        label_title.pack()

        # creating a container
        container = tk.Frame(canvas, bg='black')
        container.pack(side = "top", fill = "both", expand = True) 

        label1 = tk.Label(
            container, padx=15, fg='white', bg='black', 
            text='Select data source:', font=(self.button_font[0], self.button_font[1], 'bold'))
        label1.pack()

        b1 = tk.Button(container, text="Upload Excel File 📁", bg='#A3CFA4')
        t = threading.Thread(target=self.load_data)
        b1.config(command=lambda: [self.load_data(), self.add_main_menu(canvas)])
        b1.config(font=self.button_font, width=30)
        b1.pack()

        b2 = tk.Button(container, text="Load from Save File 💾", bg='#FFF3BD')
        b2.config(command=lambda: [self.load_data(), self.add_main_menu(canvas)])
        b2.config(font=self.button_font, width=30)
        b2.pack()

        label2 = tk.Label(padx=15, fg='black', bg='black')
        label2.pack()

        self.ws.mainloop()

if __name__ == "__main__":
    app = App()