import gdal
import netCDF4   
import osr   
import sys
import os
from netCDF4 import Dataset

def find_location_values(fileHandle, numberOfHruCells, position):

    """
    
    Returns the values of variables in the file. 

    Args:
        numberOfDays (int): is the total number of values for the variable
	position (int): is the column position from where the values can be 
        retrieved
    
    """

    values = []
   
    for i in range(numberOfHruCells):
	valuesInLine = fileHandle.next().strip().split()
        values.append(valuesInLine[position])
    
    return values

def find_column_values(fileHandle, totalNumberOfDataValues, numberOfMetadataLines, position):
    
    """
    
    Returns the values of variables in the file. 

    Args:
        numberOfDays (int): is the total number of values for the variable
	position (int): is the column position from where the values can be 
        retrieved
    
    """

    values = []

    for i in range(numberOfMetadataLines):
	fileHandle.next()
    
    for j in range(2):
	fileHandle.next()
    
    for k in range(totalNumberOfDataValues):
	valuesInLine = fileHandle.next().strip().split()[2:]
        values.append(valuesInLine[position])
    
    return values

def find_average_resolution(fileHandle, numberOfHruCells, numberOfRows, numberOfColumns):

    """
    
    Returns the values of variables in the file. 

    Args:
        numberOfDays (int): is the total number of values for the variable
	position (int): is the column position from where the values can be 
        retrieved
    
    """

    latitudeValues = []
    longitudeValues = []
   
    for i in range(numberOfHruCells):
	valuesInLine = fileHandle.next().strip().split()
        longitudeValues.append(float(valuesInLine[1]))
	latitudeValues.append(float(valuesInLine[2]))

    minimumLatitudeValue = min(latitudeValues)
    maximumLatitudeValue = max(latitudeValues)

    minimumLongitudeValue = min(longitudeValues)
    maximumLongitudeValue = max(longitudeValues)

    averageOfLatitudeValues = (maximumLatitudeValue-minimumLatitudeValue)/numberOfRows
    averageOfLongitudeValues = (maximumLongitudeValue-minimumLongitudeValue)/numberOfColumns
 
    latitudeOfFirstHru = latitudeValues[0]
    longitudeOfFirstHru = longitudeValues[0]

    return averageOfLatitudeValues, averageOfLongitudeValues, latitudeOfFirstHru, longitudeOfFirstHru

def add_metadata(outputVariableName):

    projectRoot = os.path.dirname(os.path.dirname(__file__))
    fileLocation = os.path.join(projectRoot, 'variableDetails/outputVariables.txt')
    fileHandle = open(fileLocation, 'r')
    for line in fileHandle:
        if outputVariableName in line:
	    outputVariableNameFromFile = line.strip()		
	    lengthOfOutputVariableName = len(outputVariableNameFromFile)
	    positionOfNameStart = outputVariableNameFromFile.index(':') + 2
 	    outputVariableName = outputVariableNameFromFile[positionOfNameStart:lengthOfOutputVariableName]
		
	    outputVariableDescriptionFromFile = fileHandle.next().strip()
	    lengthOfOutputVariableDescription = len(outputVariableDescriptionFromFile)
	    positionOfDescriptionStart = outputVariableDescriptionFromFile.index(':') + 2
	    outputVariableDescription = outputVariableDescriptionFromFile[positionOfDescriptionStart:lengthOfOutputVariableDescription]
		
	    outputVariableUnitFromFile = fileHandle.next().strip()
	    lengthOfOutputVariableUnit = len(outputVariableUnitFromFile)
	    positionOfUnitStart = outputVariableUnitFromFile.index(':') + 2
	    outputVariableUnit = outputVariableUnitFromFile[positionOfUnitStart:lengthOfOutputVariableUnit]
		
	    break;

    return outputVariableName, outputVariableDescription, outputVariableUnit

def extract_row_column_hru_information(parameterFile):

    fileHandle = Dataset(parameterFile, 'r')
    attributes = fileHandle.ncattrs()    
    for attribute in attributes:
        if attribute == 'number_of_hrus':
            numberOfHruCells = int(repr(str(fileHandle.getncattr(attribute))).replace("'", ""))
	if attribute == 'number_of_rows':
            numberOfRows = int(repr(str(fileHandle.getncattr(attribute))).replace("'", ""))
        if attribute == 'number_of_columns':
            numberOfColumns = int(repr(str(fileHandle.getncattr(attribute))).replace("'", ""))

    return numberOfHruCells, numberOfRows, numberOfColumns

def extract_lat_and_lon_information(parameterFile):

    fileHandle = Dataset(parameterFile, 'r')
    latitude = 'lat'
    latitudeValues = fileHandle.variables[latitude][:]
    longitude = 'lon'
    longitudeValues = fileHandle.variables[longitude][:]
    
    return latitudeValues, longitudeValues


def animation_to_netcdf(animationFile, parameterFile, outputFileName):

    values = extract_row_column_hru_information(parameterFile)    
    numberOfHruCells = values[0]
    numberOfRows = values[1]
    numberOfColumns = values[2]

    values = extract_lat_and_lon_information(parameterFile)
    latitudeValues = values[0]
    longitudeValues = values[1]
    
    numberOfMetadataLines = 0
    timeValues = []
    numberOfHRUValues = [] 
        
    fileHandle = open(animationFile, 'r')
    totalNumberOfLines = sum(1 for _ in fileHandle)

    fileHandle = open(animationFile, 'r')
    for line in fileHandle:
	if '#' in line:
            numberOfMetadataLines = numberOfMetadataLines + 1
    
    totalNumberOfDataValues = totalNumberOfLines-(numberOfMetadataLines+2)
    numberOfTimestamps = totalNumberOfDataValues/(numberOfRows*numberOfColumns)
    
    fileHandle = open(animationFile, 'r')
    for i in range(numberOfMetadataLines):
	fileHandle.next()
    outputVariableNames = fileHandle.next().strip().split()[2:]
    fileHandle.next()
    firstDate = fileHandle.next().strip().split()[0]     
	
    # Initialize new dataset
    ncfile = netCDF4.Dataset(outputFileName, mode='w')

    # Initialize dimensions
    time_dim = ncfile.createDimension('time', numberOfTimestamps)  
    nrows_dim = ncfile.createDimension('lat', numberOfRows)
    ncols_dim = ncfile.createDimension('lon', numberOfColumns)

    time = ncfile.createVariable('time', 'i4', ('time',))
    time.long_name = 'time'  
    time.units = 'days since '+firstDate
    for index in range(numberOfTimestamps):
	timeValues.append(index+1)	
    time[:] = timeValues
   
    lat = ncfile.createVariable('lat', 'f8', ('lat',))
    lat.long_name = 'latitude'  
    lat.units = 'degrees_north'
    lat[:] = latitudeValues

    lon = ncfile.createVariable('lon', 'f8', ('lon',))
    lon.long_name = 'longitude'  
    lon.units = 'degrees_east'
    lon[:] = longitudeValues

    sr = osr.SpatialReference()
    sr.ImportFromEPSG(4326)
    crs = ncfile.createVariable('crs', 'S1',)
    crs.spatial_ref = sr.ExportToWkt()

    for index in range(len(outputVariableNames)):

	metadata = add_metadata(outputVariableNames[index])
	outputVariableName = metadata[0]
	outputVariableDescription = metadata[1]
	outputVariableUnit = metadata[2]

	var = ncfile.createVariable(outputVariableNames[index], 'f8', ('time', 'lat', 'lon')) 
	var.layer_name = outputVariableName
	var.layer_desc = outputVariableDescription
        var.layer_units = outputVariableUnit
	var.grid_mapping = "crs" 
	
        fileHandle = open(animationFile, 'r')
        columnValues = find_column_values(fileHandle, totalNumberOfDataValues, numberOfMetadataLines, index)		
	var[:] = columnValues

    # Global attributes
    ncfile.title = 'PRMS Animation File'
    ncfile.nsteps = 1
    ncfile.bands_name = 'nsteps'
    ncfile.bands_desc = 'Variable information for ' + animationFile
    
    # Close the 'ncfile' object
    ncfile.close()
    

if __name__ == "__main__":

    numberOfArgs = len(sys.argv)
    
    for i in range(numberOfArgs):
        if sys.argv[i] == "-data":
	    animationFile = sys.argv[i+1]

    animation_to_netcdf(animationFile, 'parameter.nc', 'animation.nc')
  



