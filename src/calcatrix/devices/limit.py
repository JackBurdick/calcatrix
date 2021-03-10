from gpiozero import SmoothedInputDevice


class Limit(SmoothedInputDevice):
    """
    Limit switch -- normally open
    """

    def __init__(
        self,
        name="limit_switch",,
        pin=None,
        pull_up=False,
        active_state=None,
        queue_len=5,
        # sample_rate=100,
        # threshold=0.5,
        partial=False,
        pin_factory=None,
        when_activated=None,
        when_deactivated=None,
    ):
        super().__init__(
            pin,
            pull_up=pull_up,
            active_state=active_state,
            queue_len=queue_len,
            partial=partial,
            pin_factory=pin_factory,
        )
        try:
            self._queue.start()
        except:
            self.close()

        if not isinstance(name, str):
            raise ValueError(
                f"name ({name}) expected to be type {str}, not {type(name)}"
            )
        self.name = name

    @property
    def value(self):
        return super(Hall, self).value

    def __repr__(self):
        return str(self.__class__.__name__) + ": " + f"{self.__dict__}"
