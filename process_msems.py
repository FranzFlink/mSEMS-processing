import pandas as pd
import os
import numpy as np
import xarray as xr
import argparse


def read_data(file_name, raw):
    # Skip the initial configuration lines
    if raw:
        data = pd.read_csv(file_name, skiprows=55, delimiter='\t')

        raw_bin_cols = [col for col in data.columns if 'bin' in col]

        dia = np.arange(len(raw_bin_cols))
        conc = data[raw_bin_cols]

    else:        
        data = pd.read_csv(file_name, skiprows=56, delimiter='\t')

        bin_dia_cols = [col for col in data.columns if 'bin_dia' in col]
        bin_conc_cols = [col for col in data.columns if 'bin_conc' in col]
        if len(bin_dia_cols) == 0:
            bin_dia_cols = [col for col in data.columns if 'Dia' in col]
            bin_conc_cols = [col for col in data.columns if 'Conc' in col]

        dia = data[bin_dia_cols]
        conc = data[bin_conc_cols]


    num_rows = data.shape[0]
    print('Number of rows: ', num_rows)



    try: 
        time = data['#YY/MM/DD']+'T'+data['HR:MN:SC']
        time = pd.to_datetime(time, format='%y/%m/%dT%H:%M:%S')

    except KeyError:
        time = data['#Date']+'T'+data['Time']        
        time = pd.to_datetime(time, format='%y/%m/%dT%H:%M:%S')

    return dia, conc, time


def data_to_netcdf(data, output_dir,raw=False):

    bin, conc, time = read_data(data, raw)
    bin = np.array(bin, dtype=np.float32)
    conc = np.array(conc, dtype=np.float32)

    name = data.split('/')[-1].split('.')[0]


    ### JM this should still be changed; right now the average bin is taken and not interpolated to the same bin size

    if len(bin.shape) == 1:
        bin_mean = bin
    else: 
        bin_mean = bin.mean(axis=0)


    xr_data = xr.DataArray(conc, dims=['time', 'bin'], coords={'time': time, 'bin': bin_mean})

    xr_data = xr_data.to_dataset(name='conc').to_netcdf(f'{output_dir}{name}.nc')

    ### JM still the metadata is missing; this should be added
    ### time, place, sheath air blabla


    if raw:
        xr_data.attrs['raw'] = True
    else:
        xr_data.attrs['raw'] = False




    return xr_data


if __name__ == '__main__':


    parser = argparse.ArgumentParser(description='Converts a raw or processed mSEMS data file to netcdf')

    parser.add_argument('--file', type=str, help='Path to the data file')
    parser.add_argument('--raw', help='If the data is raw or processed')
    parser.add_argument('--output_dir', type=str, help='Path to the output directory')

    args = parser.parse_args()

    data_to_netcdf(args.file, args.output_dir, args.raw)




