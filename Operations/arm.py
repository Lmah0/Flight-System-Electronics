# Provides functionality to arm and disarm the vehicle.

# Created by: Liam Mah, May 2024

#TODO: Conduct safety checks with physical vehicle [IMPORTANT!]

from pymavlink import mavutil

def arm(vehicle_connection):
    # PROMISES: The vehicle will be armed
    # REQUIRES: Vehicle connection

    vehicle_connection.mav.command_long_send( # Specify COMMAND_LONG
        vehicle_connection.target_system, # Specify vehicle target system
        vehicle_connection.target_component, # Specify the vehicle target component
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, # Specify arm/disarm command
        0, # Confirmation - 0: First transmission of this cmd, 1-255: Confirmation transmissions (e.g. kill)
        1, # Param 1 - Arm/Disarm Control [0: Disarm, 1: Arm]
        0, # Param 2 - Force [0: Arm-disarm unless prevented  by safety checks (i.e. when landed), 21196: Force arm/disarm to override preflight check and disarm during flight]
        0, # Param 3 - Unused, set to zero to populate all 7 parameters
        0, # Param 4 - Unused, set to zero to populate all 7 parameters
        0, # Param 5 - Unused, set to zero to populate all 7 parameters
        0, # Param 6 - Unused, set to zero to populate all 7 parameters
        0 # Param 7 - Unused, set to zero to populate all 7 parameters
    )

    msg = vehicle_connection.recv_match(type='COMMAND_ACK', blocking=True) # Print ACK to confirm successful execution
    print(msg)

def disarm(vehicle_connection):
    # PROMISES: The vehicle will be disarmed
    # REQUIRES: Vehicle connection

    vehicle_connection.mav.command_long_send( # Specify COMMAND_LONG
        vehicle_connection.target_system, # Specify vehicle target system
        vehicle_connection.target_component, # Specify the vehicle target component
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, # Command ID (or enum of command) - In this case, arm/disarm command
        0, # Confirmation - 0: First transmission of this cmd, 1-255: Confirmation transmissions (e.g. kill)
        0, # Param 1 - Arm/Disarm Control [0: Disarm, 1: Arm]
        0, # Param 2 - Force [0: Arm-disarm unless prevented  by safety checks (i.e. when landed), 21196: Force arm/disarm to override preflight checks and disarm during flight]
        0, # Param 3 - Unused, set to zero to populate all 7 parameters
        0, # Param 4 - Unused, set to zero to populate all 7 parameters
        0, # Param 5 - Unused, set to zero to populate all 7 parameters
        0, # Param 6 - Unused, set to zero to populate all 7 parameters
        0 # Param 7 - Unused, set to zero to populate all 7 parameters
    )

    msg = vehicle_connection.recv_match(type='COMMAND_ACK', blocking=True) # Print command ACK to confirm successful execution
    print(msg)
