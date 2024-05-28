# Connects to the vehicle and tests heartbeat

# Created by: Liam Mah, May 2024

from pymavlink import mavutil

def verify_connection(vehicle_connection):
    # PROMISES: Vehicle heartbeat will be verified
    # REQUIRES: Vehicle connection
    # Verify vehicle heartbeat

    vehicle_connection.wait_heartbeat()
    print("Heartbeat from system (system %u component %u)" %
        (vehicle_connection.target_system, vehicle_connection.target_component))
    return True

def connect_to_vehicle(port, baudrate):
    # PROMISES: Connection to the vehicle will be established
    # REQUIRES: Vehicle network port
    # Connect to the vehicle

    vehicle_connection = mavutil.mavlink_connection(port, baud=baudrate)
    # valid_connection = verify_connection(vehicle_connection)   
    # return vehicle_connection, valid_connection
    return vehicle_connection