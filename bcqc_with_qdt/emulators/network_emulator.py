from bcqc_with_qdt.emulators.workcell_emulator import Workcell
from flask import Flask

# Initialize app
app = Flask(__name__)


def add_routes(quality_controllers, threshold):
    for qc_id, qc_inst in quality_controllers.items():
        app.add_url_rule(
            rule=f'/{qc_id}/inspection',
            endpoint=f'{qc_id}_initiate_quality_control_{threshold}',
            view_func=qc_inst.initiate_quality_control, methods=['POST']
        )
        app.add_url_rule(
            rule=f'/{qc_id}/inspection/results',
            endpoint=f'{qc_id}_get_inspection_results_{threshold}',
            view_func=qc_inst.get_inspection_results,
            methods=['GET']
        )
        app.add_url_rule(
            rule=f'/{qc_id}/inspection/results/self',
            endpoint=f'{qc_id}_requested_inspection_results_{threshold}',
            view_func=qc_inst.requested_inspection_results,
            methods=['POST']
        )
        app.add_url_rule(
            rule=f'/{qc_id}/inspection/assignment',
            endpoint=f'{qc_id}_assigned_to_inspect_{threshold}',
            view_func=qc_inst.assigned_to_inspect,
            methods=['POST']
        )
        app.add_url_rule(
            rule=f'/{qc_id}/blockchain/registration',
            endpoint=f'{qc_id}_register_quality_controllers_{threshold}',
            view_func=qc_inst.register_quality_controllers,
            methods=['POST']
        )
        app.add_url_rule(
            rule=f'/{qc_id}/blockchain/mine',
            endpoint=f'{qc_id}_mine_{threshold}',
            view_func=qc_inst.mine,
            methods=['POST']
        )
        app.add_url_rule(
            rule=f'/{qc_id}/blockchain/consensus',
            endpoint=f'{qc_id}_consensus_{threshold}',
            view_func=qc_inst.consensus,
            methods=['POST']
        )


if __name__ == '__main__':
    # Instantiate objects
    total_workcells = 17
    print("Instantiating objects...")
    quality_controllers = {
        f"wc_{i + 1}": Workcell(step_idx=i + 1, id=f"wc_{i + 1}", ip="localhost", port=5000, qc_id=f"wc_{i + 1}")
        for i in range(total_workcells)
    }
    print("Completed instantiating objects")

    add_routes(quality_controllers)
    app.run(host='0.0.0.0', port=5000)
