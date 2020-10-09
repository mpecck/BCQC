class Workpiece:
    def __init__(self, id):
        self.id = id
        # self.status = "awaiting production"
        self.status = "awaiting next step"
        self.actual_quality = None
        self.source = None
        self.sink = None
        self.location = "wc_0"   # Starting point. Location refers to workcell id.
        self.step_idx = None
        self.pos = None
        self.count_down = 0


