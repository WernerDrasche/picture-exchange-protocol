from os import system
import platform
import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename
from connector import Connector
from editor import Editor
from verifier import Verifier

OS = platform.system()
FILETYPES = [("Image Files", (".png", ".jpg", ".jpeg"))]

def main():
    window = tk.Tk()
    connector = Connector(window)
    connector.pack()
    window.mainloop()
    if not connector.is_successful():
        # triggered only when exiting forcefully
        connector.cleanup() 
        return
    conn, role = connector.get_results()
    connector.destroy()

    window.withdraw()
    while True:
        filename = askopenfilename(parent=window, filetypes=FILETYPES)
        window.deiconify()
        if not filename:
            conn.close()
            return
        editor = Editor(window, filename)
        editor.pack()
        window.mainloop()
        if not editor.is_successful():
            conn.close()
            editor.cleanup()
            return
        images = editor.get_results()
        editor.destroy()

        verifier = Verifier(window, conn, role, images)
        if verifier.has_paniced():
            verifier.cleanup()
            return
        verifier.pack()
        window.mainloop()
        if not verifier.is_successful():
            verifier.cleanup()
            return
        image = verifier.get_results()

        window.withdraw()
        filename = asksaveasfilename(parent=window, filetypes=[("Image Files", ".png")])
        if filename:
            if not ".png" in filename: filename += ".png"
            image.save(filename)

        answer = messagebox.askyesno("Question", "One more time?")
        window.update()
        if not answer or not verifier.ask_resume():
            print("INFO: One party wanted to stop")
            verifier.cleanup()
            break

        for img in images:
            img.close()
        verifier.destroy()
        
        if OS == "Windows": system("cls")
        elif OS == "Linux": system("clear")
    
    window.destroy()


if __name__ == "__main__": main()
