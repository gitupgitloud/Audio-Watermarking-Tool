import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
from tkinter import messagebox, filedialog
import customtkinter as ctk
import audio_utils as au
import pygame
import soundfile as sf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Initialize pygame mixer for audio playback
pygame.mixer.init()

class ToolTip:
    def __init__(self, widget, text, delay=0.5):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tipwindow = None
        self.id = None
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

def clear_plots(root):
    """Clear existing matplotlib plots from the window"""
    for widget in root.winfo_children():
        if isinstance(widget, FigureCanvasTkAgg):
            widget.get_tk_widget().destroy()
        elif hasattr(widget, '_fig_cache'):
            # Handle any custom plot containers if they exist
            widget.destroy()

def display_waveform_in_window(root):
    if au.original_audio is None or au.sr is None:
        messagebox.showwarning("Warning", "No audio loaded.")
        return

    clear_plots(root)
    
    fig, ax = plt.subplots(figsize=(10, 4))
    time_values = np.linspace(0, len(au.original_audio)/au.sr, len(au.original_audio))
    ax.plot(time_values, au.original_audio)
    ax.set_title('Audio Waveform')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Amplitude')
    
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(pady=20, fill='both', expand=True)
    canvas._fig_cache = fig  # Keep reference to prevent garbage collection

    # Connect click event for audio playback
    def on_click(event):
        if event.inaxes == ax:
            click_time = event.xdata
            play_audio_from_time(click_time)
    
    canvas.mpl_connect('button_press_event', on_click)

    # Progress line for playback
    progress_line, = ax.plot([], [], color='r', linewidth=2)
    
    def update_progress():
        if pygame.mixer.music.get_busy():
            current_pos = pygame.mixer.music.get_pos() / 1000
            progress_line.set_data([current_pos, current_pos], 
                                 [min(au.original_audio), max(au.original_audio)])
            canvas.draw()
            root.after(100, update_progress)
    
    update_progress()

def display_mel_spectrogram_in_window(root):
    if au.original_audio is None or au.sr is None:
        messagebox.showwarning("Warning", "No audio loaded.")
        return

    clear_plots(root)
    
    S = librosa.feature.melspectrogram(y=au.original_audio, sr=au.sr, n_mels=128)
    S_dB = librosa.power_to_db(S, ref=np.max)

    fig, ax = plt.subplots(figsize=(10, 4))
    img = librosa.display.specshow(S_dB, sr=au.sr, 
                                 x_axis='time', y_axis='mel', ax=ax)
    fig.colorbar(img, ax=ax, format='%+2.0f dB')
    ax.set_title('Mel Spectrogram')
    
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(pady=20, fill='both', expand=True)
    canvas._fig_cache = fig

def display_extracted_watermark(root, watermark, sr, method):
    clear_plots(root)
    
    # Create frame for plots and button
    container = ctk.CTkFrame(root)
    container.pack(fill='both', expand=True, pady=10)
    
    # Create side-by-side plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Left plot - Waveform
    time = np.arange(len(watermark)) / sr
    ax1.plot(time, watermark)
    ax1.set_title(f"{method} Watermark Signal")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Amplitude")
    
    # Right plot - Histogram
    ax2.hist(watermark, bins=50)
    ax2.set_title("Value Distribution")
    ax2.set_xlabel("Amplitude")
    ax2.set_ylabel("Count")
    
    plt.tight_layout()
    
    # Embed plots in the container
    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas.draw()
    canvas.get_tk_widget().pack(side='top', fill='both', expand=True)
    canvas._fig_cache = fig
    
    # Add SNR info if available
    if au.original_audio is not None and au.watermarked_audio is not None:
        snr = au.calculate_snr(au.original_audio, au.watermarked_audio)
        snr_label = ctk.CTkLabel(container, 
                                text=f"Watermark SNR: {snr:.2f} dB",
                                font=ctk.CTkFont(size=14, weight='bold'))
        snr_label.pack(pady=5)
    
    # Save button
    btn_frame = ctk.CTkFrame(root)
    btn_frame.pack(pady=10)
    
    def save_watermark():
        file_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav")]
        )
        if file_path:
            sf.write(file_path, watermark, sr)
            messagebox.showinfo("Success", "Watermark saved successfully.")
    
    save_btn = ctk.CTkButton(btn_frame, 
                           text="Save Extracted Watermark", 
                           command=save_watermark)
    save_btn.pack()

def play_audio_from_time(start_time):
    if au.original_audio is None or au.sr is None:
        messagebox.showwarning("Warning", "No audio loaded.")
        return

    start_sample = int(start_time * au.sr)
    pygame.mixer.music.load(au.current_file)
    pygame.mixer.music.play(start=start_sample / au.sr)