import tkinter as tk
from PIL import ImageTk, Image, ImageFilter, ImageDraw
import threading
import time

USAGE = """USAGE: Mousewheel Up = Blur+
USAGE: Mousewheel Down = Blur-
USAGE: Mousebutton Left = Create Rectangle (Drag)
USAGE: Mousebutton Right = Delete Rectangle (Click)
USAGE: Enter = Confirm and Exchange"""

class KeyTracker:
    def __init__(self, keys, duration):
        self.keys = {key: False for key in keys}
        self.duration = duration

    def press(self, key, callback):
        if self.keys[key]: return
        self.keys[key] = True
        threading.Thread(target=lambda: self.lock(key)).start()
        callback()
        
    def lock(self, key):
        time.sleep(self.duration)
        self.keys[key] = False

class ScrollEvent:
    def __init__(self, event):
        if event.keysym == "Up": self.num = 4
        if event.keysym == "Down": self.num = 5
        self.delta = 0

class Editor(tk.Canvas):
    def __init__(self, master, filename, **kwargs):
        print(USAGE)
        self.successful = False
        self.master = master
        self.key_tracker = KeyTracker(["Up", "Down"], 0.10)
        self.rects = {}
        self.current_rect = -1
        self.blur = 0.0
        self.image = Image.open(filename)
        if self.image.mode not in ["RGB", "RGBA"]:
            new = self.image.convert("RGBA")
            self.image.close()
            self.image = new
        self.blurred = self.image.copy()
        self.image_gui = ImageTk.PhotoImage(self.blurred)
        kwargs["width"] = self.image_gui.width()
        kwargs["height"] = self.image_gui.height()
        super().__init__(master, **kwargs)
        self.image_id = self.create_image(0, 0, image=self.image_gui, anchor="nw")
        self.bind("<MouseWheel>", self.change_blur)
        self.bind("<Up>", lambda event: self.key_tracker.press(
            "Up", lambda: self.change_blur(ScrollEvent(event))))
        self.bind("<Down>", lambda event: self.key_tracker.press(
            "Down", lambda: self.change_blur(ScrollEvent(event))))
        self.bind("<Button-1>", self.new_rect)
        self.bind("<B1-Motion>", self.resize_rect)
        self.bind("<ButtonRelease-1>", self.create_rect)
        self.bind("<Return>", self.finish)
        self.focus_force()

    def change_blur(self, event):
        if event.num == 4 or event.delta == 120: sign = 1
        elif event.num == 5 or event.delta == -120: sign = -1
        self.blur += 0.5 * sign
        self.blur = max(0.0, self.blur)
        tmp = self.blurred
        self.blurred = self.image.filter(ImageFilter.GaussianBlur(self.blur))
        tmp.close()
        self.image_gui = ImageTk.PhotoImage(self.blurred)
        self.itemconfigure(self.image_id, image=self.image_gui)

    def new_rect(self, event):
        coords = [event.x, event.y, event.x, event.y]
        self.current_rect = self.create_rectangle(*coords)
        self.rects[self.current_rect] = coords
        

    def resize_rect(self, event):
        self.rects[self.current_rect][2] = event.x
        self.rects[self.current_rect][3] = event.y
        self.coords(self.current_rect, *self.rects[self.current_rect])

    def create_rect(self, _):
        def make_deleter(handle):
            return lambda _: self.delete_rect(handle)
        self.itemconfigure(self.current_rect, fill="BLACK")
        self.tag_bind(self.current_rect, "<Button-3>", make_deleter(self.current_rect))

    def delete_rect(self, rect):
        self.delete(rect)
        del self.rects[rect]

    def finish(self, _):
        print("STATUS: Image locked and sent")
        self.successful = True
        self.master.quit()

    def cleanup(self):
        self.image.close()
        self.blurred.close()

    def is_successful(self):
        return self.successful
    
    def get_results(self):
        imgs_with_rects = [self.blurred, self.image.copy()]
        for img in imgs_with_rects:
            for rect in self.rects.values():
                draw = ImageDraw.Draw(img)
                draw.rectangle(rect, "BLACK", "BLACK")
        return imgs_with_rects[0], imgs_with_rects[1], self.image
    
if __name__ == "__main__":
    window = tk.Tk()
    editor = Editor(window, "test.png")
    editor.pack()
    window.mainloop()
