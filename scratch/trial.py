from calcatrix import LinearDevice

DIR_PIN = 27
STEP_PIN = 17
LOC_PIN = 24
ENABLE_PIN = 22
BOUND_A_PIN = 23
BOUND_B_PIN = 25
init_config = {
    "stepper": {"dir": DIR_PIN, "step": STEP_PIN, "enable": ENABLE_PIN},
    "location": {
        "marker": {"pin": LOC_PIN},
        "bound_a": {"pin": BOUND_A_PIN},
        "bound_b": {"pin": BOUND_B_PIN},
    },
}
ld = LinearDevice(init_config=init_config)

# r_steps = 500
# l_steps = 550

ld.set_home()

print(ld)

# ld.move_direction(l_steps, True)
# time.sleep(0.3)
# ld.move_direction(r_steps, False)
