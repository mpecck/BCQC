# BCQC with QDT

## Methodology
1. The range of production time and inspection time by each workcell was specified in ```Data_Sheet_qdt.csv```.
2. As there were 17 workcells, actual capability of each workcell in performing inspection was randomly generated from 0 to 1 and was written in ```actual_inspector_capability.csv```.
3. The actual capability values and data sheet were used to generate a simulated production process of computer deskstop assembly using ```bcqc_with_qdt/input_generator.py```. The simulated production process did not include inspection process.
4. Computer simulations in Section 5.3 in our manuscript was performed using ```bcqc_with_qdt/independent_qc_simulation.py```.
- To simulate for ```score_type = "training"```, a new simulated production process has to be generated with at least 20 products to be assembled. The estimated capability value ```score``` of each workcell was written in ```estimated_inspector_capability.csv```.
- To simulate for ```score_type = "score"```, both the actual capability and estimated capability values were used as input in the simulation.
5. Computer simulations in Section 5.4 in our manuscript is performed using ```bcqc_with_qdt/dependent_qc_simulation.py```. This simulation only simulate for ```score_type = "score"```.

## Visualization
1. Fig. 8 was generated from ```bcqc_with_qdt/analysis/qc_info.py```.
2. Fig. 9 was generated from ```bcqc_with_qdt/analysis/independent_qc/independent_qc_majority_general_plot.py```. The input file was generated using the following steps.
- Run ```bcqc_with_qdt/analysis/independent_qc/independent_qc_majority_per_input.py``` for each input.
- Run ```bcqc_with_qdt/analysis/independent_qc/independent_qc_majority_per_simulation.py```.
3. Fig. 10 was generated from ```bcqc_with_qdt/analysis/independent_qc/independent_qc_confidence_scatter_plot.py```. The input file was generated using the following steps.
- Run ```bcqc_with_qdt/analysis/independent_qc/independent_qc_capability_per_input.py``` for each input.
- Run ```bcqc_with_qdt/analysis/independent_qc/independent_qc_capability_per_simulation.py```.
- Run ```bcqc_with_qdt/analysis/independent_qc/independent_qc_score_per_input.py``` for each input.
- Run ```bcqc_with_qdt/analysis/independent_qc/independent_qc_score_per_simulation.py```.
4. Fig. 11 was generated from ```bcqc_with_qdt/analysis/independent_qc/independent_qc_training_mse_per_input_plot.py```. The input file was generated using the following steps.
- Run ```bcqc_with_qdt/analysis/independent_qc/independent_qc_training_mse_per_input.py``` for each input.
5. Fig. 12 was plotted in excel ```bcqc_with_qdt/results/postprocessed/scatter_plot_for_score_independent_vs_dependent```. The input file was generated using the following steps.
- Run ```bcqc_with_qdt/analysis/dependent_qc/independent_qc_score_per_input.py``` for each input.
- Run ```bcqc_with_qdt/analysis/dependent_qc/independent_qc_score_per_simulation.py```.

