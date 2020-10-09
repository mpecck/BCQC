from bcqc_with_qdt.emulators.belt_emulator import Transporter

from ast import literal_eval
from collections import Counter
from flask import request, jsonify
from numpy import prod
from threading import Thread
from time import time
from random import choices, randint, shuffle
import hashlib  # the library to encrypt a block has value
import json
import requests


headers = {
    'Content-Type': "application/json",
}


class QualityController:
    def __init__(
            self,
            id,
            ip,
            port,
            consensus_mode="confidence",
            threshold=0.9,
            score=0.1,
            capability=randint(1, 10)/10,
            learning=True):
        """
        self.inspection_results = {
            <workpiece_id>: {
                <qc_id>: {
                    "results": <results>,
                    "score": <score>
                }
            }
        }
        self.blockchain_dict = {
            <workpiece_id>: <blockchain instance>
        }
        :param step_idx:
        :param id:
        :param consensus_mode:
        :param threshold:
        """
        self.id = id    # this is node_id
        self.capability = capability
        self.in_qc_counter = 0
        self.in_winner_counter = 0
        self.inspection_workpiece = None
        self.inspection_results = dict()
        self.inspection_time = 0
        self.consensus_mode = consensus_mode
        self.score = self.check_score_validity(score)    # initial score
        self.threshold = self.check_threshold_validity(threshold)
        self.learning = learning
        self.qc_list = list()
        self.nodes = dict()
        self.address = f'http://{ip}:{port}/{id}'
        self.blockchain_dict = dict()
        self.transporter = Transporter()

    def check_score_validity(self, score):
        if self.consensus_mode == "confidence":
            if score < 0 or score > 1:
                raise ValueError("Score must be between 0 to 1 for confidence mode.")
            return score
        elif self.consensus_mode == "majority":
            if not isinstance(score, int):
                if not score.is_integer():
                    raise TypeError("Threshold must be positive whole number.")
            return score

    def check_threshold_validity(self, threshold):
        if self.consensus_mode == "confidence" and (threshold > 1 or threshold < 0):
            raise ValueError("Threshold must be between 0 to 1 for confidence mode.")
        elif self.consensus_mode == "majority" and isinstance(threshold, float) and threshold < 0:
            raise TypeError("Threshold must be positive whole number.")
        else:
            return threshold

    def register_nodes(self, nodes):
        self.nodes.update(nodes)    # add dict to nodes dict

    def register_workpiece(self, workpiece_id):
        self.blockchain_dict[workpiece_id] = Blockchain(
            id=workpiece_id,
            threshold=self.threshold,
            consensus_mode=self.consensus_mode
        )
        self.inspection_results[workpiece_id] = dict()  # initialize

    def add_to_inspection(self, workpiece):
        self.inspection_workpiece = workpiece
        self.inspection_results[workpiece.id] = dict()  # reset

    def start_inspection(self, step_idx, worksheet_df=None, inspection_time=None):
        if not self.blockchain_dict.get(self.inspection_workpiece.id, False):  # register blockchain if workpiece is new
            self.register_workpiece(self.inspection_workpiece.id)
        self.inspection_workpiece.status = "in inspection"
        if worksheet_df is not None:
            _ = self.get_inspection_time(step_idx, worksheet_df)   # update self.inspection_time
        elif inspection_time is not None:
            self.inspection_time = inspection_time
        else:
            raise ValueError("Insufficient data. Please input either worksheet_df or inspection_time.")
        self.inspection_workpiece.count_down = self.inspection_time

    def in_inspection(self, time_interval):
        self.inspection_workpiece.count_down += -time_interval
        if self.inspection_workpiece.count_down <= 0:  # count down completed, finished inspection
            return False
        else:  # still in inspection
            return True

    def end_inspection(self, execution_info=None, inspection_results=None):
        network_time = 0
        _ = self.inspect_workpiece(state_list=inspection_results)
        inspection_time = self.inspection_time
        network_time += self.gather_inspection_results()   # add gathered inspection results into self attributes
        self.qc_list.append(self.id)    # append only after gathering results from qc_list
        consent, winner_dict = self.check_consensus(self.inspection_workpiece.id, execution_info)  # results fom self
        if consent and winner_dict:   # post and mine data and allow workpiece to go to next production
            network_time += self.be_miner(self.inspection_workpiece.id, execution_info, winner_dict)
            # self.inspection_workpiece.status = "awaiting production"
            self.inspection_workpiece.status = "awaiting next step"
            self.inspection_workpiece.actual_quality = None     # Reset when got consent
        else:     # randomly assign next node to inspect
            network_time += self.assign_next_inspection(execution_info)
            self.inspection_workpiece.status = "awaiting inspection"
        self.inspection_workpiece.count_down = 0  # reset
        self.qc_list = list()  # reset after passing qc_list to next qc
        self.inspection_workpiece = None  # reset
        return inspection_time, network_time, consent, winner_dict

    def inspect_workpiece(self, state_list=None):
        """
        Determines if a manufacturing process is carried out successfully or not.
        """
        if state_list is None:
            quality = self.inspection_workpiece.actual_quality
            actual_quality = max(quality, key=quality.get)  # Key with max value in dict
            actual_quality_weight = quality[actual_quality]
            adjusted_actual_quality_weight = min(actual_quality_weight * (1 + self.capability-0.5), 100)
            possible_states = [key for key in quality.keys() if key != actual_quality]
            weights = [
                (
                        quality[key] / (100 - actual_quality_weight) * (100 - adjusted_actual_quality_weight)
                        if quality[key] != 0
                        else
                        0
                )
                for key in possible_states
                if key != actual_quality
            ]
            weights[-1] = (100-adjusted_actual_quality_weight) - sum(weights[:-1])   # ensure total weights are 100
            possible_states.append(actual_quality)
            weights.append(adjusted_actual_quality_weight)
            state_list = choices(possible_states, weights=weights)
        self.inspection_results[self.inspection_workpiece.id] = {  # add new results for workpiece id with self only
            self.id: {
                "results": state_list,
                "score": float(self.score)
            }
        }
        return state_list

    def get_inspection_time(self, step_idx, worksheet_df):
        """
        Determine validation time for a step based on a given lower and upper limit
        Only human validators take extra time for validation as they can only perform one task at a time
        """
        if worksheet_df.loc[step_idx, 'Inspection_Agent'] == "Human":
            time_min = worksheet_df.loc[worksheet_df['Step'] == step_idx].Inspection_Time_Min.iloc[0]
            time_max = worksheet_df.loc[worksheet_df['Step'] == step_idx].Inspection_Time_Max.iloc[0]
            self.inspection_time = randint(time_min, time_max)
        else:
            self.inspection_time = 0
        return self.inspection_time

    def gather_inspection_results(self):
        network_time = 0
        payload = {
            self.inspection_workpiece.id: {
                self.id: self.inspection_results[self.inspection_workpiece.id][self.id]
            }
        }
        for node_id in self.qc_list:
            address = self.nodes[node_id]["address"]
            res = requests.post(f"{address}/inspection/results/self", data=json.dumps(payload), headers=headers)
            network_time += res.elapsed.total_seconds()
            if res.status_code == 200:
                results = literal_eval(res.text)
                self.inspection_results[self.inspection_workpiece.id][node_id] = \
                    results[self.inspection_workpiece.id][node_id]
            else:
                raise ConnectionError("Results not gathered.")
        return network_time

    def check_consensus(self, workpiece_id, execution_info):
        if len(self.inspection_results[workpiece_id]) == 0:  # not part of qc_list
            return True, {}
        consent = False
        winner_dict = self.get_winner(workpiece_id)   # dict of results, qc_list and score
        if len(self.qc_list) == len(self.nodes):
            consent = True
        if winner_dict["score"] >= self.threshold \
                and len(winner_dict["winner_qc_list"]) >= execution_info.get("min_qc_required", 0):
            consent = True
        if consent:
            self.post_transaction(workpiece_id, winner_dict, execution_info)
            self.update_score(winner_dict["winner_qc_list"], winner_dict["qc_list"])
        return consent, winner_dict

    def post_transaction(self, workpiece_id, winner_dict, execution_info):
        bc = self.blockchain_dict[workpiece_id]
        data = {
            "workpiece_id": workpiece_id,
            "execution_info": execution_info,
            "results": winner_dict["results"],
            "winner_qc_list": winner_dict["winner_qc_list"],
            "qc_list": winner_dict["qc_list"],
            "score": winner_dict["score"]
        }
        bc.new_transaction(data)

    def assign_next_inspection(self, execution_info):
        network_time = 0
        possible_qc = [
            node_id
            for node_id in self.nodes.keys()
            if node_id not in self.qc_list
        ]
        node_dist_tuple_list = [
            (wc_id, self.transporter.estimate_travel_distance(self.id, wc_id))
            for wc_id in possible_qc
        ]
        if self.learning:
            shuffle(node_dist_tuple_list)     # todo: comment out if need to find nearest
        else:
            node_dist_tuple_list.sort(key=lambda x: x[1])   # todo: comment out if don't need to find nearest
        for node_dist_tuple in node_dist_tuple_list:    # try the list one by one until communication gets through
            address = self.nodes[node_dist_tuple[0]]['address']
            payload = {
                "qc_list": self.qc_list,
                "workpiece_id": self.inspection_workpiece.id,
                "execution_info": execution_info
            }
            res = requests.post(f"{address}/inspection/assignment", data=json.dumps(payload), headers=headers)
            network_time += res.elapsed.total_seconds()
            if res.status_code == 202:  # If accepted, assign source and sink to transport workpiece
                self.inspection_workpiece.source = self.id  # ready to transport
                self.inspection_workpiece.sink = node_dist_tuple[0]  # ready to transport
                print(f"        {res.text}")
                break
            else:
                print("another")
                continue
        return network_time

    def get_winner(self, workpiece_id):
        results_score = (None, None)    # dummy tuple for results
        qc_list = [
            qc_id
            for qc_id in self.inspection_results[workpiece_id].keys()
        ]
        all_results = [
            results_score_dict["results"]
            for results_score_dict in self.inspection_results[workpiece_id].values()
        ]
        unique_results = [list(x) for x in set(tuple(x) for x in all_results)]
        grouped_results = [
            (results, [
                (qc_id, results_score_dict["score"])
                for qc_id, results_score_dict in self.inspection_results[workpiece_id].items()
                if results_score_dict["results"] == results
            ])
            for results in unique_results
        ]
        # print(grouped_results)
        if self.consensus_mode == "majority":
            results_score = self.get_winner_by_majority(grouped_results)
        elif self.consensus_mode == "confidence":
            results_score = self.get_winner_by_confidence(grouped_results)
        winner = {
            "results": results_score[0],
            "winner_qc_list": [qc_list for results, qc_list in grouped_results if results == results_score[0]][0],
            "score": results_score[1],
            "qc_list": qc_list
        }
        return winner

    @staticmethod
    def get_winner_by_majority(grouped_results):
        group_count = [
            (results, sum(score for _, score in qcs_score_tup_list))  # sum of tuple second elements in list
            for results, qcs_score_tup_list in grouped_results
        ]
        group_count.sort(key=lambda x: x[1])  # sort list in ascending order of tuple second element
        winner_results_score = group_count[-1]
        return winner_results_score

    @staticmethod
    def get_winner_by_confidence(grouped_results):
        group_count = [
            (results, 1-prod([1-score for _, score in qcs_score_tup_list]))  # sum of tuple second elements in list
            for results, qcs_score_tup_list in grouped_results
        ]
        group_count.sort(key=lambda x: x[1])  # sort list in ascending order of tuple second element
        winner_results_score = group_count[-1]
        return winner_results_score

    def be_miner(self, workpiece_id, execution_info, winner_dict):
        network_time = 0
        network_time += self.post_mine(workpiece_id, execution_info)
        network_time += self.resolve_conflicts(workpiece_id, execution_info, winner_dict)  # send bc to neighbours
        return network_time

    def post_mine(self, workpiece_id, execution_info):
        payload = {
            "workpiece_id": workpiece_id,
            "execution_info": execution_info,
            "miner": self.id,
        }
        res = requests.post(f"{self.address}/blockchain/mine", data=json.dumps(payload), headers=headers)
        if res.status_code != 200:
            raise ConnectionError("Fail to mine.")
        return res.elapsed.total_seconds()

    def resolve_conflicts(self, workpiece_id, execution_info, winner_dict):
        """
        Send block chain to other nodes.
        :return:
        """
        network_time = 0
        bc = self.blockchain_dict[workpiece_id]
        payload = {
            "workpiece_id": workpiece_id,
            "execution_info": execution_info,
            "winner_dict": winner_dict,
            "miner": self.id,
            "chain": bc.chain
        }
        for node_id, node_info in self.nodes.items():
            if node_id == self.id:  # Don't call self
                continue
            node_address = node_info["address"]
            res = requests.post(f"{node_address}/blockchain/consensus", data=json.dumps(payload), headers=headers)
            network_time += res.elapsed.total_seconds()
            if res.status_code == 406:  # Invalid chain, stop sending
                self.penalize()  # reduce own score
                break
            elif res.status_code == 412:    # Invalid chain and no consent, stop sending
                self.penalize()
                self.assign_next_inspection(execution_info)
                break
        return network_time

    def update_score(self, winner_qc_list, qc_list):
        self.in_qc_counter += 1
        if self.id in [qc_score_tup[0] for qc_score_tup in winner_qc_list]:  # if self in winner qc_list
            self.in_winner_counter += 1
            self.reward()
        elif self.id in qc_list:   # if self inspected workpiece before but not in winner qc_list
            self.penalize()

    def reward(self):
        if self.learning:
            reward_value = 0.01
            if self.consensus_mode == "confidence":     # learning
                error = self.get_score_error()
            else:   # not learning
                error = 0
            if self.consensus_mode == "confidence" and self.score < 1 and error > reward_value:
                self.score += reward_value
                if self.score > 1:
                    self.score = 1

    def penalize(self):
        if self.learning:
            penalty_value = -0.01
            if self.consensus_mode == "confidence":  # learning
                error = self.get_score_error()
            else:   # not learning
                error = 0
            if self.consensus_mode == "confidence" and self.score > 0 and error < penalty_value:
                self.score += penalty_value
                if self.score < 0:
                    self.score = 0

    def get_score_error(self):
        if self.in_qc_counter == 0:  # Avoid MathError
            history_of_success = 0
        else:
            history_of_success = self.in_winner_counter/self.in_qc_counter  # Set condition for convergence
        error = history_of_success - self.score
        # Reset counters for every 10 qc rounds
        if self.in_qc_counter >= 10:
            self.in_winner_counter = 0
            self.in_qc_counter = 0
        return error

    def initiate_quality_control(self):
        """
        Route.
        rule='/inspection'
        :return:
        """
        if self.inspection_workpiece is None:
            data = request.get_json()
            execution_info = data["execution_info"]
            workpiece_id = data["workpiece_id"]
            self.inspection_workpiece = workpiece_id
            self.qc_list = list()
            response = "Waiting to receive inspection workpiece."
            return response, 202    # Accept
        else:
            response = "Currently unavailable. Try again later."
            return response, 303    # Reject

    def get_inspection_results(self):
        """
        Route.
        rule='/inspection/results'
        :return:
        """
        return self.inspection_results, 200

    def requested_inspection_results(self):
        """
        Route.
        rule='/inspection/results/self'
        :return:
        """
        data = request.get_json()
        response = dict()
        for workpiece_id, node_results_dict in data.items():
            # Add requester's results to self inspection results list
            for node_id, results in node_results_dict.items():
                self.inspection_results[workpiece_id][node_id] = results
            # Send self inspection results to requester
            response[workpiece_id] = {
                self.id: self.inspection_results[workpiece_id][self.id]
            }
            # print(f"in results route, {response}")
        return jsonify(response), 200   # OK

    def assigned_to_inspect(self):
        """
        Route.
        rule='/inspection/assignment'
        :return:
        """
        if self.inspection_workpiece is not None:
            response = {
                "message": "Unable to fulfill request. See others."
            }
            return jsonify(response), 303   # See others
        else:
            data = request.get_json()
            self.inspection_workpiece = data.get("workpiece_id")    # to be replaced with workpiece instance in start
            self.qc_list = data.get("qc_list", [])
            execution_info = data.get("execution_info")
            response = {
                'message': "Assignment accepted."
            }
            return jsonify(response), 202   # Accepted

    def register_quality_controllers(self):
        """
        Route.
        rule='/blockchain/registration'
        :return:
        """
        data = request.get_json()
        nodes = data.get('nodes')
        if nodes is None or not isinstance(nodes, dict):
            response = {
                'message': "Error: Please supply valid nodes dict {<node_id>: {'address': <address>}}",
                'total_nodes': list(self.nodes),
            }
            return jsonify(response), 400  # Bad request
        self.register_nodes(nodes)    # add dict to nodes dict
        response = {
            'message': 'New nodes have been added',
            'total_nodes': list(self.nodes),
        }
        return jsonify(response), 200   # OK

    def mine(self):
        """
        Route.
        rule='/blockchain/mine'
        :return:
        """
        data = request.get_json()
        workpiece_id = data["workpiece_id"]
        bc = self.blockchain_dict[workpiece_id]
        pass  # todo: send results to process controller
        mined_data = bc.mine(self.threshold, self.consensus_mode, data["miner"])
        # self.resolve_conflicts(data)  # send blockchain to neighbours (resolve conflict)
        response = mined_data
        return jsonify(response), 200   # OK

    def confirm_results(self, workpiece_id, miner_id, qc_list):
        counter = 0     # Initialize
        node_id_list = list(self.nodes.keys())
        shuffle(node_id_list)   # randomly shuffle dict keys
        for node_id in node_id_list:
            node_info = self.nodes[node_id]
            if node_id in self.inspection_results[workpiece_id].keys() and node_id != self.id and node_id != miner_id:
                node_address = node_info["address"]
                res = requests.get(f"{node_address}/inspection/results")
                if res.status_code == 200:
                    node_results = literal_eval(res.text)
                    node_results = node_results[workpiece_id]
                    if not node_results:    # If results is empty dict
                        continue
                    # Check all items in results
                    if self.inspection_results[workpiece_id] != node_results:
                        return False    # Stop loop. Different results
                    else:
                        counter += 1     # Same results
                if counter >= len(qc_list) * 0.5:
                    break   # Stop loop after contacting 50% of qc list
        return False    # Nobody to confirm

    def consensus(self):
        """
        Route.
        rule='/blockchain/consensus'
        :return:
        """
        data = request.get_json()
        workpiece_id = data["workpiece_id"]
        execution_info = data["execution_info"]
        winner_dict = data["winner_dict"]
        miner_id = data["miner"]
        if not self.blockchain_dict.get(workpiece_id, False):
            self.register_workpiece(workpiece_id)
        bc = self.blockchain_dict[workpiece_id]
        chain = data.get("chain")
        if not bc.replace_chain(chain):    # Invalid chain
            response = {
                'message': "Invalid chain.",
            }
            if self.id not in winner_dict["qc_list"]:    # Self don't have inspection results
                response["action"] = "None."
            else:    # Self have inspection results
                if self.confirm_results(workpiece_id, miner_id, winner_dict["qc_list"]):    # Another node confirms
                    consent, _ = self.check_consensus(workpiece_id, execution_info)  # Check consensus and post to bc
                    if consent:     # True consent
                        t = Thread(
                            target=self.be_miner,                # Replace miner
                            args=(workpiece_id, execution_info, winner_dict)
                        )
                        t.start()
                        response["action"] = "Replace miner."
                    else:   # False consent
                        response["action"] = "Continue quality control."
                        return jsonify(response), 412  # Precondition failed
                else:       # No confirmation received
                    response["action"] = "None."
            return jsonify(response), 406  # Not acceptable
        else:   # Valid chain
            self.update_score(winner_dict["winner_qc_list"], winner_dict["qc_list"])
            response = {
                'message': "Chain replaced."
            }
            return jsonify(response), 202  # Accepted


class Blockchain:
    def __init__(self, id, threshold, consensus_mode):
        self.id = id    # workpiece id
        self.current_transaction = ['Start']
        self.chain = []
        # Create the genesis block
        self.create_new_block(consensus_mode=consensus_mode, previous_hash='1', threshold=threshold, miner_id='1')

    def create_new_block(self, consensus_mode, threshold, previous_hash, miner_id):
        """
        Create a new Block in the Blockchain
        """
        block = {
            'index': len(self.chain) + 1,
            'head': {
                'previous_hash': previous_hash or self.hash(self.chain[-1]),
                'consensus_mode': consensus_mode,
                'threshold': threshold,
                'miner_id': miner_id
            },
            'body': self.current_transaction,
            'timestamp': time(),
        }
        # Reset the current list of transactions
        self.current_transaction = []
        self.chain.append(block)
        return block

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod  # no idea
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def validate_last_block(self, last_block):
        if last_block.get("body") == self.current_transaction or not self.current_transaction:  # Check content
            return True
        else:
            return False

    def validate_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: A blockchain
        :return: True if valid, False if not
        """
        valid = False
        if isinstance(chain, list):
            last_block = chain[-1]
            if self.validate_last_block(last_block):
                current_index = 1
                while current_index < len(chain):
                    block = chain[current_index]
                    # Check that the hash of the block is correct
                    last_block_hash = self.hash(last_block)
                    if block['head']['previous_hash'] != last_block_hash:
                        break
                    last_block = block
                    current_index += 1
                valid = True
        return valid

    def new_transaction(self, transaction):
        """
        Add new production step which includes inspection to temporary holder.
        This information will be hashed into a new block in mine function.
        :return:
        """
        required = ["execution_info", "winner_qc_list", "qc_list", "results", "score"]
        if not all(k in transaction for k in required):
            return False
        self.current_transaction.append(transaction)
        index = self.last_block['index'] + 1
        return index

    def mine(self, threshold, consensus_mode, miner_id):
        '''
        Mine transaction.
        :return:
        '''
        last_block = self.last_block
        # Forge the new Block by adding it to the chain
        previous_hash = self.hash(last_block)
        block = self.create_new_block(
            previous_hash=previous_hash,
            threshold=threshold,
            consensus_mode=consensus_mode,
            miner_id=miner_id
        )
        mined_data = {
            'message': "New Block Forged",
            'index': block['index'],
            'head': block['head'],
            'body': block['body'],
        }
        return mined_data

    def replace_chain(self, chain):
        """
        Replace self.chain with chain.
        """
        if self.validate_chain(chain):
            self.chain = chain
            return True
        else:
            return False

