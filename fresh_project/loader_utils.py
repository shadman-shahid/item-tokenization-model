import pandas as pd


def get_columns(file_path: str):
    '''
    Function to read the first line of a csv file and return a list of column names.
    :param file_path: file path to csv file
    :return: column names
    '''
    with open(file_path, 'r') as file:
        contents = file.readline()
    return contents.strip().split(sep=',')


# # Old functions to deal with unclean csv files. Not needed now
# # Function to read an unclean csv file of customer data and return a generator of dictionaries to be used by pandas
# Dataframe class to return a dataframe.
def get_customer_rows(file_path):
    with open(file_path, 'r') as file:
        contents = file.readlines()
    for i, line in enumerate(contents):
        words = line.split(sep=', ')
        if len(words) > 5:
            yield {'CustomerCode': words[0], 'CustomerName': ' '.join(words[1:-3]), 'DepotCode': words[-3],
                   'AvgNSI': words[-2], 'InvCnt': words[-1]}
        else:
            yield {'CustomerCode': words[0], 'CustomerName': words[1], 'DepotCode': words[2], 'AvgNSI': words[3],
                   'InvCnt': words[4]}


def get_product_rows(product_file_path):
    with open(product_file_path, 'r') as file:
        contents = file.readlines()
    columns = get_columns(product_file_path)
    for i, line in enumerate(contents[1:]):
        words = line.strip().split(sep=', ')
        if len(words) > len(columns):
           yield {columns[i]: words[i] if i == 0 else ' '.join(words[1:-len(columns)+2]) if i ==1 else words[-(len(columns) - i)] for i in range(len(columns))}
        else:
            yield {column: word for column, word in zip(columns, words)}

def create_clean_customer_csv(file_path, return_df=False):
    '''
    Function to create a pandas dataframe from an unclean csv file of customer data.
    :param file_path: file path to csv file
    :return: pandas dataframe
    '''

    customers = pd.DataFrame(get_rows(file_path), )
    customers.InvCnt = customers.InvCnt.apply(lambda x: int(x))
    customers.AvgNSI = customers.AvgNSI.apply(lambda x: float(x))
    customers.CustomerName = customers.CustomerName.apply(lambda x: x.strip('"'))
    customers.CustomerCode = customers.CustomerCode.apply(lambda x: x.strip('"'))
    customers.DepotCode = customers.DepotCode.apply(lambda x: x.strip('"'))
    customers.to_csv(file_path[:-4] + '_clean.csv', index=False)
    if return_df:
        return customers
