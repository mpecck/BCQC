# BCQC with PoW

## Methodology
1. The range of production time and inspection time by each workcell was specified in ```Data_Sheet_pow_scenario_<scenario number>.csv```.
2. Run ```blockchain_platform.py```. Simulators will communicate with blockchain platform via flask to manage blockchain.
4. Computer simulations in Scenario 1 in Section 5.2 in our manuscript was performed using ```bcqc_with_pow/serial_with_conventional_simulator.py```. Select the scenario number to input the correct data sheet.
5. Computer simulations in Scenario 2, 3, and 4 in Section 5.2 in our manuscript was performed using ```bcqc_with_pow/serial_with_bcqc_simulator.py```. Select the scenario number to input the correct data sheet.
6. Computer simulations in Scenario 5, 6, and 7 in Section 5.2 in our manuscript was performed using ```bcqc_with_pow/parallel_with_bcqc_simulator.py```. Select the scenario number to input the correct data sheet.

## Visualization
1. After compiling results of each scenario in ```bcqc_with_pow/results```, Fig. 6 was generated from ```bcqc_with_pow/results/Data Analysis.xlsx```.
