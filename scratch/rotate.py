from time import sleep
import RPi.GPIO as GPIO  # pylint: disable=import-error
from calcatrix.devices.rotate import Rotator  # pylint: disable=import-error

if __name__ == "__main__":

    deg = 35

    GPIO.setmode(GPIO.BCM)
    cur_pins = [21, 20, 16, 12]
    m = Rotator(cur_pins)
    m.rpm = 5
    print(f"Pause in seconds: {m._T}")
    m.move_to(deg)
    sleep(1)
    m.move_to(360 - deg)
    sleep(1)
    m.move_to(0)
    sleep(1)
    GPIO.cleanup()
