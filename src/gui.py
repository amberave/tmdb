import tkinter as tk
from tkinter import ttk
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
        self.setup_interface()

    def print_lb_ratings(self):
        window, canvas = self.New_Window(height=200, width=300)
        window.title('Letterboxd User Ratings')
        label = tk.Label(canvas, text='Loading in new Letterboxd entries...')
        label.pack()
        pb = ttk.Progressbar(
            canvas,
            orient='horizontal',
            mode='indeterminate',
            length=280
        )
        pb.pack()
        pb.start()
        print(5)
        self.movie_data, missing_films = window.after_idle(add_new_letterboxd_entries(self.movie_data, self.user_ratings))
        # pb.destroy()
        label.config(text=f"You've watched {len(missing_films)} new properties since last upload: {', '.join([v['name'] for v in missing_films.values()])}\n")
        # label.pack()
        # window.mainloop()

    def load_data(self, container, start_mode=False):
        window, canvas = self.New_Window(height=100, width=200)
        window.title('Source Data')
        label = tk.Label(canvas, text='Loading in data...')
        label.pack()
        
        self.user_ratings = get_letterboxd_user_ratings("DWynter10")
        def inner_func():
            if start_mode:
                try:
                    filename = filedialog.askopenfilename()
                    self.movie_data = load_movie_data(start_mode=True, filepath=filename)
                    container.destroy()
                except:
                    pass
                window.destroy()
            else:
                try:
                    self.movie_data = load_movie_data()
                    container.destroy()
                except:
                    pass
                print('Hello')
                window.destroy()
        
        window.after(0, inner_func)
        window.mainloop()

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
        b1.config(command=lambda: [self.load_data(container, start_mode=True), self.add_main_menu(canvas)])
        b1.config(font=self.button_font, width=30)
        b1.pack()

        b2 = tk.Button(container, text="Load from Save File 💾", bg='#FFF3BD')
        b2.config(command=lambda: [self.load_data(container), self.add_main_menu(canvas)])
        b2.config(font=self.button_font, width=30)
        b2.pack()

        label2 = tk.Label(padx=15, fg='black', bg='black')
        label2.pack()

        self.ws.mainloop()

if __name__ == "__main__":
    app = App()