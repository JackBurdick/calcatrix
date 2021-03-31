from gpiozero import Device
from gpiozero.pins.native import NativeFactory

from calcatrix.devices.hall import Hall
from calcatrix.devices.limit import Limit
from calcatrix.devices.stepper import Stepper

Device.pin_factory = NativeFactory()


class LinearDevice:
    """treader cart"""

    def __init__(
        self,
        # init params
        init_config,
        name="linear",
    ):
        self.name = name
        self.stepper = Stepper(init_config["stepper"], name="step")
        self.marker = Hall(**init_config["location"]["marker"], name="marker")
        self.bound_a = Limit(**init_config["location"]["bound_a"], name="a")
        self.bound_b = Limit(**init_config["location"]["bound_b"], name="b")

        self.cur_location = None
        self.dir_dict = {}

        # TODO: const by hardware
        self.max_steps = 500
        self.backoff_steps = 40
        self.pulses_per_step = 10

        self.sequence_tolerance = 10

        # 'average' Location of the markers, is set on the set_home() sequence
        self.positions = None

        # self.set_home()

    def at_location(self):
        return self.marker.value

    def _find_seqs_with_tol(self, positions, tolerance=1):
        # https://stackoverflow.com/questions/2361945/detecting-consecutive-integers-in-a-list
        # drop duplicates (shouldn't be present) + ensure sort
        positions = sorted(set(positions))
        gaps = [[s, e] for s, e in zip(positions, positions[1:]) if s + tolerance < e]
        edges = iter(positions[:1] + sum(gaps, []) + positions[-1:])
        return list(zip(edges, edges))

    def _obtain_average_from_seq(self, l, lt):
        positions = {}
        for i, inds in enumerate(lt):
            # NOTE: will round down, e.g. 123.5 --> 123
            avg = int((inds[0] + inds[1]) / 2)
            positions[i] = avg
        return positions

    def _obtain_positions(self, l, tolerance=1):
        lt = self._find_seqs_with_tol(l, 2)
        pos = self._obtain_average_from_seq(l, lt)
        return pos

    def set_home(self):
        # move one direction
        print("moving True")
        o_t = self._move_to_bound(True)
        if o_t[0]:
            home_name = "a"
        else:
            home_name = "b"
        self.dir_dict[home_name] = {"direction": True, "location": 0}

        print("moving other")
        # move the other + and collect marker locations along the way
        o_f = self._move_to_bound(False, collect_markers=True, prev_bound=home_name)
        if o_f[0]:
            end_name = "a"
        else:
            end_name = "b"
        self.dir_dict[end_name] = {"direction": True, "location": o_f[2]}

        # ensure each direction uses a different sensor
        if home_name == end_name:
            raise ValueError("bounds appear to share same sensor")

        # override max_steps
        self.max_steps = o_f[2]

        if self.marker.activations:
            self.positions = self._obtain_positions(
                self.marker.activations, self.sequence_tolerance
            )

    def _backoff_bound(self, cur_direction):
        opp_direction = not cur_direction
        for _ in range(self.backoff_steps):
            self.stepper.step_direction(opp_direction)
            # TODO: ensure backoff

    def _move_to_bound(self, direction, collect_markers=False, prev_bound=None):
        cur_step = 0
        self.stepper.enable_pin.off()
        try:
            while cur_step < self.max_steps:
                self.stepper.step_direction(direction)
                cur_step += 1
                if cur_step % self.pulses_per_step == 0:
                    # TODO: this logic can likely be improved
                    if self.bound_a.value or self.bound_b.value:
                        if prev_bound is not None:
                            if prev_bound == "a":
                                if self.bound_b.value:
                                    print("AT BOUND 2 (B)")
                                    self._backoff_bound(direction)
                                    break
                            else:
                                if self.bound_a.value:
                                    print("AT BOUND 2 (A)")
                                    self._backoff_bound(direction)
                                    break
                        else:
                            print("AT BOUND 1")
                            self._backoff_bound(direction)
                            break
                    else:
                        if collect_markers:
                            if self.marker.value:
                                self.marker.activations.append(cur_step)
                    
            if cur_step >= self.max_steps:
                raise ValueError("Did not find bounds in max allowed step")
        finally:
            self.stepper.enable_pin.on()

        return (self.bound_a.value, self.bound_b.value, cur_step)

    def move_direction(self, num_steps, direction):
        # turn stepper enable_pin off at start and on at end (opposite logic)
        self.stepper.enable_pin.off()
        cur_step = 0
        try:
            while cur_step <= num_steps:
                cur_step += 1
                self.stepper.step_direction(direction)
                if cur_step % self.pulses_per_step == 0:
                    if self.at_location():
                        print(f"stop - location: {cur_step}")
                        break
        finally:
            self.stepper.enable_pin.on()

    def __repr__(self):
        return str(self.__class__.__name__) + ": " + f"{self.__dict__}"
