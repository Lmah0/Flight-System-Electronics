# Triggers the vehicle to takeoff to a specified altitude.
# REQUIRES: Vehicle to be armed and in Guided mode.

from pymavlink import mavutil

def takeoff(vehicle_connection, takeoff_height):
    # PROMISES: The vehicle will takeoff to the specified height
    # REQUIRES: Vehicle connection, takeoff height
    vehicle_connection.mav.command_long_send( # Specify COMMAND_LONG 
        vehicle_connection.target_system, # Specify target system
        vehicle_connection.target_component, # Specify target component
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, # Command ID (or enum of command) - Takeoff command
        0, # Confirmation - 0: First transmission of this cmd, 1-255: Confirmation transmissions (e.g. kill)
        0, # Param 1 - Pitch/Climb Angle (Plane only; set to 0 since this is tuned for copter mode)
        0, # Param 2 - Empty
        0, # Param 3 - Empty
        0, # Param 4 - Yaw angle (ignored if no compass present): Unused, set to zero
        0, # Param 5 - Latitude (set to zero to use current latitude)
        0, # Param 6 - Longitude (set to zero to use current longitude)
        takeoff_height # Param 7 - Height to ascend to (in metres)
    )

    msg = vehicle_connection.recv_match(type='COMMAND_ACK', blocking=True) # Print command ACK to confirm successful execution
    print(msg)