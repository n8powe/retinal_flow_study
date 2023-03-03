
import sys

sys.path.append('retinal_flow_study_path')

from retinal_flow_processor import RetinalFlowProcessor

proc = RetinalFlowProcessor('2022-12-21')

# proc.calibrationVideoRaw = 'calibration'
# proc.do_calibration(starting_frame=300, stopping_frame=1600)

# proc.eyeVideoRaw = 'eye_2023-03-03_14-38-35'
# proc.process_eye()

proc.sceneVideoRaw = 'scene_2023-03-03_14-38-35'
proc.process_scene()

print('done')
