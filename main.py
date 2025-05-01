import customtkinter as ctk
from tkinter import filedialog, messagebox
import audio_utils as au
import visual_utils as vu
import librosa
import sqlite3
import os
import webbrowser
from PIL import Image, ImageTk
import pygame

class ToolTip:
    def __init__(self, widget, text, delay=0.5):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.schedule)
        self.widget.bind("<Leave>", self.hidetip)
        self.widget.bind("<Motion>", self.motion)
        self.widget.bind("<ButtonPress>", self.hidetip)

    def schedule(self, event):
        self.unschedule()
        self.id = self.widget.after(int(self.delay * 1000), self.showtip)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def motion(self, event):
        self.unschedule()
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

    def showtip(self):
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        
        self.tipwindow = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(fg_color="#333333")
        
        label = ctk.CTkLabel(tw, text=self.text,
                            fg_color="#333333",
                            text_color="white",
                            corner_radius=5,
                            padx=10, pady=5)
        label.pack()

    def hidetip(self, event=None):
        self.unschedule()
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

class AudioPlayerControls:
    def __init__(self, parent):
        self.frame = ctk.CTkFrame(parent)
        self.frame.pack(pady=10)
        
        self.play_img = ctk.CTkImage(Image.open("assets/play.png").resize((20,20)))
        self.pause_img = ctk.CTkImage(Image.open("assets/pause.png").resize((20,20)))
        self.stop_img = ctk.CTkImage(Image.open("assets/stop.png").resize((20,20)))
        
        self.play_button = ctk.CTkButton(
            self.frame, text="", image=self.play_img,
            width=40, command=self.play_audio,
            fg_color="transparent", hover_color="#2A3A5A"
        )
        self.play_button.pack(side="left", padx=5)
        
        self.pause_button = ctk.CTkButton(
            self.frame, text="", image=self.pause_img,
            width=40, command=self.pause_audio,
            fg_color="transparent", hover_color="#2A3A5A"
        )
        self.pause_button.pack(side="left", padx=5)
        
        self.stop_button = ctk.CTkButton(
            self.frame, text="", image=self.stop_img,
            width=40, command=self.stop_audio,
            fg_color="transparent", hover_color="#2A3A5A"
        )
        self.stop_button.pack(side="left", padx=5)
        
        self.volume_slider = ctk.CTkSlider(
            self.frame, from_=0, to=100,
            command=self.set_volume
        )
        self.volume_slider.set(70)
        self.volume_slider.pack(side="left", padx=10)
        
        ToolTip(self.play_button, "Play audio")
        ToolTip(self.pause_button, "Pause audio")
        ToolTip(self.stop_button, "Stop audio")
        ToolTip(self.volume_slider, "Adjust volume")

    def play_audio(self):
        if au.original_audio is not None:
            pygame.mixer.music.play()

    def pause_audio(self):
        pygame.mixer.music.pause()

    def stop_audio(self):
        pygame.mixer.music.stop()

    def set_volume(self, value):
        pygame.mixer.music.set_volume(float(value)/100)

def show_help():
    help_text = """Audio Watermarking Tool Help:

1. Load an audio file (WAV or MP3)
2. Select watermarking method (LSB or Echo Hiding)
3. Adjust strength using the slider
4. Embed the watermark
5. Save the watermarked audio

For extraction:
1. Load original and watermarked files
2. Select the method used
3. Extract the watermark
                                        """
    messagebox.showinfo("Help", help_text)

def open_docs():
    webbrowser.open("https://github.com/gitupgitloud/Audio-Watermarking-Tool")

def launch_main_app(user_id):
    global watermark_strength, current_user_id, current_view
    watermark_strength = 5
    current_user_id = user_id
    current_view = "waveform"
    au.current_user_id = user_id

    # Initialize pygame mixer
    pygame.mixer.init()

    # Appearance settings
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")  

    root = ctk.CTk()
    root.title("Audio Watermarking Tool")
    root.configure(fg_color="#0D1B2A")

    # Fonts
    raleway_regular = ctk.CTkFont(family="Raleway", size=14)
    raleway_bold = ctk.CTkFont(family="Raleway", size=20, weight="bold")
    raleway_large = ctk.CTkFont(family="Raleway", size=35, weight="bold")

    # Window positioning
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = min(1000, screen_width - 100)
    window_height = min(700, screen_height - 100)
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Menu bar
    menu_frame = ctk.CTkFrame(root, height=30, fg_color="#1B263B")
    menu_frame.pack(fill="x", padx=0, pady=0)
    
    help_button = ctk.CTkButton(menu_frame, text="Help", width=60, 
                              command=show_help, font=raleway_regular)
    help_button.pack(side="left", padx=5)
    
    docs_button = ctk.CTkButton(menu_frame, text="Documentation", width=120,
                              command=open_docs, font=raleway_regular)
    docs_button.pack(side="left", padx=5)

    # Status bar
    status_bar = ctk.CTkLabel(root, text="Ready", height=20, 
                            font=raleway_regular, anchor="w", 
                            fg_color="#1B263B", text_color="white")
    status_bar.pack(side="bottom", fill="x", padx=0, pady=0)

    def update_status(message):
        status_bar.configure(text=message)
        root.update()

    # Main tab view
    tabview = ctk.CTkTabview(root, fg_color="#0D1B2A")
    tabview.pack(fill="both", expand=True, padx=20, pady=(5,0))

    def toggle_view():
        global current_view
        if current_view == "waveform":
            vu.display_mel_spectrogram_in_window(root)
            current_view = "mel"
            toggle_button.configure(text="Show Waveform")
        else:
            vu.display_waveform_in_window(root)
            current_view = "waveform"
            toggle_button.configure(text="Show Spectrogram")

    # LSB Watermarking Tab
    lsb_tab = tabview.add("LSB Watermarking")

    # Audio player controls
    lsb_player = AudioPlayerControls(lsb_tab)

    load_button_lsb = ctk.CTkButton(lsb_tab, text="Load Audio", 
                                  command=lambda: [au.load_audio(root), update_status(f"Loaded: {os.path.basename(au.current_file)}")],
                                  width=300, height=80, font=raleway_large)
    ToolTip(load_button_lsb, "Load an audio file for watermarking (WAV or MP3)")
    load_button_lsb.pack(pady=10)

    strength_label = ctk.CTkLabel(lsb_tab, 
                                text=f"Watermark Strength: {watermark_strength}/10 (Recommended: 6)", 
                                font=raleway_regular)
    strength_label.pack(pady=5)

    strength_slider_lsb = ctk.CTkSlider(lsb_tab, from_=1, to=10, number_of_steps=9,
                                      command=lambda value: au.update_watermark_strength(value, strength_label))
    strength_slider_lsb.set(watermark_strength)
    strength_slider_lsb.pack(pady=5)

    embed_button_lsb = ctk.CTkButton(lsb_tab, text="Embed LSB Watermark", 
                                   command=lambda: [au.embed_watermark("LSB"), update_status("LSB watermark embedded")],
                                   font=raleway_bold)
    ToolTip(embed_button_lsb, "Embed a Least Significant Bit watermark in the audio")
    embed_button_lsb.pack(pady=10)

    button_frame_lsb = ctk.CTkFrame(lsb_tab, fg_color="#0D1B2A")
    button_frame_lsb.pack(fill="x", pady=10)

    save_button_lsb = ctk.CTkButton(button_frame_lsb, 
                                  text="Save to Device", 
                                  command=lambda: [au.save_audio(), update_status(f"Saved to {au.saved_audio_path}")],
                                  font=raleway_regular)
    ToolTip(save_button_lsb, "Save the watermarked audio to your computer")
    save_button_lsb.pack(side="left", padx=20, expand=True)

    save_db_button_lsb = ctk.CTkButton(button_frame_lsb, 
                                     text="Save to Database",
                                     command=lambda: [au.save_watermarked_to_db(au.saved_audio_path, "LSB", "LSB"), update_status("Saved to database")],
                                     font=raleway_regular)
    ToolTip(save_db_button_lsb, "Save the watermarked audio to the database")
    save_db_button_lsb.pack(side="right", padx=20, expand=True)

    # Echo Hiding Tab
    echo_tab = tabview.add("Echo Hiding")

    # Audio player controls
    echo_player = AudioPlayerControls(echo_tab)

    load_button_echo = ctk.CTkButton(echo_tab, text="Load Audio", 
                                   command=lambda: [au.load_audio(root), update_status(f"Loaded: {os.path.basename(au.current_file)}")],
                                   width=300, height=80, font=raleway_large)
    ToolTip(load_button_echo, "Load an audio file for watermarking (WAV or MP3)")
    load_button_echo.pack(pady=10)

    strength_label_echo = ctk.CTkLabel(echo_tab, 
                                     text=f"Watermark Strength: {watermark_strength}/10 (Recommended: 6)", 
                                     font=raleway_regular)
    strength_label_echo.pack(pady=5)

    strength_slider_echo = ctk.CTkSlider(echo_tab, from_=1, to=10, number_of_steps=9,
                                       command=lambda value: au.update_watermark_strength(value, strength_label_echo))
    strength_slider_echo.set(watermark_strength)
    strength_slider_echo.pack(pady=5)

    embed_button_echo = ctk.CTkButton(echo_tab, text="Embed Echo Watermark", 
                                    command=lambda: [au.embed_watermark("Echo Hiding"), update_status("Echo watermark embedded")],
                                    font=raleway_bold)
    ToolTip(embed_button_echo, "Embed an echo-based watermark in the audio")
    embed_button_echo.pack(pady=10)

    button_frame_echo = ctk.CTkFrame(echo_tab, fg_color="#0D1B2A")
    button_frame_echo.pack(fill="x", pady=10)

    save_button_echo = ctk.CTkButton(button_frame_echo, 
                                   text="Save to Device", 
                                   command=lambda: [au.save_audio(), update_status(f"Saved to {au.saved_audio_path}")],
                                   font=raleway_regular)
    ToolTip(save_button_echo, "Save the watermarked audio to your computer")
    save_button_echo.pack(side="left", padx=20, expand=True)

    save_db_button_echo = ctk.CTkButton(button_frame_echo, 
                                      text="Save to Database",
                                      command=lambda: [au.save_watermarked_to_db(au.saved_audio_path, "Echo Hiding", "Echo"), update_status("Saved to database")],
                                      font=raleway_regular)
    ToolTip(save_db_button_echo, "Save the watermarked audio to the database")
    save_db_button_echo.pack(side="right", padx=20, expand=True)

    # Extraction Tab
    extraction_tab = tabview.add("Extract Watermark")
    
    load_frame = ctk.CTkFrame(extraction_tab)
    load_frame.pack(pady=10)
    
    load_original_button = ctk.CTkButton(load_frame, text="Load Original", 
                                       command=lambda: [au.load_original_for_extraction(), update_status("Original audio loaded")],
                                       width=150)
    ToolTip(load_original_button, "Load the original unwatermarked audio for comparison")
    load_original_button.pack(side="left", padx=10)
    
    load_watermarked_button = ctk.CTkButton(load_frame, text="Load Watermarked", 
                                          command=lambda: [au.load_watermarked_for_extraction(), update_status("Watermarked audio loaded")],
                                          width=150)
    ToolTip(load_watermarked_button, "Load the watermarked audio for extraction")
    load_watermarked_button.pack(side="left", padx=10)
    
    method_var = ctk.StringVar(value="LSB")
    method_combobox = ctk.CTkComboBox(extraction_tab, 
                                    values=["LSB", "Echo Hiding"], 
                                    variable=method_var,
                                    width=200)
    ToolTip(method_combobox, "Select the watermarking method used")
    method_combobox.pack(pady=10)
    
    def handle_extraction():
        method = method_var.get()
        watermark = au.extract_watermark(method)
        if watermark is not None:
            vu.display_extracted_watermark(root, watermark, au.sr, method)
            update_status(f"{method} watermark extracted")
    
    extract_button = ctk.CTkButton(extraction_tab, text="Extract Watermark", 
                                 command=handle_extraction,
                                 width=200)
    ToolTip(extract_button, "Extract the watermark from the audio")
    extract_button.pack(pady=10)
    
    def extract_from_db():
        files = au.get_user_files_from_db()
        if not files:
            messagebox.showinfo("Info", "No files found in database.")
            return
            
        file_window = ctk.CTkToplevel()
        file_window.title("Select File to Extract From")
        file_window.geometry("400x300")
        
        scroll_frame = ctk.CTkScrollableFrame(file_window)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for file in files:
            def create_handler(file_id):
                def handler():
                    conn = sqlite3.connect('watermarking.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT audio_data FROM watermarked_audio WHERE id=?", (file_id,))
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result:
                        temp_path = "temp_watermarked.wav"
                        with open(temp_path, "wb") as f:
                            f.write(result[0])
                        
                        audio, sr = librosa.load(temp_path, sr=None)
                        au.watermarked_audio = audio
                        au.sr = sr
                        update_status(f"Loaded from DB: {file[2]}")
                        file_window.destroy()
                    else:
                        messagebox.showerror("Error", "Could not load file from database.")
                
                return handler
            
            btn = ctk.CTkButton(scroll_frame, 
                               text=f"{file[2]} ({file[3]})", 
                               command=create_handler(file[0]),
                               width=350,
                               anchor="w")
            btn.pack(pady=5)
    
    db_extract_button = ctk.CTkButton(extraction_tab, text="Extract From Database", 
                                    command=extract_from_db,
                                    width=200)
    ToolTip(db_extract_button, "Extract watermark from files saved in the database")
    db_extract_button.pack(pady=10)

    def view_my_files():
        files = au.get_user_files_from_db()
        if not files:
            messagebox.showinfo("Files", "No files found in database.")
            return
        
        files_window = ctk.CTkToplevel()
        files_window.title("My Watermarked Files")
        files_window.geometry("600x400")
        
        scroll_frame = ctk.CTkScrollableFrame(files_window)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for file in files:
            file_info = (
                f"File: {file[2]}\n"
                f"Method: {file[3]}\n"
                f"Watermark: {file[4]}\n"
                f"Created: {file[6]}\n"
                "------------------------"
            )
            label = ctk.CTkLabel(scroll_frame, text=file_info, justify="left")
            label.pack(pady=5, anchor="w")

    # Bottom control buttons
    control_frame = ctk.CTkFrame(root, fg_color="#0D1B2A")
    control_frame.pack(side="bottom", fill="x", padx=10, pady=5)

    view_button = ctk.CTkButton(control_frame, text="My Files", 
                              command=view_my_files, 
                              font=raleway_regular,
                              width=120)
    ToolTip(view_button, "View all your previously watermarked files")
    view_button.pack(side="left", padx=10)

    toggle_button = ctk.CTkButton(control_frame, text="Show Spectrogram", 
                                command=toggle_view, 
                                font=raleway_regular,
                                width=150)
    ToolTip(toggle_button, "Switch between waveform and spectrogram views")
    toggle_button.pack(side="right", padx=10)
    
    # Add Update Waveform button
    update_button = ctk.CTkButton(control_frame, 
                                text="Update Waveform", 
                                command=lambda: vu.display_waveform_in_window(root), 
                                font=raleway_regular,
                                width=150)
    ToolTip(update_button, "Refresh the waveform display")
    update_button.pack(side="right", padx=10)

    # Set focus to first tab
    tabview.set("LSB Watermarking")

    root.mainloop()

if __name__ == "__main__":
    from auth_window import open_auth_window
    user_id = open_auth_window()
    if user_id:
        launch_main_app(user_id)