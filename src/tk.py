import tkinter as tk
from tkinter import ttk

# root window
root = tk.Tk()
root.geometry('300x120')
root.title('Progressbar Demo')

root.grid()

# progressbar
pb = ttk.Progressbar(
    root,
    orient='horizontal',
    mode='indeterminate',
    length=280
)
# place the progressbar
pb.grid(column=0, row=0, columnspan=2, padx=10, pady=20)
pb.start()

def New_Window(height=200, width=200):
        window = tk.Toplevel()
        canvas = tk.Canvas(window, height=height, width=width)
        canvas.pack()

        # start button
        start_button = ttk.Button(
            canvas,
            text='Start',
            command=pb.start
        )
        start_button.grid(column=0, row=1, padx=10, pady=10, sticky=tk.E)
        return window, canvas

window, canvas = New_Window(height=200, width=200)
# stop button
stop_button = ttk.Button(
    root,
    text='Stop',
    command=pb.stop
)
stop_button.grid(column=1, row=1, padx=10, pady=10, sticky=tk.W)


root.mainloop()