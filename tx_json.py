import json
data = {
        'Version': '1.0',
        'Type': 'CMD',
        'Name':'not_set',
        'Session': '0',
        'Sequence': 0,
        'Steering': 0,
        'Throttle': 0,
        'Brake': 100,
        'Trans': 1,
        'Velocity': 0,
        'State_Estop': 0,
        'State_Paused': 1,
        'State_Manual': 0,
        'State_Enable': 0,
        'State_L1': 0,
        'State_L2': '',
        'State_Motion': '',
        'State_Reserved7': '',
        'Process_Operation': 0,
        'Process_Shutdown': 0,
        'Process_Start': 0,
        'Process_SteeringCal': 0,
        'Process_TransShift': 0,
        'Process_Reserved5': '',
        'Process_Reserved6': '',
        'Process_Reserved7': '',
        'Mode_ProgressiveSteeringDisable': 0,
        'Mode_ProgressiveBrakingDisable': 0,
        'Mode_VelocityControlEnable': 0,
        'Mode_Reserved3': '',
        'Mode_Reserved4': '',
        'Mode_Reserved5': '',
        'Mode_Reserved6': '',
        'Mode_Reserved7': ''
        }
with open('tx.json', 'w') as outfile:
    json.dump(data, outfile)
