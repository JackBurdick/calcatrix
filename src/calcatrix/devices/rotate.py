from time import sleep

import RPi.GPIO as GPIO  # pylint: disable=import-error


class Rotator(object):
    def __init__(self, pins):
        """Rotator, Half step
        inspired by http://blog.scphillips.com/
        """
        GPIO.setmode(GPIO.BCM)
        # set pins
        if not isinstance(pins, list):
            raise TypeError(f"pins is expected to be type {list}, not {type(pins)}")
        else:
            assert len(pins) == 4, ValueError(
                f"pins is expected to have 4 values, not {len(pins)}"
            )
        self.P1 = pins[0]
        self.P2 = pins[1]
        self.P3 = pins[2]
        self.P4 = pins[3]

        self.deg_per_step = 5.625 / 64
        self.steps_per_rev = int(360 / self.deg_per_step)  # 4096

        # TODO: set home, presently it is assumed init position is home
        self.step_angle = 0  # Assume the way it is pointing is zero degrees

        # set pins
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)

        self.rpm = 5

    def _set_rpm(self, rpm):
        """Set the turn speed in RPM."""
        self._rpm = rpm
        # _T is the amount of time to stop between signals
        self._T = (60.0 / rpm) / self.steps_per_rev

    rpm = property(lambda self: self._rpm, _set_rpm)

    def move_to(self, angle):
        """Take the shortest route to a particular angle (degrees)."""
        # Make sure there is a 1:1 mapping between angle and stepper angle
        # TODO: 8*n where n = n/8 ??
        target_step_angle = 8 * (int(angle / self.deg_per_step) / 8)
        steps = target_step_angle - self.step_angle
        steps = steps % self.steps_per_rev
        if steps > self.steps_per_rev / 2:
            steps -= self.steps_per_rev
            self._move_acw(-steps // 8)
        else:
            print(f"moving {steps} steps")
            self._move_cw(steps // 8)
        self.step_angle = target_step_angle

        # clear
        self.__clear()

    def __clear(self):
        GPIO.output(self.P1, 0)
        GPIO.output(self.P2, 0)
        GPIO.output(self.P3, 0)
        GPIO.output(self.P4, 0)

    def _move_acw(self, big_steps):
        self.__clear()
        for _ in range(int(big_steps)):
            GPIO.output(self.P1, 0)
            sleep(self._T)
            GPIO.output(self.P3, 1)
            sleep(self._T)
            GPIO.output(self.P4, 0)
            sleep(self._T)
            GPIO.output(self.P2, 1)
            sleep(self._T)
            GPIO.output(self.P3, 0)
            sleep(self._T)
            GPIO.output(self.P1, 1)
            sleep(self._T)
            GPIO.output(self.P2, 0)
            sleep(self._T)
            GPIO.output(self.P4, 1)
            sleep(self._T)

    def _move_cw(self, big_steps):
        self.__clear()
        for _ in range(int(big_steps)):
            GPIO.output(self.P3, 0)
            sleep(self._T)
            GPIO.output(self.P1, 1)
            sleep(self._T)
            GPIO.output(self.P4, 0)
            sleep(self._T)
            GPIO.output(self.P2, 1)
            sleep(self._T)
            GPIO.output(self.P1, 0)
            sleep(self._T)
            GPIO.output(self.P3, 1)
            sleep(self._T)
            GPIO.output(self.P2, 0)
            sleep(self._T)
            GPIO.output(self.P4, 1)
            sleep(self._T)
