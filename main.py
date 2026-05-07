from canbus import Canbus
from ecu import Ecu

if __name__ == "__main__":
    ecu1 = Ecu(1,"Wheel",{
        10:{
            "frequence": 20  
        },
        100:{
            "frequence": 100
        }
    })
    ecu2 = Ecu(2,"ABS",{
        20:{
            "frequence": 20  
        }
    })

    canbus = Canbus(100,[ecu1,ecu2])
    canbus.startSimulation()
