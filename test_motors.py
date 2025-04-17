import time
from controllers.motor_control import Motor
from controllers.Usb2Comm import Usb2Comm

def test_motors():
    try:
        # Initialize USB communication
        usb_comm = Usb2Comm()
        #usb_comm.connect()
        print("USB communication initialized.")

        # Initialize motors
        pos_motor = Motor(usb_comm, motIdx=2)  # Positional motor
        rot_motor = Motor(usb_comm, motIdx=1)  # Rotational motor

        # # Initialize positional motor
        print("Initializing positional motor...")
        pos_motor.IniMotor(True)
        time.sleep(1)
        print("Positional motor initialized.")

        # Initialize rotational motor
        print("Initializing rotational motor...")
        rot_motor.IniMotor(True)
        time.sleep(1)
        print("Rotational motor initialized.")

        # Test positional motor movement
        print("Testing positional motor...")
        pos_motor.SelectMotor()
        pos_motor.move_z_motor(10, "right")  # Move right by 10 steps
        time.sleep(1)
        pos_motor.move_z_motor(10, "left")  # Move left by 10 steps
        print("Positional motor test completed.")

        # Test rotational motor movement
        print("Testing rotational motor...")
        rot_motor.SelectMotor()
        rot_motor.RotateToPos(90, 5, 500000, 0.1)  # Rotate clockwise by 90 degrees
        time.sleep(1)
        rot_motor.RotateToPos(-90, 5, 500000, 0.1)  # Rotate counterclockwise by 90 degrees
        print("Rotational motor test completed.")

    except Exception as e:
        print(f"Error during motor test: {e}")
    finally:
        # Disconnect USB communication
        if 'usb_comm' in locals():
            # usb_comm.disconnect()
            print("USB communication disconnected.")

if __name__ == "__main__":
    test_motors()