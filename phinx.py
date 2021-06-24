userStates={
        "DEGRADED_MODE":0x40000000,
        "FAILURE_MODE": 0x80000000,
        "DVL_RECEIVED_VALID":0x00000001,
        "GPS_RECEIVED_VALID":0x00000002,
        "DEPTH_RECEIVED_VALID":0x00000004,
        "USBL_RECEIVED_VALID":0x00000008,
        "LBL_RECEIVED_VALID":0x00000010,
        "GPS2_RECEIVED_VALID":0x00000020,
        "EMLOG_RECEIVED_VALID":0x00000040,
        "MANUAL_GPS_RECEIVED_VALID":0x00000080,
        "TIME_RECEIVED_VALID UTC_DETECTED":0x00000100,
        "FOG_ANOMALY":0x00000200,
        "ACC_ANOMALY":0x00000400,
        "TEMPERATURE_ERR":0x00000800,
        "CPU_OVERLOAD":0x00001000,
        "DYNAMIC_EXCEDEED INTERPOLATION_MISSED":0x00002000,
        "SPEED_SATURATION SPEED_SATURATION":0x00004000,
        "ALTITUDE_SATURATION ALTITUDE_SATURATION":0x00008000,
        "INPUT_A_ERR / GPS_INPUT_ERR(*) INPUT_A_ERR / GPS_INPUT_ERR(*)":0x00010000,
        "INPUT_B_ERR / UTC_INPUT_ERR(*) INPUT_B_ERR / UTC_INPUT_ERR(*)":0x00020000,
        "INPUT_C_ERR INPUT_C_ERR":0x00040000,
        "INPUT_D_ERR / INPUT_A_ERR (*) INPUT_D_ERR / INPUT_A_ERR (*)":0x00080000,
        "INPUT_E_ERR / INPUT_B_ERR (*) INPUT_E_ERR / INPUT_B_ERR (*)":0x00100000,
        "OUTPUT_A_ERR OUTPUT_A_FULL":0x00200000,
        "OUTPUT_B_ERR OUTPUT_B_FULL":0x00400000,
        "OUTPUT_C_ERR / POSTPRO_OUT_ERR(*) OUTPUT_C_FULL / POST_PRO_OUT_FULL(*)":0x00800000,
        "OUTPUT_D_ERR / OUTPUT_C_ERR(*) OUTPUT_D_FULL / OUTPUT_C_FULL(*)":0x01000000,
        "OUTPUT_E_ERR / OUTPUT_D_ERR(*) OUTPUT_E_FULL / OUTPUT_D_FULL(*)":0x02000000,
        "HRP_INVALID_ALIGNEMENT or FOG_ANOMALY or ACC_ANOMALY or SPEED_SATURATION":0x04000000,
        "ALIGNEMENT":0x08000000,
        "FINE_ALIGNEMENT":0x10000000,
        "NAVIGATION":0x20000000,
    }


def analyzeUserStatus(obj,status):
    mapValid = []
    mapDegraded = None
    mapFailure = None

    for k, v in userStates.items():
        if status&v: #(1024).to_bytes(8, byteorder='big')
            if "DEGRADED" in k:
                mapDegraded=[]
                mapDegraded.append( k )
            elif "FAILURE" in k:
                mapFailure=[]
                mapFailure.append( k )
            elif mapDegraded is not None and "_VALID" not in k and "ANOMALY" not in k:
                mapDegraded.append( k )
            elif mapFailure is not None and "_VALID" not in k:
                mapFailure.append( k )
            if "_VALID" in k or "ALIGNMENT" in k or "NAVIGATION" in k:
                mapValid.append( k )

    if mapFailure is None and hasattr(obj,"attitude_and_velocities_validity"):
        obj.attitude_and_velocities_validity = 0 if mapDegraded is None else 2
        obj.heading_validity = 0 if mapDegraded is None else 2
        obj.course_and_speed_over_ground_validity = 0 if mapDegraded is None else 2
        obj.set_and_drift_validity = 0 if mapDegraded is None else 2
    if "GPS_RECEIVED_VALID" in mapValid or "GPS2_RECEIVED_VALID" in mapValid and hasattr(obj,"position_validity"):
        obj.position_validity = 0 if mapDegraded is None else 2
    if "DEPTH_RECEIVED_VALID" in mapValid and hasattr(obj,"water_depth_validity"):
        obj.water_depth_validity = 0 if mapDegraded is None else 2
    return mapValid, mapDegraded, mapFailure


def gyro_availability(mapValid,mapDegraded, mapFailure ):#0: AVAILABLE;1: DEGRADED;2: FAILED;
    if "GPS_RECEIVED_VALID" in mapValid and "GPS2_RECEIVED_VALID" in mapValid:
        return 0 #available
    elif mapDegraded is not None:
        return 1 #degrated
    elif mapFailure is not None and len(mapFailure)>0:
        return 2 #FAILED;
    elif "GPS_RECEIVED_VALID" in mapValid or "GPS2_RECEIVED_VALID" in mapValid:
        return 1 #degrated
    else:
        return 0

def gyro_readiness_state(mapValid):#0:OPERATIONAL;1: SIMULATION;2: ALIGNMENT;
    if "ALIGNEMENT" in mapValid:
        return 2
    elif "NAVIGATION" in mapValid or len(mapValid)>0:
        return 0
    else:
        return 1
