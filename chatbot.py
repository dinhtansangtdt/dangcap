import tkinter as tk
from tkinter import ttk
import speech_recognition as sr
from openai import OpenAI
from gtts import gTTS
import pygame
import tempfile
import uuid
from threading import Thread
import time
import os
import re
from collections import deque
from PIL import Image, ImageTk


class AIChatBot:
    def __init__(self, root):
        self.root = root
        self.root.title("Trợ lý AI ChatBot")
        self.root.geometry("320x480")
        self.root.configure(bg="#EAEAEA")
        self.root.resizable(False, False)

        # API
        self.client = OpenAI(api_key="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")

        # Voice & State
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.stop_speaking_flag = False
        self.conversation_history = deque(maxlen=10)
        self.last_activity_time = time.time()
        self.wake_word = "bạn ơi"
        self.wake_word_detected = False
        self.is_resetting = False

        pygame.mixer.init()

        # UI
        self.setup_ui()
        Thread(target=self.background_wake_listener, daemon=True).start()
        self.root.after(10000, self.check_auto_reset)

    # ===== UI =====
    def setup_ui(self):
        header = tk.Frame(self.root, bg="#4CAF50", height=80)
        header.pack(fill=tk.X)

        try:
            logo_path = "Logo.png"
            logo = Image.open(logo_path).resize((55, 55), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo)
            tk.Label(header, image=self.logo_photo, bg="#4CAF50").pack(side=tk.LEFT, padx=10, pady=8)
        except:
            pass

        tk.Label(header, text="Trợ lý AI ChatBot", bg="#4CAF50", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        chat_area = tk.Frame(self.root, bg="#EAEAEA")
        chat_area.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(chat_area, bg="#EAEAEA", highlightthickness=0)
        self.chat_frame = tk.Frame(self.canvas, bg="#EAEAEA")
        self.scrollbar = ttk.Scrollbar(chat_area, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
        self.chat_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        controls = tk.Frame(self.root, bg="#DADADA")
        controls.pack(fill=tk.X, pady=2)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Blue.TButton", background="#2196F3", foreground="white", font=("Arial", 10, "bold"))
        style.configure("Red.TButton", background="#E53935", foreground="white", font=("Arial", 10, "bold"))
        style.configure("Gray.TButton", background="#9E9E9E", foreground="white", font=("Arial", 10, "bold"))

        self.start_btn = ttk.Button(controls, text="🎤 Bắt đầu", style="Blue.TButton", command=self.toggle_listening)
        self.start_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3, pady=3)
        self.reset_btn = ttk.Button(controls, text="🔄 Reset", style="Gray.TButton", command=self.reset_chat)
        self.reset_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3, pady=3)

        self.status = tk.Label(self.root, text="⚫ Sẵn sàng", bg="#EAEAEA", fg="#555", font=("Arial", 9))
        self.status.pack(fill=tk.X, pady=(0, 2))

        tk.Label(
            self.root, text="Powered by Bình Thuận College", bg="#EAEAEA", fg="#888", font=("Arial", 8, "italic")
        ).pack(side=tk.BOTTOM, pady=(0, 3))

    # ===== Tin nhắn =====
    def fade_in(self, widget, steps=10, duration=0.5):
        delay = int((duration / steps) * 1000)
        def gradual(i=0):
            if i <= steps:
                widget.update()
                self.root.after(delay, gradual, i + 1)
        gradual()

    def add_message(self, text, sender="ai"):
        text = self.clean_text(text)
        frame = tk.Frame(self.chat_frame, bg="#EAEAEA")

        if sender == "user":
            msg = tk.Label(frame, text=text, bg="#BBDEFB", fg="#000", wraplength=260,
                           justify="left", anchor="e", padx=10, pady=6, font=("Arial", 11))
            msg.pack(anchor="e", padx=6, pady=3, ipadx=4, ipady=2, fill="x")
        elif sender == "ai":
            msg = tk.Label(frame, text="", bg="#FFFFFF", fg="#000", wraplength=260,
                           justify="left", anchor="w", padx=10, pady=6, font=("Arial", 11))
            msg.pack(anchor="w", padx=6, pady=3, ipadx=4, ipady=2, fill="x")
            self.animate_typing(msg, text)
        else:
            msg = tk.Label(frame, text=text, bg="#EAEAEA", fg="gray", font=("Arial", 9, "italic"))
            msg.pack(anchor="center", pady=2)

        frame.pack(fill=tk.X, expand=True)
        self.fade_in(msg)
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def animate_typing(self, label, text, delay=25):
        def effect(i=0):
            if i <= len(text):
                label.config(text=text[:i])
                self.canvas.update_idletasks()
                self.canvas.yview_moveto(1.0)
                self.root.after(delay, effect, i + 1)
        effect()

    def show_typing_indicator(self):
        lbl = tk.Label(self.chat_frame, text="AI đang gõ", bg="#FFFFFF", fg="#777",
                       padx=10, pady=5, font=("Arial", 10, "italic"))
        lbl.pack(anchor="w", padx=6, pady=3)
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

        def animate():
            dots = ""
            while getattr(lbl, "running", True):
                dots = "." * ((len(dots) + 1) % 4)
                lbl.config(text=f"AI đang gõ{dots}")
                time.sleep(0.4)
        lbl.running = True
        Thread(target=animate, daemon=True).start()
        return lbl

    def remove_typing_indicator(self, lbl):
        lbl.running = False
        lbl.destroy()

    # ===== Mic điều khiển =====
    def toggle_listening(self):
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        if self.is_resetting:  # tránh lỗi khi reset
            return
        self.is_listening = True
        self.start_btn.config(text="⏸️ Dừng", style="Red.TButton")
        self.status.config(text="🎤 Đang lắng nghe...")
        Thread(target=self.listen_loop, daemon=True).start()

    def stop_listening(self):
        self.is_listening = False
        self.start_btn.config(text="🎤 Bắt đầu", style="Blue.TButton")
        self.status.config(text="⚫ Đã dừng")
        self.stop_audio()

    def listen_loop(self):
        while self.is_listening:
            try:
                with sr.Microphone() as src:
                    self.recognizer.adjust_for_ambient_noise(src, duration=0.5)
                    audio = self.recognizer.listen(src, timeout=5, phrase_time_limit=8)
                    text = self.recognizer.recognize_google(audio, language="vi-VN")
                    if text:
                        self.add_message(text, "user")
                        self.process_question(text)
            except sr.WaitTimeoutError:
                continue
            except Exception:
                continue

    # ===== GPT xử lý =====
    def process_question(self, question):
        try:
            self.conversation_history.append({"role": "user", "content": question})
            messages = [{"role": "system", "content": "Bạn là trợ lý AI tiếng Việt thân thiện, tự nhiên, ngắn gọn."}]
            messages.extend(self.conversation_history)

            typing = self.show_typing_indicator()
            response = self.client.chat.completions.create(model="gpt-4o", messages=messages, max_tokens=300)
            answer = self.clean_text(response.choices[0].message.content)

            self.remove_typing_indicator(typing)
            self.conversation_history.append({"role": "assistant", "content": answer})
            self.add_message(answer, "ai")
            self.speak(answer)
        except Exception as e:
            self.add_message(f"Lỗi: {e}", "system")

    # ===== TTS =====
    def speak(self, text):
        try:
            was_listening = self.is_listening
            self.is_listening = False
            self.status.config(text="🔊 Đang trả lời...")
            temp = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.mp3")
            gTTS(text=self.clean_text(text), lang="vi").save(temp)
            self.stop_audio()
            Thread(target=self.play_audio, args=(temp, was_listening), daemon=True).start()
        except Exception as e:
            print("TTS lỗi:", e)

    def play_audio(self, filename, resume=False):
        try:
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        finally:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            if os.path.exists(filename):
                os.remove(filename)
            if resume and not self.is_resetting:
                self.add_message("(🎤 Tiếp tục lắng nghe...)", "system")
                self.start_listening()

    def stop_audio(self):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
        except:
            pass

    # ===== Công cụ =====
    def clean_text(self, text):
        return re.sub(r"\*{1,2}|#+", "", text).strip()

    def reset_chat(self):
        self.is_resetting = True
        self.stop_audio()
        self.stop_listening()
        for w in self.chat_frame.winfo_children():
            w.destroy()
        self.canvas.yview_moveto(0.0)
        self.conversation_history.clear()
        self.status.config(text="⚫ Đã reset")
        self.start_btn.config(text="🎤 Bắt đầu", style="Blue.TButton")
        self.wake_word_detected = False
        self.is_listening = False
        self.is_resetting = False

    def background_wake_listener(self):
        while True:
            try:
                with sr.Microphone() as src:
                    self.recognizer.adjust_for_ambient_noise(src, duration=0.5)
                    audio = self.recognizer.listen(src, timeout=5, phrase_time_limit=5)
                    text = self.recognizer.recognize_google(audio, language="vi-VN").lower()
                    if self.wake_word in text and not self.is_listening:
                        self.add_message("(🎧 Nghe thấy 'bạn ơi'...)", "system")
                        self.start_listening()
            except:
                continue

    def check_auto_reset(self):
        if time.time() - self.last_activity_time > 300:
            self.add_message("⏰ Tự động reset do không hoạt động", "system")
            self.reset_chat()
        self.root.after(10000, self.check_auto_reset)


def main():
    root = tk.Tk()
    app = AIChatBot(root)
    root.mainloop()


if __name__ == "__main__":
    main()
