import tkinter as tk
import socket
import threading

PORT = 12345

USAGE="""USAGE: To connect to existing server input IP-Address on the right
USAGE: To start a server click on \"Listen\" Button"""

class Connector(tk.Frame):
    def __init__(self, master):
        print(USAGE)
        super().__init__(master)

        self.master = master
        self.successful = False
        self.in_mainloop = True
        self.frm_connect = tk.Frame(self)
        self.frm_connect.columnconfigure(1, minsize=100)
        self.btn_connect = tk.Button(self.frm_connect, text="Connect", command=lambda: self.start(self.connect))
        self.ent_ip = tk.Entry(self.frm_connect)
        self.btn_connect.grid(row=0, column=0, padx=5, pady=2.5)
        self.ent_ip.grid(row=0, column=1, padx=5) 
        
        self.rowconfigure([0, 1], minsize=30)
        self.frm_connect.grid(row=0, columnspan=2)
        self.btn_listen = tk.Button(self, text="Listen", command=lambda: self.start(self.listen))
        self.btn_listen.grid(row=1, column=0, padx=5, pady=2.5, sticky="w")
        self.btn_cancel = tk.Button(self, text="Cancel", command=self.stop)
        self.btn_cancel.grid(row=1, column=1, sticky="w")
        self.btn_cancel.grid_remove()

        self.thread = threading.Thread(target=lambda: "dummy")

    def enable_buttons(self):
        self.btn_connect["state"] = "active"
        self.btn_listen["state"] = "active"

    def disable_buttons(self):
        self.btn_connect["state"] = "disable"
        self.btn_listen["state"] = "disable"

    def start(self, target):
        self.disable_buttons()
        self.btn_cancel.grid()
        self.thread = threading.Thread(target=target)
        self.thread.start()

    def stop(self):
        if self.in_mainloop:
            self.enable_buttons()
            self.btn_cancel.grid_remove()
        self.sock.close()

    def listen(self):
        print(f"STATUS: Listening on port {PORT}")
        self.sock = socket.socket()
        try:
            self.sock.bind(("", PORT))
            self.sock.listen(1)
            self.sock.settimeout(0.5)
            while True:
                if self.in_mainloop:
                    try: self.conn, addr = self.sock.accept() 
                    except: continue
                    break
                else: return
            self.sock.settimeout(0)
        except OSError as e: 
            print(e)
            self.stop()
            return
        print(f"STATUS: Got connection from {addr[0]}")
        self.successful = True
        self.role = "server"
        self.master.quit()

    def connect(self):
        self.sock = socket.socket()
        ip = self.ent_ip.get()
        #[DEBUG]
        if not ip: ip = "localhost"
        print(f"STATUS: Connecting to {ip}")
        try: self.sock.connect((ip, PORT))
        except OSError as e:
            self.stop()
            print(e)
            return
        print("STATUS: Connection successful")
        self.successful = True
        self.conn = self.sock
        self.role = "client"
        self.master.quit()

    def cleanup(self):
        self.in_mainloop = False
        if self.thread.is_alive(): self.sock.close()

    def is_successful(self):
        return self.successful

    def get_results(self):
        return self.conn, self.role

if __name__ == "__main__":
    connector = Connector()
    connector.mainloop()
    if connector.successful:
        connection = connector.conn
        role = connector.role
        connector.destroy()
        #WTF window has to be destroyed before communication otherwise very laggy
        if role == "server": 
            connection.send(b"Hello from the server side!")
            print(connection.recv(50).decode())
        elif role == "client":
            print(connection.recv(50).decode())
            connection.send(b"Hello from the client side!")
        input("close...")
        connection.close()
    elif connector.thread.is_alive(): connector.sock.close()
    
