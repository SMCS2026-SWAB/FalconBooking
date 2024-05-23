class Booking:
    """Represents a single booking made by a teacher for a study room."""

    AVAILABLE_PERIODS = ["Pd. 1", "Pd. 2", "Pd. 3", "Pd. 4", "Pd. 5", "Pd. 6", "Pd. 7", "Pd. 8", "Lunch"]

    def __init__(self, periods_free: list):
        self.periods_free = periods_free
        self.availability = int(
            (len(self.AVAILABLE_PERIODS) - len(self.periods_free)) / len(self.AVAILABLE_PERIODS) * 100
        )
