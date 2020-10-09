class Transporter:
    def __init__(self):
        self.pos_dict = {  # order along belt, belt no.
            "wc_0": (1, 1),
            "wc_1": (2, 1),
            "wc_2": (3, 1),
            "wc_3": (4, 1),
            "wc_4": (5, 1),
            "wc_5": (6, 1),
            "wc_6": (1, 2),
            "wc_7": (2, 2),
            "wc_8": (3, 2),
            "wc_9": (4, 2),
            "wc_10": (5, 2),
            "wc_11": (6, 2),
            "wc_12": (1, 3),
            "wc_13": (2, 3),
            "wc_14": (3, 3),
            "wc_15": (4, 3),
            "wc_16": (5, 3),
            "wc_17": (6, 3),
        }
        self.belt_velocity = 0.05
        self.splitter_delay = 1

    def start_travel(self, workpiece):
        workpiece.location = None   # reset
        source = workpiece.source
        sink = workpiece.sink
        travel_dist, splitter = self.estimate_travel_distance(source, sink)
        travel_time = self.estimate_travel_time(travel_dist, splitter)
        workpiece.count_down = travel_time
        return travel_time, travel_dist, splitter

    def in_travel(self, workpiece, time_interval):
        workpiece.count_down += -1*time_interval
        if workpiece.count_down <= 0:  # count down completed, finished transportation
            return False
        else:   # still in transportation
            return True

    def end_travel(self, workpiece):
        workpiece.location = workpiece.sink
        workpiece.count_down = 0    # reset
        workpiece.source = None     # reset
        workpiece.sink = None     # reset

    def estimate_travel_distance(self, source, sink):
        travel_dist = 0
        splitter = 0
        source_pos = self.pos_dict[source]
        sink_pos = self.pos_dict[sink]
        num_of_belt = sink_pos[1] - source_pos[1]     # -ve is to the left; +ve is to the right
        if num_of_belt == 0:   # same belt
            local_dist = sink_pos[0] - source_pos[0]
            if local_dist < 0:  # sink order is behind source order
                travel_dist += local_dist + 6
                if source_pos[0] >= 4 and sink_pos[0] >= 4:     # sink and source on the same side
                    splitter += 2
                if source_pos[0] <= 3 and sink_pos[0] <= 3:     # sink and source on the same side
                    splitter += 2
                else:   # sink and source on different side
                    splitter += 1
        else:
            travel_dist += abs(num_of_belt)*2 - 1
            if num_of_belt < 0:    # different belt to the left
                if source_pos[0] >= 4:  # source on right side of belt
                    travel_dist += 6 - source_pos[0]
                    splitter += 1
                    travel_dist += 1 + 3
                elif source_pos[0] <= 3:  # source on left side of belt
                    travel_dist += 4 - source_pos[0] + 1
                if sink_pos[0] >= 4:    # sink on right side of belt
                    travel_dist += 6 + sink_pos[0] + 1
                    splitter += 1
                elif sink_pos[0] <= 3:    # sink on left side of belt
                    splitter += 1
                    travel_dist += 6 - 4 + sink_pos[0] + 1
                    splitter += 1
            elif num_of_belt > 0:    # different belt to the right
                if source_pos[0] >= 4:  # source on right side of belt
                    travel_dist += 6 - source_pos[0] + 1
                elif source_pos[0] <= 3:  # source on left side of belt
                    travel_dist += 3 - source_pos[0]
                    splitter += 1
                    travel_dist += 3 + 1
                if sink_pos[0] >= 4:    # sink on right side of belt
                    splitter += 1
                    travel_dist += sink_pos[0]
                    splitter += 1
                elif sink_pos[0] <= 3:    # sink on left side of belt
                    splitter += 1
                    travel_dist += sink_pos[0]
        return travel_dist, splitter

    def estimate_travel_time(self, travel_dist, splitter):
        travel_time = 0
        travel_time += travel_dist / self.belt_velocity
        travel_time += splitter / self.splitter_delay
        return travel_time


class ConveyorBelt:
    def __init__(self):
        """
        Row numbering starts from top row.
        Column numbering starts from left column.
        Direction is indexed by: 1 up, 2 right, 3 down, 4 left
        """
        self.workcell_pos_dict = {  # pos = (row, column)
            1: (2, 1),
            2: (3, 1),
            3: (3, 2),
            4: (2, 2),
            5: (1, 2),
            6: (1, 3),
            7: (2, 3),
            8: (3, 3),
            9: (3, 4),
            10: (2, 4),
            11: (1, 4),
            12: (1, 5),
            13: (2, 5),
            14: (3, 5),
            15: (3, 6),
            16: (2, 6),
            17: (1, 6),
        }
        self.splitter_dict = {  # pos: dir --> pos = (row, column); dir = (original, split)
            (0.6, 1.4): (2, 3),
            (3.2, 1.4): (3, 2),
            (0.8, 1.8): (1, 4),
            (3.4, 1.8): (4, 1),
            (0.6, 3.4): (2, 3),
            (3.2, 3.4): (3, 2),
            (0.8, 3.8): (1, 4),
            (3.4, 3.8): (4, 1),
            (0.6, 5.4): (2, 3),
            (3.2, 5.4): (3, 2),
            (0.8, 5.8): (1, 4),
            (3.4, 5.8): (4, 1),
        }

    def program_splitter_dir(self, pos, source, sink):
        dir_options = self.splitter_dict[pos]
        if sink[1] - 1 > pos[1] > sink[1] + 1:   # if splitter is in the column range of sink
            if sink[1] > pos[1] > sink[1] + 0.5 or sink[1] + 0.5 > pos[1] > sink[1]:  # if splitter is on sink column
                pass
            else:   # if splitter is on the opposite belt of sink column
                if source[1] > sink[1]:  # sink column on left of source column
                    if dir_options[1] == 3:     # splitter has option to turn down
                        dir = dir_options[1]
                        split = True
                    else:   # keep to original direction
                        dir = dir_options[0]
                        split = False
                else:  # sink column on right of source column
                    if dir_options[1] == 1:     # splitter has option to turn up
                        dir = dir_options[1]
                        split = True
                    else:   # keep to original direction
                        dir = dir_options[0]
                        split = False
        else:   # if splitter is not in the same column as sink
            if source[1] > sink[1]:  # sink column on left of source column
                if dir_options[1] == 4:     # splitter has option to turn left
                    dir = dir_options[1]
                    split = True
                else:   # keep to original direction
                    dir = dir_options[0]
                    split = False
            else:  # sink column on right of source column
                if dir_options[1] == 2:     # splitter has option to turn right
                    dir = dir_options[1]
                    split = True
                else:   # keep to original direction
                    dir = dir_options[0]
                    split = False
        return dir, split

    def get_belt_dir(self, pos):
        """
        Direction is indexed by: 1 up, 2 right, 3 down, 4 left
        :param pos:
        :return:
        """
        if pos[0] == 0.6:
            dir = 2
        elif pos[0] == 3.4:
            dir = 4
        else:
            if 1 <= pos[1] < 1.5 and 3 <= pos[1] < 3.5 and 5 <= pos[1] < 5.5:
                dir = 3
            elif 1.5 <= pos[1] < 2 and 3.5 <= pos[1] < 4 and 5.5 <= pos[1] < 6:
                dir = 1

    @staticmethod
    def move_up(pos):
        pos[0] += -0.2
        return pos

    @staticmethod
    def move_down(pos):
        pos[0] += 0.2
        return pos

    @staticmethod
    def move_right(pos):
        pos[1] += 0.2
        return pos

    @staticmethod
    def move_left(pos):
        pos[1] += -0.2
        return pos


