
import sys

sys.path.append('retinal_flow_study_path')

from retinal_flow_processor import RetinalFlowProcessor

proc = RetinalFlowProcessor('2022-12-21')

proc.do_calibration()

print('done')
