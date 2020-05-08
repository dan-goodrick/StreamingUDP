import tkinter as tk
from tkinter import font
from twisted.internet import tksupport, reactor, task
from twisted.internet.protocol import DatagramProtocol
import socket
import json
from protocol import BuildStreamingUDP, ParseStreamingUDP

def valid_IP(ip):
    segs = ip.split('.')
    if len(segs) != 4:
        return False
    for seg in segs:
        if len(seg) > 3:
            return False
        if not seg.isnumeric():
            return False
        if int(seg) < 0  or int(seg) >= 256:
            return False
    return True

class RX(DatagramProtocol):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.params = {}

    def datagramReceived(self, datagram, address):
        self.msg = datagram.decode('utf-8')
        self.widget.set(self.msg)  # update the label

class GUI():
    def __init__(self):
        self.root = tk.Tk()
        self.cnt = 0
        self.running = None
        self.root.protocol('WM_DELETE_WINDOW', self.exit)
        tksupport.install(self.root)
        self.tx_loop = task.LoopingCall(self.send_message)
        self.main_window()
        # self.root.mainloop()
        reactor.run()

    def main_window(self):
        self.tx = tk.LabelFrame(self.root,
                                text='Transmited Message')
        self.tx.pack(fill="y", side='left')
        self.build_tx_frame()
        self.rx = tk.LabelFrame(self.root,
                                text='Received Message',)
        self.rx.pack(fill="y", side='right')
        self.build_rx_frame()
        self.build_quit_frame()

    def build_rx_frame(self):
        self.rx_port = tk.IntVar()
        self.rx_port.set("7200")
        self.rx_port_label = tk.Label(self.rx,text="Receive port:" )
        self.rx_port_label.grid(row=0, column=0)#pack(side='left')
        self.rx_port_label['font'] = font.Font(weight='bold')
        self.rx_port_field = tk.Entry(self.rx,
                                      textvariable=self.rx_port)
        self.rx_port_field.grid(row=0, column=1)#.pack(side='right')
        self.rx_msg = tk.StringVar()
        self.rx_msg.set('')
        reactor.listenUDP(int(self.rx_port.get()), RX(self.rx_msg))

        self.msg_lbl = tk.Label(self.rx, textvariable=self.rx_msg, width=75)
        self.msg_lbl.grid(row=1, column=0, columnspan=2)#.pack(side='bottom')
        self.rx_labels = {}
        self.rx_param = {}
        self.rx_params = {}
        self.rx_dict = {}
        self.init_msg()
        self.rx_msg.trace('w', self.parse_msg)

    def init_msg(self, *args):
        self.rx_dict = self.load_rx_dict()
        for key in self.rx_dict:
            if "Reserved" in key:
                continue
            self.rx_labels[key] = tk.Label(self.rx,text=f"{key}:", anchor="e" )
            self.rx_param[key] = tk.StringVar()
            self.rx_param[key].set('')
            self.rx_params[key] = tk.Label(self.rx, textvariable=self.rx_param[key])
            self.rx_labels[key].grid(column=0)
            self.rx_params[key].grid(column=1, row=self.rx_labels[key].grid_info()['row'])

    def parse_msg(self, *args):
        self.rx_dict = ParseStreamingUDP(self.rx_msg.get())
        for key,val in self.rx_dict.items():
            if "Reserved" in key:
                continue
            self.rx_param[key].set(val)
            self.rx_params[key] = tk.Label(self.rx, textvariable=self.rx_param[key])

    def load_tx_dict(self):
        with open('tx.json') as f:
            data = json.load(f)
        if type(data) == dict:
            return data
        else:
            return {'Version':"Error loading 'tx.json' file"}

    def load_rx_dict(self):
        with open('rx.json') as f:
            data = json.load(f)
        if type(data) == dict:
            return data
        else:
            return {'Version':"Error loading 'rx.json' file"}

    def listen(self):
        try:
            reactor.listenUDP(int(self.rx_port.get()), RX(self.rx_msg))
        except Exception as e:
            print(e)
            print(f'Port {self.rx_port.get()} unavailable.  Select a different port')

    def build_tx_frame(self):
        self.state = tk.StringVar()
        self.state.set("Send Message") # initial Button text
        self.tx_cmd = tk.Checkbutton(self.tx,
                                     onvalue="Edit Message",
                                     offvalue="Start Sending",
                                     indicatoron=False,
                                     variable=self.state, #enables var.get
                                     textvariable=self.state, #prints onvalue/offvalue on button
                                     command=self.tx_toggle,
                                     width=30)
        self.tx_cmd.grid(row=0, column=0, columnspan = 4, sticky = tk.W+tk.E,)
        self.tx_cmd['font'] = font.Font(size=20, weight='bold')
        self.tx_ip = tk.StringVar()
        self.tx_ip.set('127.0.0.1')
        self.tx_ip_label = tk.Label(self.tx,text="Transmit IP (x.x.x.x):" )
        self.tx_ip_label.grid(row=1, column=0)#pack(side='left')
        self.tx_ip_field = tk.Entry(self.tx,
                                    textvariable=self.tx_ip,
                                    validate="focusout",
                                    validatecommand=self.update_ip)
        self.tx_ip_field.grid(row=1, column=1)#.pack(side='right')

        self.tx_port = tk.IntVar()
        self.tx_port.set(7200)
        self.tx_port_label = tk.Label(self.tx,text="Transmit port:" )
        self.tx_port_label.grid(row=2, column=0)#pack(side='left')
        self.tx_port_field = tk.Entry(self.tx,
                                      textvariable=self.tx_port)
        self.tx_port_field.grid(row=2, column=1)#.pack(side='right')

        self.tx_freq = tk.IntVar()
        self.tx_freq.set(1000)
        self.tx_freq_label = tk.Label(self.tx,text="Message Ferquency (ms):" )
        self.tx_freq_label.grid(row=3, column=0)#pack(side='left')
        self.tx_freq_field = tk.Entry(self.tx,
                                      textvariable=self.tx_freq)
        self.tx_freq_field.grid(row=3, column=1)#.pack(side='right')

        self.tx_msg = tk.StringVar()
        self.tx_dict = self.load_tx_dict()
        self.tx_labels = {}
        self.tx_fields = {}
        for key in self.tx_dict:
            if 'Reserved' in key:
                continue
            if key == 'Type': #with a refresh button, I could dynamically choose which Name to show in the congig window
                self.tx_labels[key] = tk.Label(self.tx,text=f"{key} ('STS', or 'CMD'):", anchor="e"  )
            else:
                self.tx_labels[key] = tk.Label(self.tx,text=f"{key}:", anchor="e" )
            self.tx_fields[key] = tk.Entry(self.tx)
            self.tx_fields[key].insert(tk.END, self.tx_dict[key])
            self.tx_labels[key].grid(column=0)
            self.tx_fields[key].grid(column=1, row=self.tx_labels[key].grid_info()['row'])

    def update_ip(self):
        if not valid_IP(self.tx_ip.get()):
            print(f'{self.tx_ip.get()} is not a valid IP address')
            self.tx_ip.set("127.0.0.1")

    def update_dict(self):
        for key in self.tx_fields:
            self.tx_dict[key] = self.tx_fields[key].get()

    def update_msg(self):
        self.tx_dict['Sequence'] = self.cnt
        self.tx_msg.set(BuildStreamingUDP(self.tx_dict))

    def tx_toggle(self):
        if self.tx_loop.running:
            self.tx_loop.stop()
        if self.state.get() == "Edit Message":
            print("turning on...")
            self.running = True
            self.update_dict()
        else:
            print(f"edit message...")
            self.running = False
        self.tx_loop.start(self.tx_freq.get()/1000.)
        # self.tx_id = self.tx.after(int(self.tx_freq.get()), self.send_message)

    def send_message(self):
        if self.running:
            self.cnt += 1
            self.update_msg()
            # print(f'Sending to: {self.tx_ip.get()} Port:{self.tx_port.get()} Freq: {self.tx_freq.get()} msg/sec \n{self.tx_msg.get()}')
            sock = socket.socket(socket.AF_INET, # Internet
                                 socket.SOCK_DGRAM) # UDP
            sock.sendto(self.tx_msg.get().encode(), (self.tx_ip.get(), int(self.tx_port.get())))
        # After freq milliseconds, call send_message again (create a recursive loop)
        # self.tx_id = self.tx.after(int(self.tx_freq.get()), self.send_message)

    def build_quit_frame(self):
        self.quit = tk.Frame(self.root)
        self.quit.pack(side='bottom', fill='x', anchor='s')
        self.quit_button = tk.Button(self.root,text="Exit",command=self.exit)
        self.quit_button['font'] = font.Font(size=16, weight='bold')
        self.quit_button.pack(anchor='s')

    def exit(self):
        reactor.stop()
        self.root.destroy()


if __name__ == "__main__":
    window = GUI()
    # to do:
    # store last TX values in a pickle file
    # Make parameter names modifiable from the GUI
    # have a reset button
