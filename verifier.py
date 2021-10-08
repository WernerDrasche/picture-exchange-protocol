import tkinter as tk
from tkinter import messagebox
import io
import threading
from PIL import Image, ImageTk

MAX_INIT_SIZE = 10

USAGE = """USAGE: Enter = Accept
USAGE: Escape = Decline
INFO: If you decline once the program will be stopped
INFO: The image will be saved only if both parties accept at all stages"""

class Verifier(tk.Frame):
    def __init__(self, master, conn, role, images):
        super().__init__(master)

        self.master = master
        self.conn = conn
        self.role = role
        self.images = images
        self.stage = 0
        self.stages = len(images)
        self.stages_other = 0
        self.successful = False
        self.paniced = False
        self.busy = False
        self.forcequit = False

        self.image_gui = ImageTk.PhotoImage(self.images[self.stage])
        self.active = tk.Label(self, image=self.image_gui)
        self.active.pack()

        self.thread = threading.Thread(target=self.init2)
        self.thread.start()

    def init2(self):
        print("STATUS: Waiting for partner to finish editing...")
        print("INFO: The program might become unresponsive for a while")
        try: 
            self.stages_other = int(self.exchange_text(str(self.stages)))
            self.image = self.exchange_image(self.images[self.stage])
        except: 
            self.panic()
            return
        self.image_gui = ImageTk.PhotoImage(self.image)
        self.active["image"] = self.image_gui

        if self.stages < self.stages_other:
            for _ in range(self.stages_other - self.stages):
                self.images.insert(-2, self.images[-2])

        self.bind("<Return>", lambda _: self.start("ACCEPT"))
        self.bind("<Escape>", lambda _: self.start("DECLINE"))
        self.focus_force()
        print(USAGE)

    def start(self, arg):
        if self.busy: return
        self.busy = True
        self.thread = threading.Thread(target=self.verify, args=(arg,))
        self.thread.start()

    def verify(self, msg_send):
        print(f"STATUS: Stage {self.stage + 1} -> {msg_send}")
        try: msg_recv = self.exchange_text(msg_send)
        except: 
            self.panic()
            return
        if msg_send == "ACCEPT" and msg_recv == "ACCEPT":
            self.stage += 1
        else:
            if msg_recv == "DECLINE":
                messagebox.showinfo("Info", "Your image was declined")
            print("STATUS: Image was declined")
            print("STATUS: Operation aborted")
            self.master.quit()
        if self.stage == len(self.images):
            print("STATUS: Operation successful")
            self.successful = True
            self.master.quit()
        else:
            try: self.image = self.exchange_image(self.images[self.stage])
            except:
                self.panic()
                return
            self.image_gui = ImageTk.PhotoImage(self.image)
            self.active["image"] = self.image_gui
            if self.stages_other - 1 <= self.stage < self.stages - 1:
                self.verify("ACCEPT")
            else:
                self.busy = False
    
    def exchange_text(self, msg_send):
        msg_recv = self.exchange(msg_send.encode())
        return msg_recv.decode()

    def exchange_image(self, img_send):
        fd = io.BytesIO()
        img_send.save(fd, "png")
        img_recv = self.exchange(fd.getvalue())
        if self.stage != 0: self.image.close()
        fd.close()
        return Image.open(io.BytesIO(img_recv))
        
    def exchange(self, to_send):
        size_send = str(len(to_send))
        size_send = "0" * (MAX_INIT_SIZE - len(size_send)) + size_send
        if self.role == "client":
            self.conn.sendall(size_send.encode())
            size_recv = int(self.recvall(MAX_INIT_SIZE).decode())
            self.conn.sendall(to_send)
            return self.recvall(size_recv)
        elif self.role == "server":
            size_recv = int(self.recvall(MAX_INIT_SIZE).decode())
            self.conn.sendall(size_send.encode())
            received = self.recvall(size_recv)
            self.conn.sendall(to_send)
            return received

    def recvall(self, size):
        msg = bytes()
        while len(msg) < size:
            recv = self.conn.recv(size - len(msg))
            if not recv: raise IOError
            msg += recv
        return msg

    def ask_resume(self):
        print("STATUS: Waiting for partner to make up his mind...")
        print("INFO: The program might become unresponsive for a while")
        try: other = self.exchange_text("RESUME") 
        except: return False
        return other == "RESUME"

    def panic(self):
        if not self.forcequit:
            print("ERROR: Connection lost")
            print("STATUS: Operation aborted")
            self.paniced = True
            messagebox.showerror("Error", "Connection lost")
            self.master.quit()

    def cleanup(self):
        self.forcequit = True
        for stage in range(self.stages):
            self.images[stage].close()
        self.conn.close()

    def has_paniced(self):
        return self.paniced

    def is_successful(self):
        return self.successful

    def get_results(self):
        return self.image
