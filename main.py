from canbus import Canbus
from ecu import Ecu, AttackerEcu

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

    ecuA = AttackerEcu(3,"Infected",{
        10:{
            "frequence": 20
        }
    })

    canbus = Canbus(0,[ecu1,ecuA])
    canbus.startSimulation()
