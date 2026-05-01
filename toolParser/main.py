import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from data.data_parsers.custom_instance_parser import parse
from visualization import gantt_chart, precedence_chart

from solution_methods.GA.src.initialization import initialize_run
from solution_methods.GA.run_GA import run_GA
from solution_methods.CP_SAT.run_cp_sat import run_CP_SAT


from task_parser import create_processing_info

processing_info = create_processing_info("test.txt")
# processing_info = {
#         "instance_name": "custom_problem_instance",
#         "nr_machines": 2, 
#         "jobs": [
#             {"job_id": 0, "operations": [
#                 {"operation_id": 0, "processing_times": {'machine_1': 26213, 'machine_2': 0, 'machine_3': 0, 'machine_4': 0, 'machine_5': 16986, 'machine_6': 69683, 'machine_7': 163, 'machine_8': 0, 'machine_9': 58539, 'machine_10': 0, 'machine_11': 80808, 'machine_12': 80400, 'machine_13': 76976, 'machine_14': 64942, 'machine_15': 0, 'machine_16': 0, 'machine_17': 0, 'machine_18': 43318, 'machine_19': 53214, 'machine_20': 0}, "predecessors": None},
#                 {"operation_id": 4, "processing_times": {'machine_1': 26213, 'machine_2': 33318, 'machine_3': 80817, 'machine_4': 57181, 'machine_5': 0, 'machine_6': 0, 'machine_7': 8007, 'machine_8': 63511, 'machine_9': 0, 'machine_10': 0, 'machine_11': 54069, 'machine_12': 225, 'machine_13': 0, 'machine_14': 0, 'machine_15': 32083, 'machine_16': 0, 'machine_17': 86366, 'machine_18': 62338, 'machine_19': 57912, 'machine_20': 4989}, "predecessors": [0]}
#             ]},
#             {"job_id": 1, "operations": [
#                 {"operation_id": 1, "processing_times": 'machine_1': 26213, 'machine_2': 82129, 'machine_3': 0, 'machine_4': 9671, 'machine_5': 0, 'machine_6': 64922, 'machine_7': 0, 'machine_8': 36099, 'machine_9': 0, 'machine_10': 0, 'machine_11': 0, 'machine_12': 29458, 'machine_13': 0, 'machine_14': 0, 'machine_15': 36570, 'machine_16': 0, 'machine_17': 0, 'machine_18': 63458, 'machine_19': 0, 'machine_20': 27323}: None},
#                 {"operation_id": 2, "processing_times": {'machine_1': 26213, 'machine_2': 0, 'machine_3': 34880, 'machine_4': 1413, 'machine_5': 0, 'machine_6': 76790, 'machine_7': 0, 'machine_8': 0, 'machine_9': 0, 'machine_10': 0, 'machine_11': 36216, 'machine_12': 0, 'machine_13': 48027, 'machine_14': 0, 'machine_15': 0, 'machine_16': 61050, 'machine_17': 0, 'machine_18': 40568, 'machine_19': 990, 'machine_20': 36887}, "predecessors": [1]}
#             ]},
#         ],
#         "sequence_dependent_setup_times": {
#             "machine_1": [
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0]
#             ],
#             "machine_2": [
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0]
#             ],
#             "machine_3": [
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0]
#             ],
#             "machine_4": [
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0]
#             ],
#             "machine_5": [
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0],
#                 [0, 0, 0, 0]
#             ],

#         }
#     }


parameters = {"instance": {"problem_instance": "custom_problem_instance"},
             "solver": {"time_limit": 3600, "model": "fajsp"},
             "output": {"logbook": True}
             }

jobShopEnv = parse(processing_info)
results, jobShopEnv = run_CP_SAT(jobShopEnv, **parameters)

# plt = gantt_chart.plot(jobShopEnv)
# plt.show()
print(results)