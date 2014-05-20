import argparse
import omx
import array as _array
import numpy as np
import inro.emme.desktop.app as app
import inro.modeller as _m
import inro.emme.matrix as ematrix
import inro.emme.database.matrix
import inro.emme.database.emmebank as _eb
import sys, getopt
import json


# This script converts Emme matrices to OMX and vice versa.
input_path = sys.argv[1]
output_path = sys.argv[2]
scenario_id = sys.argv[3]

# An optional json file of matrix names in list format:
try:
    matrix_list_file = sys.argv[4]
except IndexError:
    matrix_list_file = None

# Convert Emme matrices to OMX.
# Requires full paths for emmebank and OMX output. 
# Optional arguments may specify list of matrices to convert and scenario number, for zone numbering.  
 
def emme2omx(emmebank_file, omx_file_name, emme_matrix_list = None, scenario_number = None):
    
    emmebank = _eb.Emmebank(emmebank_file)                          # Access the emmebank with Emme libraries
    all_emme_matrices = emmebank.matrices()                          # Create a list of all matrices in emmebank

    # If no matrix subset list provided, convert all matrices in emmebank.
    if emme_matrix_list is None:
        emme_matrices = all_emme_matrices
    else:
        emme_matrices = []
        for item in emme_matrix_list:
            emme_matrices.append(emmebank.matrix(item))
        
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
    
     #Map zone numbers to matrix indeces.
    try:
        zones = tuple(current_scenario.zone_numbers)
        omx_file.createMapping('taz', zones)                    
    except AttributeError:
        print "ERROR: No zone numbers found for this scenario. Check scenario is valid, or leave input blank to use default scenario."            
            
    # Create OMX matrix for each Emme matrix specified.         
    for emme_matrix in emme_matrices:    
        if emme_matrix.type == 'FULL':                              # Only FULL matrices can be handled by OMX. 
            matrix_data = emme_matrix.get_data(scenario_number)
            numpy_matrix = np.matrix(matrix_data.raw_data)  
            omx_file[emme_matrix.name] = numpy_matrix
            print str(emme_matrix.name) + " added to OMX."               
        else:
            print "WARNING: Matrix '" + str(emme_matrix.name) + "' not FULL type and was not be converted. OMX only handles FULL matrices."
    emmebank.dispose()      
    omx_file.close()
           
# Convert OMX to Emme matrix files

def omx2emme(omx_file_name, emmebank_file, matrix_list = None, scenario_number = None):

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
        zones = current_scenario.zone_numbers
    except AttributeError:
        print "ERROR: No zone numbers found for this scenario. Check scenario is valid, or leave input blank to use default scenario."            

    # Load OMX matrix data
    

    omx_file = omx.openFile(omx_file_name, 'r')

    if matrix_list is None:
        matrix_list = omx_file.listMatrices()

    for omx_matrix_name in matrix_list:                         # Cycle through all matrices in OMX file
        np_matrix = np.matrix(omx_file[str(omx_matrix_name)])                    # Create NumPy array of OMX data
        np_matrix = np_matrix.astype(float)                                 
        np_array = np.squeeze(np.asarray(np_matrix))                       
        np_array_resize = np.resize(np_array, [len(zones), len(zones)])     # Set array size to match zones
        emme_matrix = ematrix.MatrixData(indices=[zones,zones],type='f')    
        emme_matrix.raw_data = [_array.array('f',row) for row in np_array_resize]
        print "Processing " + str(omx_matrix_name)

        # Test if matrix exists in emmebank. If not create new one. 
        if emmebank.matrix(omx_matrix_name) is None:
             new_id = emmebank.available_matrix_identifier("FULL") 
             new_matrix = emmebank.create_matrix(new_id) 
             new_matrix.name = omx_matrix_name
             print str(omx_matrix_name) + " does not exist. Creating new Emme matrix."
             
        matrix_id = emmebank.matrix(omx_matrix_name).id   
        emmebank.matrix(matrix_id).set_data(emme_matrix,current_scenario)   # Write data to OMX matrix

    emmebank.dispose()   
    omx_file.close()


def main():
    if matrix_list_file is not None:
        with open (matrix_list_file, 'r') as f:
            matrix_list = json.load(f)      
    else:
        matrix_list = None
        
    if 'emmebank' in input_path:
        emme2omx(input_path, output_path, matrix_list, scenario_id)
    else:
        omx2emme(input_path, output_path, matrix_list, scenario_id)

  

if __name__ == "__main__":
    main()