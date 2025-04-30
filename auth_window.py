import customtkinter as ctk
from tkinter import messagebox
from db_utils import login_user, register_user, init_db
import main

def open_auth_window():
    init_db()
    ctk.set_appearance_mode("dark")  # Options: "dark", "light", or "system"
    ctk.set_default_color_theme("blue")  # You can try "green", "dark-blue", etc.

    def handle_login():
        username = username_entry.get()
        password = password_entry.get()
        user_id = login_user(username, password)
        if user_id:
            root.destroy()
            main.launch_main_app(user_id)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def handle_register():
        username = username_entry.get()
        password = password_entry.get()
        if register_user(username, password):
            messagebox.showinfo("Success", "Registration successful. You can now log in.")
        else:
            messagebox.showerror("Error", "Username already taken.")

    # Create main window
    root = ctk.CTk()
    root.title("Login or Register")
    window_width = 360
    window_height = 280
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.resizable(False, False)

    # UI Components
    ctk.CTkLabel(root, text="Username:", text_color="white").pack(pady=(20, 5))
    username_entry = ctk.CTkEntry(root, width=220)
    username_entry.pack(pady=5)

    ctk.CTkLabel(root, text="Password:", text_color="white").pack(pady=(10, 5))
    password_entry = ctk.CTkEntry(root, show="*", width=220)
    password_entry.pack(pady=5)

    ctk.CTkButton(root, text="Login", command=handle_login, width=150).pack(pady=(20, 8))
    ctk.CTkButton(root, text="Register", command=handle_register, width=150, fg_color="#2563eb").pack()

    root.mainloop()

if __name__ == "__main__":
    open_auth_window()
