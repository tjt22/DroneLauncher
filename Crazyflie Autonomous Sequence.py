
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander
from cflib.utils import uri_helper
import time

# URI to the Crazyflie to connect to
uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')


def simple_sequence():
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        # Hover
        with PositionHlCommander(scf, controller=PositionHlCommander.CONTROLLER_PID) as pc:
            time.sleep(2)
            # Move forward 3 ft at 0.2 m/s
            pc.forward(3, velocity = 0.2)

            # Land


if __name__ == '__main__':
    cflib.crtp.init_drivers()

    simple_sequence()
    
