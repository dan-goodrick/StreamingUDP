from datetime import date
import time

def get_checksum(string, num_digits=3):
    return abs(hash(string)) % (10 ** num_digits)

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

if __name__ == "__main__":
    from pprint import pprint
    import json

    with open('tx.json') as f:
        data = json.load(f)
        msg = BuildStreamingUDP(data)
        print(msg)
        msg_dict = ParseStreamingUDP(msg)
        pprint(msg_dict)
