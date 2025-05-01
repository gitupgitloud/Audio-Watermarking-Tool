import numpy as np
import librosa
import soundfile as sf
from tkinter import filedialog, messagebox
import sqlite3
import os
import datetime
import visual_utils as vu
import db_utils
import customtkinter as ctk

# Globals
current_user_id = None
original_audio = None
watermarked_audio = None
sr = None
watermark_strength = 5  # On a 1-10 scale
saved_audio_path = None
current_file = None

def calculate_snr(original_signal, watermarked_signal):
    """Calculate Signal-to-Noise Ratio between original and watermarked audio"""
    if original_signal is None or watermarked_signal is None:
        return None
        
    if len(original_signal) != len(watermarked_signal):
        return None
        
    # Calculate signal power (original audio)
    signal_power = np.mean(original_signal**2)
    
    # Calculate noise power (difference between original and watermarked)
    noise = watermarked_signal - original_signal
    noise_power = np.mean(noise**2)
    
    # Avoid division by zero
    if noise_power == 0:
        return float('inf')
        
    snr = 10 * np.log10(signal_power / noise_power)
    return snr

def load_audio(root=None):
    global current_file
    filename = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav *.mp3")])
    if filename:
        try:
            audio, sr = librosa.load(filename, sr=None)
            globals()['original_audio'] = audio
            globals()['sr'] = sr
            globals()['current_file'] = filename
            print(f"Loaded {filename}")
            
            if root:
                # Update status bar
                for widget in root.winfo_children():
                    if isinstance(widget, ctk.CTkLabel) and widget.cget("text").startswith("Ready"):
                        widget.configure(text=f"Loaded: {os.path.basename(filename)} | SR: {sr}Hz | Duration: {len(audio)/sr:.2f}s")
                        break
                
                # Force waveform update
                vu.display_waveform_in_window(root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load audio: {str(e)}")

def lsb_watermark():
    global watermarked_audio, original_audio, sr, watermark_strength
    if original_audio is None:
        messagebox.showwarning("Warning", "Load an audio file first.")
        return
    strength_linear = watermark_strength / 10 * 0.05
    watermark_data = np.random.uniform(-0.01, 0.01, len(original_audio))
    watermarked_audio = original_audio + (watermark_data * strength_linear)
    
    # Calculate and show SNR
    snr = calculate_snr(original_audio, watermarked_audio)
    messagebox.showinfo("Success", 
                       f"LSB watermark embedded successfully.\nSNR: {snr:.2f} dB")

def echo_hiding():
    global watermarked_audio, original_audio, sr, watermark_strength
    if original_audio is None:
        messagebox.showwarning("Warning", "Load an audio file first.")
        return
    strength_linear = watermark_strength / 10 * 0.05
    delay = 1000
    watermark_data = np.random.uniform(-0.01, 0.01, len(original_audio))
    echo_signal = np.zeros_like(original_audio)
    echo_signal[delay:] = watermark_data[:-delay] * strength_linear
    watermarked_audio = original_audio + echo_signal
    
    # Calculate and show SNR
    snr = calculate_snr(original_audio, watermarked_audio)
    messagebox.showinfo("Success", 
                       f"Echo Hiding watermark embedded successfully.\nSNR: {snr:.2f} dB")

def save_audio():
    global watermarked_audio, sr, saved_audio_path
    if watermarked_audio is None:
        messagebox.showwarning("Warning", "No watermarked audio to save.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV Files", "*.wav")])
    if file_path:
        sf.write(file_path, watermarked_audio, sr)
        saved_audio_path = file_path
        messagebox.showinfo("Success", "Watermarked audio saved successfully.")

def update_watermark_strength(value, strength_label):
    global watermark_strength
    watermark_strength = int(round(float(value)))
    strength_label.configure(text=f"Watermark Strength: {watermark_strength}/10 (Recommended: 6)")

def embed_watermark(method):
    if method == "LSB":
        lsb_watermark()
    elif method == "Echo Hiding":
        echo_hiding()

def get_user_files_from_db():
    if not current_user_id:
        return []
    conn = sqlite3.connect('watermarking.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM watermarked_audio WHERE user_id = ?", (current_user_id,))
    files = cursor.fetchall()
    conn.close()
    return files

def save_watermarked_to_db(file_path, method, watermark_text):
    global current_user_id
    if not file_path or not os.path.exists(file_path):
        messagebox.showerror("Error", "No valid audio file to save.")
        return

    # Create progress window
    progress_window = ctk.CTkToplevel()
    progress_window.title("Saving...")
    progress_window.geometry("300x100")
    progress_label = ctk.CTkLabel(progress_window, text="Saving to database...")
    progress_label.pack(pady=10)
    progress_bar = ctk.CTkProgressBar(progress_window)
    progress_bar.pack(pady=10)
    progress_bar.set(0)
    progress_window.update()

    try:
        with open(file_path, 'rb') as f:
            audio_data = f.read()
        progress_bar.set(0.5)
        progress_window.update()

        filename = os.path.basename(file_path)

        db_utils.save_watermarked_file(
            user_id=current_user_id,
            file_path=filename,
            method=method,
            watermark=method,
            audio_data=audio_data
        )
        progress_bar.set(1.0)
        messagebox.showinfo("Success", "Watermarked audio saved to database.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save to database: {e}")
    finally:
        progress_window.destroy()

# Watermark Extraction Functions
def extract_lsb_watermark():
    global original_audio, watermarked_audio, sr
    if original_audio is None or watermarked_audio is None:
        messagebox.showwarning("Warning", "Load both original and watermarked audio first.")
        return None
    
    if len(original_audio) != len(watermarked_audio):
        messagebox.showwarning("Warning", "Audio files must be the same length.")
        return None
    
    extracted_watermark = watermarked_audio - original_audio
    return extracted_watermark

def extract_echo_watermark():
    global watermarked_audio, sr
    if watermarked_audio is None:
        messagebox.showwarning("Warning", "Load watermarked audio first.")
        return None
    
    delay = 1000
    extracted_watermark = np.zeros_like(watermarked_audio)
    extracted_watermark[:-delay] = watermarked_audio[delay:]
    return extracted_watermark

def extract_watermark(method):
    if method == "LSB":
        return extract_lsb_watermark()
    elif method == "Echo Hiding":
        return extract_echo_watermark()
    else:
        messagebox.showwarning("Warning", "Unknown watermarking method.")
        return None

def load_original_for_extraction():
    filename = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav *.mp3")])
    if filename:
        audio, sr = librosa.load(filename, sr=None)
        globals()['original_audio'] = audio
        globals()['sr'] = sr
        print(f"Loaded original audio: {filename}")
        return True
    return False

def load_watermarked_for_extraction():
    filename = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav *.mp3")])
    if filename:
        audio, sr = librosa.load(filename, sr=None)
        globals()['watermarked_audio'] = audio
        globals()['sr'] = sr
        print(f"Loaded watermarked audio: {filename}")
        return True
    return False