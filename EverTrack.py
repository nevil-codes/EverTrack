import tkinter as tk
from tkinter import messagebox
import json
import matplotlib.pyplot as plt

# Load or initialize data
try:
    with open("data.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {'Read': 30}  # Initialize with default habit if JSON doesn't exist

# Function to add habit
def add_habit():
    habit = entry_habit.get()
    duration = entry_duration.get()
    if habit and duration:
        data[habit] = duration
        with open("data.json", "w") as f:
            json.dump(data, f)
        messagebox.showinfo("Success", f"Habit '{habit}' added!")
        entry_habit.delete(0, tk.END)
        entry_duration.delete(0, tk.END)
    else:
        messagebox.showwarning("Input Error", "Please enter both fields.")

# GUI setup
root = tk.Tk()
root.title("EverTrack")

tk.Label(root, text="Habit:").pack()
entry_habit = tk.Entry(root)
entry_habit.pack()

tk.Label(root, text="Duration (min):").pack()
entry_duration = tk.Entry(root)
entry_duration.pack()

tk.Button(root, text="Add Habit", command=add_habit).pack()

root.mainloop()