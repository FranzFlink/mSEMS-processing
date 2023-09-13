import pandas as pd
import matplotlib.pyplot as plt

def read_data(file_name):
    # Skip the initial configuration lines
    data = pd.read_csv(file_name, skiprows=55, delimiter='\t')
    return data

def plot_data(data):
    # Select only the bin columns
    bins = data.filter(regex='bin')
    
    # Plot each bin
    for column in bins.columns:
        plt.plot(data[column], label=column)
    
    plt.xlabel('Time')
    plt.ylabel('Concentration')
    plt.title('Concentrations and their bins')
    plt.legend()
    plt.show()

def main():
    file_name = "/home/josh/OneDrive/TROPOS/mSMES/Data - Copy/mSEMS_107_230807_100619_SCAN.txt"
    data = read_data(file_name)
    plot_data(data)

if __name__ == "__main__":
    main()