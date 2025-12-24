import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import pandas as pd

from request_movie_site_data import get_letterboxd_user_ratings, setup_apis
from get_movie_info import get_movie_info, load_movie_data, add_new_letterboxd_entries, save_progress

HEIGHT = 600
WIDTH = 800

class App:

    def __init__(self):
        self.movie_data = None
        self.user_ratings = None
        self.errors = set()
        self.filename = None

        self.ws = tk.Tk()
        self.button_font = ('Garamond', 15)
        self.icon = tk.PhotoImage(file=r"assets\cinefiles_icon.png")
        self.ws.iconphoto(True, self.icon)

        self.setup_interface()
        self.ws.mainloop()

    # -------------------- LOADING WINDOW --------------------

    def show_loading_screen(self, text="Loading..."):
        self.loading_window = tk.Toplevel(self.ws)
        self.loading_window.title("Loading")
        self.loading_window.geometry("300x150")
        self.loading_window.transient(self.ws)
        self.loading_window.grab_set()

        label = tk.Label(self.loading_window, text=text)
        label.pack(pady=10)

        self.pb = ttk.Progressbar(
            self.loading_window,
            orient='horizontal',
            mode='indeterminate',
            length=200
        )
        self.pb.pack(pady=10)
        self.pb.start()
    
    def close_loading_screen(self):
        if hasattr(self, "loading_window"):
            self.loading_window.destroy()
    
    def show_progress_screen(self, text="Retrieving movie data..."):
        self.progress_window = tk.Toplevel(self.ws)
        self.progress_window.title("Loading")
        self.progress_window.geometry("300x150")
        self.progress_window.transient(self.ws)
        self.progress_window.grab_set()

        label = tk.Label(self.progress_window, text=text)
        label.pack(pady=10)

        self.pb_pc = ttk.Progressbar(
            self.progress_window,
            orient='horizontal',
            mode='determinate',
            length=200,
            maximum=100
        )
        self.pb_pc.pack(pady=20)

        self.progress_label = tk.Label(self.progress_window, text=f"0/{len(self.movie_data)}\n(0%)")
        self.progress_label.pack()

    def close_progress_screen(self):
        if hasattr(self, "progress_window"):
            self.progress_window.destroy()

    def update_progress(self, current_num, num_entries):
        progress = round((current_num / num_entries) * 100, 2)
        self.pb_pc["value"] = progress
        self.progress_label.config(text=f"{current_num}/{num_entries}\n({progress}%)")

    # -------------------- DATA LOADING --------------------

    def load_data(self, start_mode=False):
        self.show_loading_screen()
        threading.Thread(
            target=self.load_data_thread,
            args=(start_mode,),
            daemon=True
        ).start()

    def load_data_thread(self, start_mode=False, letterboxd_username="jigsaw4real"):
        try:
            self.user_ratings = get_letterboxd_user_ratings(letterboxd_username)

            if start_mode:
                filename = filedialog.askopenfilename()
                if filename:
                    self.movie_data, self.filename = load_movie_data(start_mode=True, filepath=filename)
            else:
                self.movie_data, self.filename = load_movie_data()

        except Exception as e:
            print("Error loading data:", e)

        self.ws.after(0, self.finish_loading)

    def finish_loading(self):
        self.close_loading_screen()
        if self.first_time:
            self.first_time = False
            self.add_main_menu(self.main_canvas)
    
    # -------------------- DATA EXPORTING --------------------

    def export_data(self):
        self.show_loading_screen("Exporting data...")
        threading.Thread(
            target=self.export_data_thread,
            daemon=True
        ).start()
    
    def export_data_thread(self):
        save_progress(self.filename, "output/output-", self.movie_data, self.errors)
        output_df = pd.DataFrame(self.movie_data)
        
        output_filename = "output/output-" + self.filename
        output_df.to_excel(output_filename, index=False)

        self.ws.after(0, self.finish_exporting)
    
    def finish_exporting(self):
        self.pb.destroy()
        label = tk.Label(self.loading_window, text=f"Data exported to 'output-{self.filename}")
        label.pack(pady=10)
        os.system("start output\\")

    # -------------------- RETRIEVE MOVIE DATA --------------------
    
    def retrieve_data(self, skip_checked_entries):
        self.show_progress_screen()
        threading.Thread(
            target=self.retrieve_data_thread,
            args=(skip_checked_entries,),
            daemon=True
        ).start()

    def retrieve_data_thread(self, skip_checked_entries):
        tmdb = setup_apis()
        num_entries = len(self.movie_data)

        i = 0
        for idx, movie_dict in enumerate(self.movie_data):
            new_data, self.errors = get_movie_info(
                    self.filename, 
                    self.user_ratings, 
                    movie_dict, 
                    self.errors, 
                    skip_checked_entries=skip_checked_entries
                )

            if new_data:
                i += 1
            
                # add all the details, then ratings, then cast and poster url
                priority_fields = [
                    'Director', 'Runtime (minutes)', 'Budget', 'Box Office', 
                    'Country of Origin', 'Spoken Languages', 'Classification', 'IMDb ID', 'IMDb Rating',
                    'Metascore', 'Tomatometer (Critic Score)', 'Popcornmeter (Audience Score)',
                    'Letterboxd Average Rating', 'Letterboxd My Rating', 'Academy Award Nominations',
                    'Academy Award Wins', 'Academy Award Details'
                ]
                for k in list(new_data.keys()):
                    if k in priority_fields:
                        movie_dict[k] = new_data.pop(k)
                movie_dict.update(new_data)

                # save function
                if i == 6:
                    save_progress(self.filename, "src/tmp/", self.movie_data, self.errors)
                    i = 0
            
            self.ws.after(0, self.update_progress, idx, num_entries)



        self.ws.after(0, self.finish_retrieving)
    
    def finish_retrieving(self):
        self.close_progress_screen()
        messagebox.showinfo("Done", "Movie data retrieval complete!")

    # -------------------- UI WINDOWS --------------------

    def print_lb_ratings(self):
        window = tk.Toplevel(self.ws)
        window.title("Letterboxd Updates")

        self.movie_data, missing_films = add_new_letterboxd_entries(
            self.movie_data,
            self.user_ratings
        )

        tk.Label(
            window, 
            font=('Cooper Black', 15), 
            text=f"You've watched {len(missing_films)} new properties\nsince last upload:"
        ).pack(pady=10)

        tk.Label(
            window,
            text=", ".join(v['name'] for v in missing_films.values()),
            wraplength=350
        ).pack(padx=10, pady=10)

        tk.Button(window, text='OK', command=window.destroy).pack(pady=10)

    # -------------------- MAIN MENU --------------------

    def add_main_menu(self, canvas):
        container = tk.Frame(canvas, bg='black')
        container.pack(fill="both", expand=True)

        buttons = [
            ("Get Latest Letterboxd Logs", self.print_lb_ratings, '#40bdf5', 30),
            ("Fill All Missing Data", lambda: self.retrieve_data(False), '#ff7d01', 20),
            ("Fill Only Latest Entries", lambda: self.retrieve_data(True), '#ff7d01', 20),
            ("Export Data", self.export_data, '#00e155', 30),
        ]

        for text, cmd, color, width in buttons:
            b = tk.Button(
                container,
                text=text,
                command=cmd,
                bg=color,
                font=self.button_font,
                width=width
            ).pack(pady=5)

    # -------------------- START SCREEN --------------------

    def setup_interface(self):
        self.ws.title("CineFiles")
        self.ws.configure(bg="black")

        self.main_canvas = tk.Canvas(
            self.ws, 
            height=HEIGHT, 
            width=WIDTH,
            bg='black', 
            highlightbackground='black'
        )
        self.main_canvas.pack()

        title = tk.Label(
            self.main_canvas,
            text="CineFiles",
            font=("Cooper Black", 40, 'bold'),
            fg="red",
            image=self.icon,
            compound='top',
            bg="black"
        ).pack(pady=20)

        container = tk.Frame(self.main_canvas, bg='black')
        container.pack()

        tk.Label(
            container,
            text='Select data source:',
            fg='white',
            bg='black',
            font=(self.button_font[0], self.button_font[1], 'bold')
        ).pack(pady=10)

        tk.Button(
            container,
            text="Upload Excel File 📁",
            bg='#A3CFA4',
            font=self.button_font,
            width=30,
            command=lambda: self.load_data(start_mode=True)
        ).pack(pady=5)

        tk.Button(
            container,
            text="Load from Save File 💾",
            bg='#FFF3BD',
            font=self.button_font,
            width=30,
            command=self.load_data
        ).pack(pady=5)

        self.first_time = True


if __name__ == "__main__":
    App()
