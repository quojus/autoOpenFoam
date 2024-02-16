from autoOpenFoam import AutoOpenFoam
import time

def init_my_wert(autoOpenFoam: AutoOpenFoam):
    autoOpenFoam.init_modelParameter('ip', 'system/setFieldsDict', 31,
                                     f'            volScalarFieldValue permeability ...')
    autoOpenFoam.init_modelParameter('dp', 'system/setFieldsDict', 21, f'    volScalarFieldValue permeability ...')
    autoOpenFoam.init_modelParameter('e_len_x', 'gmsh/make_mesh.geo', 13, f'e_len_x=...;')
    autoOpenFoam.init_modelParameter('e_len_y', 'gmsh/make_mesh.geo', 14, f'e_len_y=...;')
    autoOpenFoam.init_modelParameter('e_center_y', 'gmsh/make_mesh.geo', 11, f'e_center_y=ymax...;')

    autoOpenFoam.init_runParameter('startFrom', 'system/controlDict.orig', 19, f'startFrom ...;')
    autoOpenFoam.init_runParameter('endTime_year', 'system/controlDict.orig', 25, f'endTime_year ...;   //year')
    autoOpenFoam.init_runParameter('writeInterval_year', 'system/controlDict.orig', 26,
                                   f'writeInterval_year ...; //year;')


autoOpenFoam = AutoOpenFoam(shell=True, root_path='/Users/falk/HydrothermalFoam_runs',
                            projekt_ortner='cooling_intrusion_auto', application='HydrothermalSinglePhaseDarcyFoam_Cpr')
init_my_wert(autoOpenFoam)
autoOpenFoam.set_Parameter(endTime_year=500)
autoOpenFoam.set_Parameter(ip=1e-19, dp=1e-13, e_len_x=700)
def meinAbbruchkriterium2(myVar=None) -> bool | str:
    if myVar is None:
        return 'myVar'
    # Logik zur Bestimmung, ob die Simulation abgebrochen werden soll
    if myVar > 3:
        print('abbrechen jkhbcsaikj')
        return True # berechnug wird abgebrochen

    return False


autoOpenFoam.myVar = 3  # name ist voher nicht definirt in autoOpenFoam
print('autoOpenFoam.myVar', autoOpenFoam.myVar)

autoOpenFoam.funktions_abbruchkreterium['brumm'] = meinAbbruchkriterium2
time.sleep(2)
autoOpenFoam.run_start()
