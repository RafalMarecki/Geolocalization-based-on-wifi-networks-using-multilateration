import fileinput

# Change commas in SSIDS from client data
def change_commas_to_periods_SSIDS(filename):
    with fileinput.FileInput(filename, inplace=True) as f:
        for line in f:
            commas = []
            if line.count(',') > 2:
                # Getting positions of commas
                for pos,char in enumerate(line):
                    if(char == ','):
                        commas.append(pos)
                # Changing commas to periods, but not the last two 
                for compos in range(len(commas) - 2):
                    line = line[:commas[compos]] + '.' + line[commas[compos] +1:]
            print(line, end='')

# Change commas in SSIDS from sniffer data
def change_commas_to_periods_SSIDS_sniffer(filename):
    with fileinput.FileInput(filename, inplace=True) as f:
        for line in f:
            commas = []
            if line.count(',') > 10:
                # Getting positions of commas
                for pos,char in enumerate(line):
                    if(char == ','):
                        commas.append(pos)
                # Changing commas to periods, but not the last two 
                for compos in range(3, len(commas)-7):
                    line = line[:commas[compos]] + '.' + line[commas[compos] +1:]
            print(line, end='')

# Merge two lists into a touple
def merge(list1, list2):
    merged_list = [(list1[i], list2[i]) for i in range(0, len(list1))]
    return merged_list

