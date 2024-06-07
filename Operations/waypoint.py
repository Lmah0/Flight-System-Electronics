# Allows the aerial vehicle to navigate to a waypoint
# Absolute - Flies to a set of coordinates (latitude, longitude, altitude)
# Relative - Flies to a set of coordinates relative to the home position [NED - north, east, down]

# Created by: Liam Mah, May 2024

from pymavlink import mavutil
import math

def waypoint_progress(vehicle_connection):
    # PROMISES: Prints vehicle positioning updates to terminal
    # REQUIRES: Vehicle connection
    while 1: # Note that if you run this, you will not be able to see live progressions in Mission Planner
        msg = vehicle_connection.recv_match(type='NAV_CONTROLLER_OUTPUT', blocking=True) # Print command ACK to confirm successful execution
        print(msg)

        if msg and msg.wp_dist == 0:
            break

def get_distance_metres(aLocation1, aLocation2):
    """
    Returns the ground distance in metres between two locations.
    This method is an approximation and will not be accurate over large distances and close to the earth's poles.
    """
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5 # Multiply by 111139.5 to convert from lat/lon distance to metres

def has_reached_target(current_pos, target_pos, tolerance=1.0):
    """
    Check if the vehicle has reached the target position within a specified tolerance.
    
    :param current_pos: Current position (latitude, longitude, altitude)
    :param target_pos: Target position (latitude, longitude, altitude)
    :param tolerance: Tolerance in metres
    :return: True if the target position is reached within tolerance, False otherwise
    """
    distance = get_distance_metres(current_pos, target_pos)
    alt_diff = abs(current_pos.alt - target_pos.alt)
    return distance <= tolerance and alt_diff <= tolerance

def wait_for_position(vehicle_connection, target_pos, tolerance=1.0):
    """
    Waits for the vehicle to reach the target position.
    
    :param vehicle_connection: MAVLink connection to the vehicle
    :param target_pos: Target position (latitude, longitude, altitude)
    :param tolerance: Tolerance in metres
    """
    while True:
        msg = vehicle_connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        if msg:
            current_pos = mavutil.mavlink.GLOBAL_POSITION_INT(
                msg.lat / 1e7, msg.lon / 1e7, msg.alt / 1e3)
            if has_reached_target(current_pos, target_pos, tolerance):
                print("Target position reached")
                return

def relative_movement(vehicle_connection, x, y, z):
    # PROMISES: The vehicle will navigate to a waypoint relative to the current position
    # REQUIRES: Vehicle connection, x (front/backwards) [metres], y (left/right) [metres], z (up/down)[metres]
    # Navigate to a waypoint relative to the current position using NED positioning
    vehicle_connection.mav.send(mavutil.mavlink.MAVLink_set_position_target_local_ned_message(
        10, # vehicle_connection: Sender's system time in milliseconds since boot (doesn't really change much I think)
        vehicle_connection.target_system, # System ID of vehicle
        vehicle_connection.target_component, # Component ID of flight controller or just 0
        mavutil.mavlink.MAV_FRAME_LOCAL_NED, # coordinate frame
        int(0b110111111000), # Typemask - Bitmask allowing you to select control fields (in this case, only position - see ArduCopter documentation)
        # Bitmask specs: bit1:PosX, bit2:PosY, bit3:PosZ, bit4:VelX, bit5:VelY, bit6:VelZ, bit7:AccX, bit8:AccY, bit9:AccZ, bit11:yaw, bit12:yaw rate
        x, # Front and backwards movement [+ is North/forwards, - is South/backwards] (in metres)
        y, # Sideways movement [+ is East/right, - is West/left] (in metres)
        z, # Vertical movement [+ is down, - is up] (in metres)
        0, # vx: Ignore for now - controls X velocity in m/s [Specified in typemask]
        0, # vy: Ignore for now - controls Y velocity in m/s [Specified in typemask]
        0, # vz: Ignore for now - controls Z velocity in m/s [Specified in typemask]
        0, # afx: Ignore for now - controls X acceleration in m/s^2
        0, # afy: Ignore for now - controls y acceleration in m/s^2
        0, # afz: Ignore for now - controls z acceleration in m/s^2
        0, # yaw: Ignore for now - controls yaw/heading in radians (with 0 being North/forwards)
        0 # yaw rate: Ignore for now - yaw rate in rad/s
    ))

    # waypoint_progress(vehicle_connection) # Comment out if you want to see live updates in Mission Planner

def absolute_movement(vehicle_connection, latitude, longitude, altitude):
    # PROMISES: The vehicle will navigate to a waypoint absolute to the current position
    # REQUIRES: Vehicle connection, latitude, longitude, altitude
    # Navigate to a waypoint at a set of coordinates using global positioning
    vehicle_connection.mav.send(mavutil.mavlink.MAVLink_set_position_target_global_int_message(
        10, # vehicle_connection: Sender's system time in milliseconds since boot (doesn't really change much I think)
        vehicle_connection.target_system, # System ID of vehicle
        vehicle_connection.target_component, # Component ID of flight controller or just 0
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, # coordinate frame
        int(0b110111111000), # Typemask - Bitmask allowing you to select control fields (in this case, only position - see ArduCopter documentation)
        # Bitmask specs: bit1:PosX, bit2:PosY, bit3:PosZ, bit4:VelX, bit5:VelY, bit6:VelZ, bit7:AccX, bit8:AccY, bit9:AccZ, bit11:yaw, bit12:yaw rate
        int(latitude * 10 ** 7), # Latitude * 1e7
        int(longitude * 10 ** 7), # Longitude * 1e7
        altitude, # Altitude (in metres) above home [DOES NEED TO BE POSITIVE]
        0, # vx: Ignore for now - controls X velocity in m/s [Specified in typemask]
        0, # vy: Ignore for now - controls Y velocity in m/s [Specified in typemask]
        0, # vz: Ignore for now - controls Z velocity in m/s [Specified in typemask]
        0, # afx: Ignore for now - controls X acceleration in m/s^2
        0, # afy: Ignore for now - controls y acceleration in m/s^2
        0, # afz: Ignore for now - controls z acceleration in m/s^2
        0, # yaw: Ignore for now - controls yaw/heading in radians (with 0 being North/forwards)
        0 # yaw rate: Ignore for now - yaw rate in rad/s
    ))
    if True: # Comment out if it fails during flight testing.
        target_pos = mavutil.mavlink.GLOBAL_POSITION_INT(latitude, longitude, altitude)
        wait_for_position(vehicle_connection, target_pos)

