from tkinter import ttk, messagebox
import tkinter as tk
import json
import colorsys
from ttkbootstrap import Style

class TodoListApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Todo List App")
        self.geometry("700x600")  # Set initial size for the main window

        # Create a ttkbootstrap Style with a different theme
        style = Style(theme="minty")  # Change theme here

        # Customize widget styles
        style.configure("Custom.TEntry", foreground="gray")
        style.configure("TButton", font=("Arial", 12))  # Change font for all buttons

        # Frame for task input and buttons
        input_frame = ttk.Frame(self, padding=(10, 10, 10, 0))
        input_frame.pack(fill=tk.X)

        # Entry for adding tasks
        self.task_input = ttk.Entry(input_frame, font=("Arial", 16), style="Custom.TEntry")
        self.task_input.grid(row=0, column=0, columnspan=7, sticky="ew", padx=5, pady=5)
        self.task_input.insert(0, "Enter your todo here...")
        self.task_input.configure(state=tk.NORMAL)  # Enable editing

        self.task_input.bind("<FocusIn>", self.clear_placeholder)
        self.task_input.bind("<FocusOut>", self.restore_placeholder)

        # Buttons for operations
        button_padding = 10
        ttk.Button(input_frame, text="Add Task", style="success.TButton", command=self.add_task).grid(row=1, column=0, padx=button_padding, pady=button_padding, sticky="ew")
        ttk.Button(input_frame, text="Clear", command=self.clear_input).grid(row=1, column=1, padx=button_padding, pady=button_padding, sticky="ew")
        ttk.Button(input_frame, text="Mark Done", style="success.TButton", command=self.mark_done).grid(row=1, column=2, padx=button_padding, pady=button_padding, sticky="ew")
        ttk.Button(input_frame, text="Delete", command=self.delete_selected_task).grid(row=1, column=3, padx=button_padding, pady=button_padding, sticky="ew")

        # Menubutton for delete options
        delete_menu_button = ttk.Menubutton(input_frame, text="Delete Options", direction="below")
        delete_menu_button.grid(row=1, column=4, padx=button_padding, pady=button_padding, sticky="ew")

        # Menu for delete options
        delete_menu = tk.Menu(delete_menu_button, tearoff=0)
        delete_menu_button.configure(menu=delete_menu)

        # Add delete options to the menu
        delete_menu.add_command(label="Delete All Undone Tasks", command=self.delete_undone_tasks)
        delete_menu.add_command(label="Delete Done Tasks", command=self.delete_marked_tasks)
        delete_menu.add_command(label="Delete All Tasks", command=self.delete_all_tasks)

        # Menubutton for picking background color
        self.color_menu_button = ttk.Menubutton(input_frame, text="Color", style="success.TButton", direction="below")
        self.color_menu_button.grid(row=1, column=5, padx=button_padding, pady=button_padding, sticky="ew")

        # Menu for color options
        self.color_menu = tk.Menu(self.color_menu_button, tearoff=0)
        self.color_menu_button.configure(menu=self.color_menu)

        # Predefined list of colors
        color_choices = {
            "Black": "#000000",
            "White": "#FFFFFF",
            "Grey": "#808080",
            "Sky Blue": "#87CEEB",
            "Yellow": "#FFFF00"
        }

        # Add color options to the menu
        for color_name, color_code in color_choices.items():
            self.color_menu.add_command(label=color_name, command=lambda c=color_code: self.set_background_color(c))

        # Frame for task list and scrollbar
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Listbox to display tasks
        self.task_list = tk.Listbox(list_frame, font=("Arial", 16), selectmode=tk.SINGLE, borderwidth=0, highlightthickness=0)
        self.task_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(0, 5))

        # Scrollbar for the task list
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_list.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.task_list.config(yscrollcommand=scrollbar.set)

        # Bind selection event to display task in Entry
        self.task_list.bind("<<ListboxSelect>>", self.display_selected_task)

        # Bind double-click event to deselect task
        self.task_list.bind("<Double-Button-1>", self.deselect_task)

        # Load tasks from file on startup
        self.load_tasks()

        # Undo and Redo variables
        self.history = []         # List to store history of tasks
        self.history_index = -1   # Index to track current position in history

        # Make the columns expand equally when the window is resized
        for i in range(7):
            input_frame.columnconfigure(i, weight=1)

        # Allow the listbox to expand with the window
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Bind Ctrl+Z and Ctrl+Y for undo and redo actions
        self.bind_all("<Control-z>", lambda event: self.undo_action())
        self.bind_all("<Control-y>", lambda event: self.redo_action())

    def set_background_color(self, color):
        self.task_list.configure(bg=color)  # Set background color of Listbox

        # Update font colors based on new background color
        for i in range(self.task_list.size()):
            current_fg_color = self.task_list.itemcget(i, "fg")
            new_fg_color = self.get_font_color(color)

            # Only update font color if the task is not marked as done (green)
            if current_fg_color != "green":
                self.task_list.itemconfig(i, fg=new_fg_color)

    def add_task(self):
        task = self.task_input.get()

        if task and task != "Enter your todo here...":
            try:
                selected_index = self.task_list.curselection()[0]
                current_fg_color = self.task_list.itemcget(selected_index, "fg")

                if current_fg_color != "green":
                    # Update the selected task
                    self.record_history()
                    self.task_list.delete(selected_index)
                    self.task_list.insert(selected_index, task)
                    self.task_list.itemconfig(selected_index, fg=self.get_font_color(self.task_list.cget("bg")))
                    self.task_list.selection_set(selected_index)
                    self.save_tasks()
                    self.clear_input()
                else:
                    messagebox.showwarning("Warning", "Cannot edit a completed task.")
            except IndexError:
                # Add a new task at the end of the list
                self.record_history()
                self.task_list.insert(tk.END, task)
                self.task_list.itemconfig(tk.END, fg=self.get_font_color(self.task_list.cget("bg")))
                self.save_tasks()
                self.clear_input()
        else:
            messagebox.showwarning("Warning", "Please enter a task.")

    def clear_input(self):
        self.task_input.delete(0, tk.END)

    def mark_done(self):
        try:
            selected_index = self.task_list.curselection()[0]
            current_fg_color = self.task_list.itemcget(selected_index, "fg")

            if current_fg_color != "green":
                self.record_history()
                self.task_list.itemconfig(selected_index, fg="green")
                self.save_tasks()
            else:
                messagebox.showwarning("Warning", "Task is already marked as done.")
        except IndexError:
            messagebox.showwarning("Warning", "Please select a task.")

    def delete_selected_task(self):
        try:
            selected_index = self.task_list.curselection()[0]
            self.record_history()
            self.task_list.delete(selected_index)
            self.save_tasks()
        except IndexError:
            messagebox.showwarning("Warning", "Please select a task.")

    def delete_undone_tasks(self):
        # Delete all tasks that are not marked as done (foreground color is not green)
        self.record_history()
        for i in reversed(range(self.task_list.size())):
            if self.task_list.itemcget(i, "fg") != "green":
                self.task_list.delete(i)
        self.save_tasks()

    def delete_marked_tasks(self):
        # Delete all tasks that are marked as done (foreground color is green)
        self.record_history()
        for i in reversed(range(self.task_list.size())):
            if self.task_list.itemcget(i, "fg") == "green":
                self.task_list.delete(i)
        self.save_tasks()

    def delete_all_tasks(self):
        # Delete all tasks (clear the listbox)
        self.record_history()
        self.task_list.delete(0, tk.END)
        self.save_tasks()

    def display_selected_task(self, event):
        try:
            selected_index = self.task_list.curselection()[0]
            current_fg_color = self.task_list.itemcget(selected_index, "fg")
            task_text = self.task_list.get(selected_index)

            if current_fg_color != "green":
                self.task_input.configure(state=tk.NORMAL)
                self.task_input.delete(0, tk.END)
                self.task_input.insert(0, task_text)
            else:
                self.task_input.configure(state=tk.DISABLED)

        except IndexError:
            pass

    def record_history(self):
        self.history_index += 1
        self.history = self.history[:self.history_index]
        current_tasks = [{"text": self.task_list.get(i), "color": self.task_list.itemcget(i, "foreground")} for i in range(self.task_list.size())]
        self.history.append(current_tasks)

    def undo_action(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.restore_state_from_history()

    def redo_action(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.restore_state_from_history()

    def restore_state_from_history(self):
        current_tasks = self.history[self.history_index]
        self.task_list.delete(0, tk.END)
        for task in current_tasks:
            self.task_list.insert(tk.END, task["text"])
            self.task_list.itemconfig(tk.END, fg=task["color"])
        self.save_tasks()

    def get_font_color(self, background_color):
        if not background_color:
            return "black"

        if len(background_color) != 7 or not background_color.startswith("#"):
            return "black"

        try:
            r = int(background_color[1:3], 16)
            g = int(background_color[3:5], 16)
            b = int(background_color[5:7], 16)
        except ValueError:
            return "black"

        brightness = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[2]

        if brightness < 0.5:
            return "white"
        else:
            return "black"

    def load_tasks(self):
        try:
            with open("tasks.json", "r") as f:
                tasks = json.load(f)
                for task in tasks:
                    self.task_list.insert(tk.END, task["text"])
                    self.task_list.itemconfig(tk.END, fg=task["color"])
        except FileNotFoundError:
            pass

    def save_tasks(self):
        data = []
        for i in range(self.task_list.size()):
            text = self.task_list.get(i)
            color = self.task_list.itemcget(i, "foreground")
            done = self.task_list.itemcget(i, "foreground") == "green"
            data.append({"text": text, "color": color, "done": done})
        with open("tasks.json", "w") as f:
            json.dump(data, f)

    def clear_placeholder(self, event):
        if self.task_input.get() == "Enter your todo here...":
            self.task_input.delete(0, tk.END)
            self.task_input.configure(style="TEntry")
            self.task_input.configure(state=tk.NORMAL)  # Enable editing on focus

    def restore_placeholder(self, event):
        if self.task_input.get() == "":
            self.task_input.insert(0, "Enter your todo here...")
            self.task_input.configure(style="Custom.TEntry")
            self.task_input.configure(state=tk.NORMAL)  # Enable editing when empty

    def deselect_task(self, event):
        self.task_list.selection_clear(0, tk.END)
        self.task_input.configure(state=tk.NORMAL)
        self.task_input.delete(0, tk.END)
        self.task_input.insert(0, "Enter your todo here...")
        self.task_input.configure(style="Custom.TEntry")

if __name__ == '__main__':
    app = TodoListApp()
    app.mainloop()
