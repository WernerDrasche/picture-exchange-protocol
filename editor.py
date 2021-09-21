import tkinter as tk
from PIL import ImageTk, Image, ImageFilter, ImageDraw

USAGE = """USAGE: Mousewheel Up = Blur+
USAGE: Mousewheel Down = Blur-
USAGE: Mousebutton Left = Create Rectangle (Drag)
USAGE: Mousebutton Right = Delete Rectangle (Click)
USAGE: Enter = Confirm and Exchange"""

class Editor(tk.Canvas):
    def __init__(self, master, filename, **kwargs):
        print(USAGE)
        self.successful = False
        self.master = master
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
        self.timer = 0
        self.bind("<Up>", self.simulate_scroll)
        self.bind("<Down>", self.simulate_scroll)
        self.bind("<Button-1>", self.new_rect)
        self.bind("<B1-Motion>", self.resize_rect)
        self.bind("<ButtonRelease-1>", self.create_rect)
        self.bind("<Return>", self.finish)
        self.focus_force()

    def simulate_scroll(self, event):
        if self.timer:
            self.timer -= 1
            return
        class ScrollEvent:
            def __init__(self, num):
                self.num = num
                self.delta = 0
        if event.keysym == "Up": event = ScrollEvent(4)
        elif event.keysym == "Down": event = ScrollEvent(5)
        self.change_blur(event)
        self.timer = 3 

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
