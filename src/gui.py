import tkinter as tk
from tkinter import filedialog
from request_movie_site_data import get_letterboxd_user_ratings
import pandas as pd

def print_lb_ratings():
    ratings = get_letterboxd_user_ratings("DWynter10")
    print(ratings)

def browse_file():
    filename = filedialog.askopenfilename()
    df = pd.read_excel(filename)
    #whatever you need to do with your df...


window = tk.Tk()
window.geometry("800x600")
window.title("CineFiles")

icon = tk.PhotoImage(file="assets\cinefiles_icon.png")
window.iconphoto(True, icon)
window.config(background="black")

label_title = tk.Label(window, 
    text="CineFiles", 
    font=("Cooper Black", 40, 'bold'), 
    fg="red", 
    bg="black",
    image=icon, 
    compound='top',
    pady=15)
label_title.pack()

button1 = tk.Button(window, text="Upload Excel File")
button1.config(command=browse_file)
button1.config(font=("Calibri", 20), width=25)
button1.pack()

button2 = tk.Button(window, text="Get Latest Letterboxd Logs")
button2.config(command=print_lb_ratings)
button2.config(font=("Calibri", 20), width=25)
button2.pack()



button3 = tk.Button(window, text="Button3")
button3.config(font=("Calibri", 20), width=25)
button3.pack()

# label_count = Label(window, 
#     text="Cinefiles", 
#     font=("Cooper Black", 40, 'bold'), 
#     fg="red", 
#     bg="black",
#     image=icon, 
#     compound='top')
# label_count.pack()

window.mainloop()

