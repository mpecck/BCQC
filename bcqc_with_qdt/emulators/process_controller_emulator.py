from random import shuffle


class ProcessController:
    def __init__(self, workpiece_id):
        self.id = workpiece_id
        self.pre_conditions = {
            1: [None],
            2: [1],
            3: [1],
            4: [1],
            5: [2, 3, 4],
            6: [5],
            7: [6],
            8: [6],
            9: [6],
            10: [6],
            11: [6],
            12: [7, 8, 9, 10, 11],
            13: [12],
            14: [13],
            15: [13],
            16: [13],
            17: [14, 15, 16],
        }
        self.step_idx_status = {    # true is completed
            None: True,
            1: False,
            2: False,
            3: False,
            4: False,
            5: False,
            6: False,
            7: False,
            8: False,
            9: False,
            10: False,
            11: False,
            12: False,
            13: False,
            14: False,
            15: False,
            16: False,
            17: False,
        }
        self.post_conditions = {
            1: ["Pass"],
            2: ["Pass"],
            3: ["Pass"],
            4: ["Pass"],
            5: ["Pass"],
            6: ["Pass"],
            7: ["Pass"],
            8: ["Pass"],
            9: ["Pass"],
            10: ["Pass"],
            11: ["Pass"],
            12: ["Pass"],
            13: ["Pass"],
            14: ["Pass"],
            15: ["Pass"],
            16: ["Pass"],
            17: ["Pass"],
        }

    def get_next_step_idx(self, workpiece, workcells):
        step_idx = None
        sink_id = None
        step_idx_list = [
            step_idx
            for step_idx, pre_condition in self.pre_conditions.items()
            if all(self.step_idx_status[pre_step_idx] for pre_step_idx in pre_condition)
               and not self.step_idx_status[step_idx]
        ]
        if len(step_idx_list) != 0:  # if there are possible steps
            shuffle(step_idx_list)
            print(f"        Possible steps {step_idx_list}.")
            for step_idx in step_idx_list:
                possible_sink_ids = [
                    wc_id
                    for wc_id, wc_inst in workcells.items()
                    if wc_inst.step_idx == step_idx and wc_inst.production_workpiece is None
                ]
                if len(possible_sink_ids) != 0:     # if no workcell is available
                    sink_id = possible_sink_ids[0]  # todo: find the nearest workcell
                    break
        if sink_id is not None:
            workpiece.step_idx = step_idx
            workpiece.source = workpiece.location
            workpiece.sink = sink_id
            workpiece.status = "awaiting production"
            workcells[sink_id].production_workpiece = workpiece.id
        return step_idx_list, step_idx, sink_id

    def update_step_status(self, step_idx, state_list):
        print(self.post_conditions[step_idx])
        if state_list == self.post_conditions[step_idx]:
            self.step_idx_status[step_idx] = True
        else:
            self.step_idx_status[step_idx] = False

    def update_workpiece_completion(self, workpiece):
        if all(status for step_idx, status in self.step_idx_status.items()):
            workpiece.status = "completed"

