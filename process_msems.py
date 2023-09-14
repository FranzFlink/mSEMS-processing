### Here should be some documentation




import pandas as pd
import os
import numpy as np
import xarray as xr
import argparse

def check_file_type(file_name):
    """
    Determine the type of the file based on specific keywords.
    
    Parameters:
    - file_name (str): Path to the data file.
    
    Returns:
    - file_type (str): Type of the file (e.g., 'uav', 'igor', 'raw').
    - metadata_dict (dict): Dictionary containing metadata extracted from the file.
    - properties (dict): Dictionary containing properties specific to the detected file type.
    """
    
    # Mapping of keywords/phrases to their corresponding file types
    keyword_mapping = {
        '#UAV Reader Version': 'uav',
        '#Date': 'igor',
        '#YY/MM/DD': 'raw'
    }

    file_type = []

    type_property_dict = { 
        'igor': {'columns': ['Bin_Dia', 'Bin_Conc'],
                 'skiprows': 56,
                 'delimiter': '\t',
                 'date_col' : '#Date',
                 'time_col' : 'Time'
        },
        'uav': {'columns': ['bin_dia', 'bin_conc'],
                'skiprows': 56,
                'delimiter': '\t',
                'date_col' : '#YY/MM/DD',
                'time_col' : 'HR:MN:SC'
        },
        'raw': {'columns': ['bin'],
                'skiprows': 55,
                'delimiter': '\t',
                'date_col' : '#YY/MM/DD',
                'time_col' : 'HR:MN:SC'
        },
    }

    
    metadata_dict = {}

    with open(file_name, 'r') as f:
        for line in f:
            # Only check lines that start with #
            if line.startswith("#"):
                if ':' in line and 'scan_direction' not in line:
                    key, value = line.split(':')
                    key = key.strip('#').strip()
                    value = value.strip('\n')
                    metadata_dict[key] = value

                for keyword, ftype in keyword_mapping.items():
                    if keyword in line:
                        file_type.append(ftype)
    

    # Ensure only one file type was found; use the first detected type
    file_type = file_type[0]


    return file_type, metadata_dict, type_property_dict[file_type]



def read_data(file_name, file_type, type_property_dict,):
    """
    Read data from the file based on its type and properties.
    
    Parameters:
    - file_name (str): Path to the data file.
    - file_type (str): Type of the file.
    - properties (dict): Dictionary containing properties specific to the file type.
    
    Returns:
    - dia (pd.DataFrame): DataFrame containing diameter values.
    - conc (pd.DataFrame): DataFrame containing concentration values.
    - time (pd.Series): Series containing timestamp values.
    """

    data = pd.read_csv(file_name, skiprows=type_property_dict['skiprows'], delimiter=type_property_dict['delimiter'])


    ### JM Handling the raw-data case explictly, as there is only one bin there...

    if len(type_property_dict['columns']) == 1:

        conc = data[[col for col in data.columns if type_property_dict['columns'][0] in col]]
        dia  = np.arange(1, conc.shape[1]+1)

    else:



        dia = data[[col for col in data.columns if  type_property_dict['columns'][0] in col]]
        conc = data[[col for col in data.columns if type_property_dict['columns'][1] in col]]

    num_rows = data.shape[0]
    print('Number of Scans: ', num_rows)
    
    time = data[type_property_dict['date_col']]+'T'+data[type_property_dict['time_col']]
    time = pd.to_datetime(time, format='%y/%m/%dT%H:%M:%S')

    return dia, conc, time


def data_to_netcdf(data, output_dir, filename, metadata_dict=None, file_type=None):
    """
    Convert data to netCDF format.
    
    Parameters:
    - data (tuple): Tuple containing diameter, concentration, and timestamp data.
    - output_dir (str): Directory to save the netCDF file.
    - filename (str): Name of the original data file.
    - metadata_dict (dict, optional): Dictionary containing metadata.
    - file_type (str, optional): Type of the original file.
    
    Returns:
    - xr_data (xr.DataArray): DataArray containing the converted data.
    """


    bin, conc, time = data
    bin = np.array(bin, dtype=np.float32)
    conc = np.array(conc, dtype=np.float32)

    name = filename.split('/')[-1].split('.')[0]


    ### JM this should still be changed; right now the average bin is taken and not interpolated to the same bin size

    if len(bin.shape) == 1:
        bin_mean = bin
    else: 
        bin_mean = bin.mean(axis=0)


    xr_data = xr.DataArray(conc, dims=['time', 'bin'], coords={'time': time, 'bin': bin_mean})


    ### JM add metadata to the netcdf file

    xr_data.attrs = metadata_dict
    xr_data.attrs['file_type'] = file_type

    ### JM save the netcdf file
    
    xr_data.to_dataset(name='conc').to_netcdf(f'{output_dir}{name}.nc')


    return xr_data



if __name__ == '__main__':


    parser = argparse.ArgumentParser(description='Converts raw, igor-inverted or uav-reader-inverted mSEMS data file to netcdf')

    parser.add_argument('--file', type=str, required=True,help='Path to the data file')
    parser.add_argument('--output_dir', type=str, default=os.getcwd(),help='Path to the output directory')

    args = parser.parse_args()

    if not args.output_dir.endswith('/'):
        args.output_dir += '/'

    
    file_type, metadata_dict, type_property_dict = check_file_type(args.file)
    print('File type: ', file_type)

    data = read_data(args.file, file_type, type_property_dict)

    data_to_netcdf(data, args.output_dir, args.file, metadata_dict=metadata_dict, file_type=file_type)

    print('Done!')


