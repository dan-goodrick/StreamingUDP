import tkinter as tk
from tkinter import font
from twisted.internet import tksupport, reactor, task
from twisted.internet.protocol import DatagramProtocol
import socket
import json
from datetime import date
import time
from collections import defaultdict
from pprint import pprint

def get_checksum(string, num_digits=3):
    return abs(hash(string)) % (10 ** num_digits)

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

def BuildStreamingUDP(strmDict):
    #   Streaming Protocol Sample
    #   #|1.0|VEH_MHAFB1|CMD|123|45|56837|S,0|A,0|B,100|G,1|V,0|X,0,1,0,0,0,,,|Y,0,0,0,0,0,,,|Z,0,0,0,,,,,|C,XXX
    #   0   #                   Header
    #       |                   Delimiter
    #   1   1.0                 Message Version
    #   2   VEH_MHAFB1          Vehicle name
    #   3   CMD                 Command Message to Robotic Asset
    #   4   123                 Session ID
    #   5   45                  Message Sequence
    #   6   56837               Time stamp, ms from midnight
    #   7   0                   Steering Angle, Steering Wheel Centered
    #   8   0                   Throttle Percentage, 0%
    #   9   100                 Brake Percentage, 100%
    #   10  1                   Transmission state, 1=Park
    #   11  0                   Vehicle speed in mph
    #   12  Vehicle State       No Estop, No Pause, Enabled, Manual
    #   13  Vehicle Sequence    Not Initiating or shutting down, No Start, No Steering Cal, No Shifting
    #   14  Vehicle Mode        Progressive Steering, Progressive Braking, No Speed Control
    #   15  XXX                 Default Checksum

    TimeStamp = int((time.time() - time.mktime(date.today().timetuple()))*1000)
    msg = []
    msg.append('#') # Header
    msg.append(strmDict['Version']) #Version
    msg.append(strmDict['Name']) # Vehicle Name
    msg.append(strmDict['Type']) # Message Type
    msg.append(str(strmDict['Session'])) #Session ID
    msg.append(str(strmDict['Sequence'])) #Message Number
    msg.append(str(TimeStamp))
    msg.append(','.join(['S', str(strmDict['Steering'])]))
    msg.append(','.join(['A', str(strmDict['Throttle'])]))
    msg.append(','.join(['B', str(strmDict['Brake'])]))
    msg.append(','.join(['G', str(strmDict['Trans'])]))
    msg.append(','.join(['V', str(strmDict['Velocity'])]))
    msg.append(','.join(['X', str(strmDict['State_Estop']),
                              str(strmDict['State_Paused']),
                              str(strmDict['State_Manual']),
                              str(strmDict['State_Enable']),
                              str(strmDict['State_L1']),
                              str(strmDict['State_L2']),
                              str(strmDict['State_Motion']),
                              str(strmDict['State_Reserved7'])]))
    msg.append(','.join(['Y',str(strmDict['Process_Operation']),
                             str(strmDict['Process_Shutdown']),
                             str(strmDict['Process_Start']),
                             str(strmDict['Process_SteeringCal']),
                             str(strmDict['Process_TransShift']),
                             str(strmDict['Process_Reserved5']),
                             str(strmDict['Process_Reserved6']),
                             str(strmDict['Process_Reserved7'])]))
    msg.append(','.join(['Z',str(strmDict['Mode_ProgressiveSteeringDisable']),
                             str(strmDict['Mode_ProgressiveBrakingDisable']),
                             str(strmDict['Mode_VelocityControlEnable']),
                             str(strmDict['Mode_Reserved3']),
                             str(strmDict['Mode_Reserved4']),
                             str(strmDict['Mode_Reserved5']),
                             str(strmDict['Mode_Reserved6']),
                             str(strmDict['Mode_Reserved7'])]))
    chk = get_checksum('|'.join(msg))
    msg.append(','.join(['C',str(chk)]))
    return '|'.join(msg)

def ParseStreamingUDP(msg):
    #   Streaming Protocol Sample
    #   #|1.0|VEH_MHAFB1|CMD|123|45|56837|S,0|A,0|B,100|G,1|V,0|X,0,1,0,0,0,,,|Y,0,0,0,0,0,,,|Z,0,0,0,,,,,|C,XXX
    #   0   #                   Header
    #       |                   Delimiter
    #   1   1.0                 Message Version
    #   2   VEH_MHAFB1          Vehicle name
    #   3   CMD                 Command Message to Robotic Asset
    #   4   123                 Session ID
    #   5   45                  Message Sequence
    #   6   56837               Time stamp, ms from midnight
    #   7   0                   Steering Angle, Steering Wheel Centered
    #   8   0                   Throttle Percentage, 0%
    #   9   100                 Brake Percentage, 100%
    #   10  1                   Transmission state, 1=Park
    #   11  0                   Vehicle speed in mph
    #   12  Vehicle State       No Estop, No Pause, Enabled, Manual
    #   13  Vehicle Sequence    Not Initiating or shutting down, No Start, No Steering Cal, No Shifting
    #   14  Vehicle Mode        Progressive Steering, Progressive Braking, No Speed Control
    #   15  XXX                 Default Checksum
    parsed_UDP_msg = msg.split('|')
    # check that msg starts with a proper header character
    if parsed_UDP_msg[0] != '#':
        valid = False
    #verify checksum
    c,checksum = parsed_UDP_msg[15].split(',')
    if c == 'C':
        n = len(parsed_UDP_msg[15]) + 1#-n = start idx of checksum in msg
        chk = get_checksum(msg[:-n])
        if checksum.upper() == 'XXX' or chk == int(checksum):
            valid = True
        else:
            valid = False
    else:
        valid = False
    # populate the stream_in_dictionary
    strminDict = {}
    strminDict['Checksum'] = checksum
    strminDict['Version'] = parsed_UDP_msg[1]
    strminDict['Name'] = parsed_UDP_msg[2]
    strminDict['Type'] = parsed_UDP_msg[3]
    strminDict['Session'] = parsed_UDP_msg[4]
    strminDict['Sequence'] = parsed_UDP_msg[5]
    strminDict['TimeStamp'] = parsed_UDP_msg[6]

    # Get the steering command
    c,val = parsed_UDP_msg[7].split(',')
    if c == 'S':
        strminDict['Steering'] = int(val)
    else:
        valid = False

    # Get the throttle command
    c,val = parsed_UDP_msg[8].split(',')
    if c == 'A':
        strminDict['Throttle'] = int(val)
    else:
        valid = False

    # Get the break command
    c,val = parsed_UDP_msg[9].split(',')
    if c == 'B':
        strminDict['Brake'] = int(val)
    else:
        valid = False

    # Get the transission state (1=Parked)
    c,val = parsed_UDP_msg[10].split(',')
    if c == 'G':
        strminDict['Trans'] = int(val)
    else:
        valid = False

    # Get the velocity
    c,val = parsed_UDP_msg[11].split(',')
    if c == 'V':
        strminDict['Velocity'] = int(val)
    else:
        valid = False

    #break out the state parameters
    state_list = parsed_UDP_msg[12].split(',')
    if state_list.pop(0) == 'X':
        strminDict['State_Estop'] = state_list[0]
        strminDict['State_Paused'] = state_list[1]
        strminDict['State_Enable'] = state_list[2]
        strminDict['State_Manual'] = state_list[3]
        strminDict['State_L1'] = state_list[4]
        strminDict['State_L2'] = state_list[5]
        strminDict['State_Motion'] = state_list[6]
        strminDict['State_Reserved7'] = state_list[7]
    else:
        valid = False

    #break out the process parameters
    process_list = parsed_UDP_msg[13].split(',')
    if process_list.pop(0) == 'Y':
        strminDict['Process_Operation']=process_list[0]
        strminDict['Process_Shutdown']=process_list[1]
        strminDict['Process_Start']=process_list[2]
        strminDict['Process_SteeringCal']=process_list[3]
        strminDict['Process_TransShift']=process_list[4]
        strminDict['Process_Reserved5']=process_list[5]
        strminDict['Process_Reserved6']=process_list[6]
        strminDict['Process_Reserved7']=process_list[7]
    else:
        valid = False

    #break out the mode parameters
    mode_list = parsed_UDP_msg[14].split(',')
    if mode_list.pop(0) == 'Z':
        strminDict['Mode_ProgressiveSteeringDisable']=mode_list[0]
        strminDict['Mode_ProgressiveBrakingDisable']=mode_list[1]
        strminDict['Mode_VelocityControlEnable']=mode_list[2]
        strminDict['Mode_Reserved3']=mode_list[3]
        strminDict['Mode_Reserved4']=mode_list[4]
        strminDict['Mode_Reserved5']=mode_list[5]
        strminDict['Mode_Reserved6']=mode_list[6]
        strminDict['Mode_Reserved7']=mode_list[7]
    else:
        valid = False
    strminDict['Valid'] = valid
    return strminDict

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
