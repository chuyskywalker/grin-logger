prstats = [
    {
        "name": "Faults (text)",
        "address": 258,
        "scale": 1,
        "bitDefs": {
            "0": "Controller over voltage",
            "1": "Filtered phase over current",
            "2": "Bad current sensor calibration",
            "3": "Current sensor over current",
            "4": "Controller over temperature",
            "5": "Motor Hall sensor fault",
            "6": "Controller under voltage",
            "7": "POST static gating test",
            "8": "Network communication timeout",
            "9": "Instantaneous phase over current",
            "10": "Motor over temperature",
            "11": "Throttle voltage outside range",
            "12": "Instantaneous controller over voltage",
            "13": "Internal error",
            "14": "POST dynamic gating test",
            "15": "Instantaneous controller under voltage"
        },
        "type": "bit vector",
        "description": "15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0\n\n1=active 0=not active\n\nbit  0: Controller over voltage (flash code 1,1)\nbit  1: Phase over current (flash code 1,2)\nbit  2: Current sensor calibration (flash code 1,3)\nbit  3: Current sensor over current (flash code 1,4)\nbit  4: Controller over temperature (flash code 1,5)\nbit  5: Motor Hall sensor fault (flash code 1,6)\nbit  6: Controller under voltage (flash code 1,7)\nbit  7: POST static gating test (flash code 1,8)\nbit  8: Network communication timeout (flash code 2,1)\nbit  9: Instantaneous phase over current (flash code 2,2)\nbit 10: Motor over temperature (flash code 2,3)\nbit 11: Throttle voltage outside range (flash code 2,4)\nbit 12: Instantaneous controller over voltage (flash code 2,5)\nbit 13: Internal error (flash code 2,6\nbit 14: POST dynamic gating test (flash code 2,7)\nbit 15: Instantaneous under voltage (flash code 2,8)"
    },
    {
        "name": "Controller Temperature (°C)",
        "address": 259,
        "scale": 1,
        "isSigned": True,
        "type": "independent",
        "description": "Base plate temperature"
    },
    {
        "name": "Vehicle Speed (km/h)",
        "address": 260,
        "scale": 256,
        "isSigned": True,
        "type": "independent",
        "description": "Calculated vehicle speed"
    },
    {
        "name": "Motor Temperature (°C)",
        "address": 261,
        "scale": 1,
        "type": "independent",
        "description": "Motor temperature "
    },
    {
        "name": "Motor Current (A)",
        "address": 262,
        "scale": 32,
        "type": "independent",
        "description": "Motor peak current "
    },
    {
        "name": "Motor RPM (RPM)",
        "address": 263,
        "scale": 1,
        "isSigned": True,
        "type": "independent",
        "description": "Motor speed "
    },
    {
        "name": "Motor Speed (%)",
        "address": 264,
        "scale": 40.96,
        "type": "independent",
        "description": "Motor speed"
    },
    {
        "name": "Battery Voltage (V)",
        "address": 265,
        "scale": 32,
        "type": "independent",
        "description": "Measured battery voltage"
    },
    {
        "name": "Battery Current (A)",
        "address": 266,
        "scale": 32,
        "isSigned": True,
        "type": "independent",
        "description": "Measured battery amperage"
    },
    {
        "name": "Battery State of Charge (%)",
        "address": 267,
        "scale": 32,
        "type": "independent",
        "description": "Remaining battery capacity"
    },
    {
        "name": "Battery Power (W)",
        "address": 268,
        "scale": 1,
        "type": "independent",
        "description": "Calculated battery output power"
    },
    {
        "name": "Last Fault (text)",
        "address": 269,
        "scale": 1,
        "bitDefs": {
            "0": "Controller over voltage",
            "1": "Filtered phase over current",
            "2": "Bad current sensor calibration",
            "3": "Current sensor over current",
            "4": "Controller over temperature",
            "5": "Motor Hall sensor fault",
            "6": "Controller under voltage",
            "7": "POST static gating test",
            "8": "Network communication timeout",
            "9": "Instantaneous phase over current",
            "10": "Motor over temperature",
            "11": "Throttle voltage outside range",
            "12": "Instantaneous controller over voltage",
            "13": "Internal error",
            "14": "POST dynamic gating test",
            "15": "Instantaneous controller under voltage"
        },
        "type": "bit vector",
        "description": "15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0\n\n1=active 0=not active\n\nbit  0: Controller over voltage (flash code 1,1)\nbit  1: Phase over current (flash code 1,2)\nbit  2: Current sensor calibration (flash code 1,3)\nbit  3: Current sensor over current (flash code 1,4)\nbit  4: Controller over temperature (flash code 1,5)\nbit  5: Motor Hall sensor fault (flash code 1,6)\nbit  6: Controller under voltage (flash code 1,7)\nbit  7: POST static gating test (flash code 1,8)\nbit  8: Network communication timeout (flash code 2,1)\nbit  9: Instantaneous phase over current (flash code 2,2)\nbit 10: Motor over temperature (flash code 2,3)\nbit 11: Throttle voltage outside range (flash code 2,4)\nbit 12: Instantaneous controller over voltage (flash code 2,5)\nbit 13: Internal error (flash code 2,6)\nbit 14: POST dynamic gating test (flash code 2,7)\nbit 15: Instantaneous under voltage (flash code 2,8)"
    },
    {
        "name": "Throttle Voltage (V)",
        "address": 270,
        "scale": 4096,
        "type": "independent",
        "description": "Filtered throttle voltage"
    },
    {
        "name": "Brake 1 Voltage (V)",
        "address": 271,
        "scale": 4096,
        "type": "independent",
        "description": "Filtered brake 1 voltage"
    },
    {
        "name": "Brake 2 Voltage (V)",
        "address": 272,
        "scale": 4096,
        "type": "independent",
        "description": "Filtered brake 2 voltage"
    },
    {
        "name": "Phase A Current (A)",
        "address": 282,
        "scale": 32,
        "isSigned": True,
        "type": "independent",
        "description": "Measured motor phase A current"
    },
    {
        "name": "Phase B Current (A)",
        "address": 283,
        "scale": 32,
        "isSigned": True,
        "type": "independent",
        "description": "Calculated motor phase B current"
    },
    {
        "name": "Phase C Current (A)",
        "address": 284,
        "scale": 32,
        "isSigned": True,
        "type": "independent",
        "description": "Measured motor phase C current"
    },
    {
        "name": "Phase A Voltage (V)",
        "address": 285,
        "scale": 32,
        "type": "independent",
        "description": "Measured instantaneous motor phase A voltage"
    },
    {
        "name": "Phase B Voltage (V)",
        "address": 286,
        "scale": 32,
        "type": "independent",
        "description": "Measured instantaneous motor phase B voltage"
    },
    {
        "name": "Phase C Voltage (V)",
        "address": 287,
        "scale": 32,
        "type": "independent",
        "description": "Measured instantaneous motor phase C voltage"
    },
    {
        "name": "Wheel Speed Sensor Based (RPM)",
        "address": 311,
        "scale": 16,
        "type": "independent",
        "description": "Calculated wheel speed based on wheel speed sensor"
    },
    {
        "name": "Wheel Speed Motor Based (RPM)",
        "address": 312,
        "scale": 16,
        "type": "independent",
        "description": "Calculated wheel speed based on motor pole pairs"
    },
    {
        "name": "Measured Wheel Speed (RPM)",
        "address": 313,
        "scale": 16,
        "type": "independent",
        "description": "Measured wheel speed"
    }
]
