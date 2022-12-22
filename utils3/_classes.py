class Process:
    """A class that represents a process"""
    def __init__(self,
                 owner: str,
                 pid: int,
                 cpu_percent: float,
                 memory_percent: float,
                 cmd: str):
        self.owner = owner
        self.pid = int(pid)
        self.cpu_percent = cpu_percent
        self.memory_percent = memory_percent
        self.cmd = cmd
