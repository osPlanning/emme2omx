import argparse
import omx
import array as _array
import numpy as np
import inro.emme.desktop.app as app
import inro.modeller as _m
import inro.emme.matrix as ematrix
import inro.emme.database.matrix
import inro.emme.database.emmebank as _eb

# This script converts Emme matrices to OMX and vice versa.


# Convert Emme matrices to OMX.
# Requires full paths for emmebank and OMX output. 
# Optional arguments may specify list of matrices to convert and scenario number, for zone numbering.  
 
def emme2omx(emmebank_file, omx_file_name, emme_matrix_list = None, scenario_number = None):
    
    emmebank = _eb.Emmebank(emmebank_file)                          # Access the emmebank with Emme libraries
    all_emme_matrices = emmebank.matrices()                          # Create a list of all matrices in emmebank

    # If no matrix subset list provided, convert all matrices in emmebank.
    if emme_matrix_list is None:
        emme_matrix_list = all_emme_matrices

    # If no scenario number provided, assume first available scenario.
    if scenario_number is None:
        current_scenario = list(emmebank.scenarios())[0]
    elif isinstance(scenario_number, basestring):                   # Check that scenario number is a string. 
        current_scenario = emmebank.scenario(scenario_number)       
    else:                           
        current_scenario = list(emmebank.scenarios())[0]
        print "Scenario number must be in string form. (Use quotations in argument). First scenario used by default." 
    
    # Initialize OMX file.
    omx_file = omx.openFile(omx_file_name, 'w')                     
    
    # Map zone numbers to matrix indeces.
    try:
        zones = tuple(current_scenario.zone_numbers)
        omx_file.createMapping('taz', zones)                    
    except AttributeError:
        print "ERROR: No zone numbers found for this scenario. Check scenario is valid, or leave input blank to use default scenario."            
            
    # Create OMX matrix for each Emme matrix specified.         
    for emme_matrix in emme_matrix_list:    
        if emme_matrix.type == 'FULL':                              # Only FULL matrices can be handled by OMX. 
            numpy_matrix = np.matrix(emme_matrix.raw_data)  
            numpy_matrix = np.resize(numpy_matrix, [len(zones), len(zones)])
            # Create NumPy array of Emme data.
            
            if emme_matrix.get_data().type == 'i':                   
                # Set maximum characters for integer data and write NumPy array to OMX matrix.
                numpy_matrix = np.where(emme_matrix > np.iinfo('uint16').max, np.iinfo('uint16').max, matrix_value)
                omx_file[emme_matrix.name] = numpy_matrix
                print str(emme_matrix.name) + " added to OMX."        
            # Write NumPy array to OMX matrix for non-integer data. 
            omx_file[emme_matrix.name] = numpy_matrix
            print str(emme_matrix.name) + " added to OMX."               
        else:
            print "WARNING: Matrix '" + str(emme_matrix.name) + "' not FULL type and was not be converted. OMX only handles FULL matrices."
             
    omx_file.close()
           
# Convert OMX to Emme matrix files

def omx2emme(emmebank_file, omx_file_name, matrix_list = None, scenario_number = None):

    emmebank = _eb.Emmebank(emmebank_file)                          # Access the emmebank with Emme libraries
    all_emme_matrices = emmebank.matrices()                          # Create a list of all matrices in emmebank

     # If no scenario number provided, assume first available scenario.
    if scenario_number is None:
        current_scenario = list(emmebank.scenarios())[0]
    elif isinstance(scenario_number, basestring):                   # Check that scenario number is a string. 
        current_scenario = emmebank.scenario(scenario_number)       
    else:                           
        current_scenario = list(emmebank.scenarios())[0]
        print "Scenario number must be in string form. (Use quotations in argument). First scenario used by default." 
                
    # Map zone numbers to matrix indeces.
    try:
        zones = tuple(current_scenario.zone_numbers)
    except AttributeError:
        print "ERROR: No zone numbers found for this scenario. Check scenario is valid, or leave input blank to use default scenario."            

    # Load OMX matrix data
    omx_file = omx.openFile(omx_file_name, 'r')
    for omx_matrix_name in omx_file.listMatrices():                         # Cycle through all matrices in OMX file
        np_matrix = np.matrix(omx_file[omx_matrix_name])                    # Create NumPy array of OMX data
        np_matrix = np_matrix.astype(float)                                 
        np_array = np.squeeze(np.asarray(np_matrix))                       
        np_array_resize = np.resize(np_array, [len(zones), len(zones)])     # Set array size to match zones
        emme_matrix = ematrix.MatrixData(indices=[zones,zones],type='f')    
        emme_matrix.raw_data = [_array.array('f',row) for row in np_array_resize]
        print "Processing " + str(omx_matrix_name)

        # Test if matrix exists in emmebank
        if emmebank.matrix(omx_matrix_name) is not None: 
            print str(omx_matrix_name) + " exists. Overwriting Emme matrix."
            matrix_id = emmebank.matrix(omx_matrix_name).id
            emmebank.matrix(matrix_id).set_data(emme_matrix,current_scenario)   # Write data to OMX matrix
        else: 
            new_id = emmebank.available_matrix_identifier("FULL")    
            new_matrix = emmebank.create_matrix(new_id) 
            new_matrix.name = omx_matrix_name
            print str(omx_matrix_name) + " does not exist. Creating Emme matrix."                                  
            emmebank.matrix(new_id).set_data(emme_matrix,current_scenario)      # Write data to OMX matrix
    
    omx_file.close()


print "Matrices converted!"