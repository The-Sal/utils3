import os
import time
from pathlib import Path
DISABLED_PLOT = False


class PrimitivePlotWriter:
    """Base class for plot writers that handles file operations and primitive x,y writing."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create the file if it doesn't exist."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.reset()

    def write_xy(self, x: float, y: float):
        """Write an x,y coordinate pair."""
        if not DISABLED_PLOT:
            with open(self.file_path, "a") as file:
                file.write(f"{x},{y}\n")
                file.flush()

    def reset(self):
        """Clear file."""
        with open(self.file_path, "w") as file:
            file.write("clear\n")


class SimplePlotWriter(PrimitivePlotWriter):
    """Simple API to write y values with auto-incrementing x."""

    def __init__(self, file_path: str = None):
        if file_path is None:
            file_path = "{}/Library/Containers/SVO-Productions.plotview/Data/tmp/plot.plt".format(os.path.expanduser("~"))
        super().__init__(file_path)
        self.x = 0

    def write(self, y: float):
        """Write a y value. X automatically increments."""
        if not DISABLED_PLOT:
            self.write_xy(self.x, y)
            self.x += 1

    def reset(self):
        """Clear file and reset x to 0."""
        super().reset()
        self.x = 0


# # Example usage
if __name__ == "__main__":
    writer = SimplePlotWriter()

    writer.reset()
    time.sleep(1)

    # Write some points
    writer.write(50)  # x=0, y=50
    writer.write(75)  # x=1, y=75
    writer.write(25)  # x=2, y=25

    # Reset when needed
    # writer.reset()  # Clears file, x back to 0

    # Write more points
    writer.write(60)  # x=0, y=60