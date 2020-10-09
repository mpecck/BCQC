from bcqc_with_qdt.emulators.quality_controller_emulator import QualityController

from random import randint
import json
import requests


headers = {
    'Content-Type': "application/json",
}


class Workcell(QualityController):
    def __init__(
            self,
            step_idx,
            id,
            ip,
            port,
            qc_id=None,
            consensus_mode="confidence",
            threshold=0.9,
            score=0.1,
            capability=randint(1, 10)/10,
            learning=True):
        # Remove if workcell != qc
        super().__init__(
            id=id,
            ip=ip,
            port=port,
            consensus_mode=consensus_mode,
            threshold=threshold,
            score=score,
            capability=capability,
            learning=learning
        )
        self.id = id
        self.dedicated_node_id = qc_id
        self.dedicated_node_address = f'http://{ip}:{port}/{qc_id}'
        self.step_idx = step_idx
        self.production_workpiece = None
        self.production_time = 0

    def add_to_production(self, workpiece):
        self.production_workpiece = workpiece

    def start_production(self, worksheet_df=None, production_time=None):
        self.production_workpiece.status = "in production"
        self.production_workpiece.step_idx = self.step_idx
        if worksheet_df is not None:
            self.production_time = self.get_production_time(worksheet_df)
        elif production_time is not None:
            self.production_time = production_time
        else:
            raise ValueError("Insufficient data. Please input either worksheet_df or production_time.")
        self.production_workpiece.count_down = self.production_time

    def in_production(self, time_interval):
        self.production_workpiece.count_down += -1*time_interval
        if self.production_workpiece.count_down <= 0:  # count down completed, finished production
            return False
        else:   # still in production
            return True

    def end_production(self, worksheet_df):
        accepted = False    # place holder
        if self.production_workpiece.actual_quality is None:
            actual_quality = self.render_actual_quality(worksheet_df)
            self.production_workpiece.actual_quality = actual_quality
        else:   # Not none, production ended but haven't passed to qc
            actual_quality = self.production_workpiece.actual_quality
        execution_info = {
            "step_idx": self.step_idx,
            "production_time": self.production_time,
            "produced_by": self.id,
            "min_qc_required": len(actual_quality) + 1
        }
        if self.dedicated_node_id is not None:
            accepted = self.pass_to_quality_controller(execution_info)  # dedicated qc initiates inspection
        if accepted:
            self.production_workpiece.status = "awaiting inspection"
            self.production_workpiece.source = self.id  # ready to transport
            self.production_workpiece.count_down = 0  # reset
            self.production_workpiece = None    # reset
        return execution_info, actual_quality

    def render_actual_quality(self, worksheet_df):
        """
        Generate the actual quality of the assembled product.
        Returns a dictionary of percentage each possible state could appear.
        """
        total_weights = 100
        possible_states = worksheet_df.loc[worksheet_df['Step'] == self.step_idx].Possible_State.to_list()
        quality = dict()
        for state in possible_states[:-1]:
            weight = randint(0, total_weights)
            quality[state] = weight
            total_weights += - weight
        # assign remaining weights to the last state
        quality[possible_states[-1]] = total_weights
        return quality

    def get_production_time(self, worksheet_df):
        """
        Determines the production time for a step between the given upper and lower bound in the excel for a given step
        :param step: manufacturing process
        :return: production time
        """
        time_min = worksheet_df.loc[worksheet_df['Step'] == self.step_idx].Production_Time_Min.iloc[0]
        time_max = worksheet_df.loc[worksheet_df['Step'] == self.step_idx].Production_Time_Max.iloc[0]
        production_time = randint(time_min, time_max)
        return production_time

    def pass_to_quality_controller(self, execution_info):
        payload = {
            "qc_list": list(),
            "workpiece_id": self.production_workpiece.id,
            "execution_info": execution_info
        }
        address = f"{self.dedicated_node_address}/inspection"
        res = requests.post(address, data=json.dumps(payload), headers=headers)
        if res.status_code == 202:
            self.production_workpiece.source = self.id
            self.production_workpiece.sink = self.dedicated_node_id
            return True
        else:   # 303
            return False

