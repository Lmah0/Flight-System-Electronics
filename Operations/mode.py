# Switches the current flight mode

# Created by: Liam Mah, May 2024

from pymavlink import mavutil

# Some flight mode IDs...
# 0 - Stabilize
# 3 - Loiter
# 6 - RTL (Return to Launch)
# 15 - Guided (Autonomous Mode)

def set_mode(vehicle_connection, mode_id):
    # PROMISES: The vehicle will switch to the specified flight mode
    # REQUIRES: Vehicle connection, mode ID
    vehicle_connection.mav.command_long_send( # Specify COMMAND_LONG
        vehicle_connection.target_system, # Specify target system
        vehicle_connection.target_component, # Specify target component
        mavutil.mavlink.MAV_CMD_DO_SET_MODE, # Command ID (or enum of command) - Set mode command
        0, # Confirmation - 0: First transmission of this cmd, 1-255: Confirmation transmissions (e.g. kill)
        217, # Param 1 - MAV_MODE_FLAG_CUSTOM_MODE_ENABLED=1 (Enable custom mode identification)
        mode_id, # Param 2 - Flight mode number
        0, # Param 3 - Unused, set to zero to populate all 7 parameters
        0, # Param 4 - Unused, set to zero to populate all 7 parameters
        0, # Param 5 - Unused, set to zero to populate all 7 parameters
        0, # Param 6 - Unused, set to zero to populate all 7 parameters
        0 # Param 7 - Unused, set to zero to populate all 7 parameters
    )

    msg = vehicle_connection.recv_match(type='COMMAND_ACK', blocking=True) # Print command ACK to confirm successful execution
    print(msg)