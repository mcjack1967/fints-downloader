import logging
from os import getenv
from dotenv import load_dotenv
import datetime
from decimal import Decimal
from fints.client import FinTS3PinTanClient, NeedTANResponse
from mt940 import models
import flatdict
import hashlib
import json
import argparse
from dateutil.relativedelta import relativedelta

def load_transactions(
    client: FinTS3PinTanClient, start_date: datetime = None, end_date: datetime = None
) -> list:
    """
    Load all transactions between start_date and end_date
    of a FinTS client connection.
    """
    with client:
        accounts = client.get_sepa_accounts()
        results = []

        for account in accounts:

            result = client.get_transactions(account, start_date, end_date)

            if type(result) == NeedTANResponse:
                tan = input("Enter tan:")
                result = client.send_tan(result, tan)

            # add iban from account as key to the data set
            for entry in result:
                entry.data["iban"] = account.iban
                # for transactions add only the data
                results.append(entry.data)

    return results


def load_balances(client: FinTS3PinTanClient):
    with client:
        accounts = client.get_sepa_accounts()
        balances = []
        for account in accounts:

            # add iban from account as key to the data set
            balances.append(
                {"iban": account.iban, "balance": client.get_balance(account)}
            )

    return balances


def load_accounts(client: FinTS3PinTanClient):
    with client:
        return client.get_sepa_accounts()


def get_FinTS_client(
    bank_code: str,
    login_name: str,
    login_pin: str,
    hbci_endpoint: str,
    product_id: str,
    log_level=logging.INFO,
):
    """
    Creates a FinTS client and sets the log level (default=ERROR)
    """
    logging.basicConfig(level=log_level)

    return FinTS3PinTanClient(
        bank_code, login_name, login_pin, hbci_endpoint, product_id=product_id
    )


def convert_objects_to_dicts(input: list):
    """
    Converts a list of objects 
        - SEPA Account
        - Balance (mt940.models)
        - Transaction (mt940.models)
    to a list of dictonaries
    """
    output = []

    for element in input:
        tmp_dict = {}

        # SEPA Account hasnt the '__dict__' attribute
        if "_fields" in dir(element):
            for idx, item in enumerate(element._fields):
                tmp_dict[item] = element[idx]

        # Use the '__dict__' attribute balance and transactions
        elif "__dict__" in dir(element):
            tmp_dict = element.__dict__

        elif type(element) == dict:
            tmp_dict = element

        tmp_dict = convert_object_to_dict(tmp_dict)
        # direct '_' doesnt work, so i used '|' and replace it later
        tmp_dict = dict(flatdict.FlatDict(tmp_dict, delimiter="|"))
        keys = list(tmp_dict.keys())
        for k in keys:
            tmp_dict[k.replace("|", "_")] = tmp_dict.pop(k)

        output.append(tmp_dict)

    return output

def save_json(data, file):
    with open(file , "w") as fp:
        json.dump(data, fp) 

    logging.info(f"File {file} saved")


def convert_object_to_dict(object):
    output = {}

    for x in object:

        if type(object[x]) == str:
            output[x] = object[x]
        elif type(object[x]) == Decimal:
            output[x] = float(object[x])
        elif type(object[x]) == datetime.date:
            output[x] = object[x].strftime("%Y-%m-%d")
        elif type(object[x]) == datetime.datetime:
            output[x] = object[x].strftime("%Y-%m-%d %H:%M:%S")
        elif type(object[x]) == models.Date:
            output[x] = datetime.datetime(
                year=object[x].year, month=object[x].month, day=object[x].day
            ).strftime("%Y-%m-%d")
        # empty key will be ignored
        elif (object[x] is None) or (
            type(object[x]) in (list, dict) and len(object[x]) == 0
        ):
            pass
        elif "__dict__" in dir(object[x]) and len(object[x].__dict__) > 0:
            output[x] = convert_object_to_dict(object[x].__dict__)
        else:
            raise Exception("Unknown data type: ", type(output[x]))

    return output


def get_uid_for_dict(dict):
    unique_str = "".join(
        ["'%s':'%s'||" % (key, val) for (key, val) in sorted(dict.items())]
    )
    return hashlib.md5(unique_str.encode()).hexdigest()


def main():

    load_dotenv()
    FINTS_BANK_LOGINS = getenv("FINTS_BANK_LOGINS")
    FINTS_PRODUCT_ID = getenv("FINTS_PRODUCT_ID")

    print(FINTS_BANK_LOGINS)

    DATA_PATH = getenv("DATA_PATH")

    parser = argparse.ArgumentParser(
                    prog='Fints data downlaoder',
                    description='''
                        This Python script allows users to download 
                        financial data using fints and export the data 
                        to JSON files. The script uses the python-fints 
                        library to connect to financial institutions and 
                        retrieve data using the HBCI protocol.'''
                    )
    
    parser.add_argument('--start-date', default=None, help='Start date for transactions')
    parser.add_argument('--data-path', default=DATA_PATH, help='Path for json outputs')  

    args = parser.parse_args()
    
    bank_logins = json.loads(FINTS_BANK_LOGINS)

    for bank in bank_logins:

        # load required arguments from enviroment vars
        client = get_FinTS_client(
            bank_logins[bank]["FINTS_BANK_CODE"],
            bank_logins[bank]["FINTS_LOGIN_NAME"],
            bank_logins[bank]["FINTS_LOGIN_PIN"],
            bank_logins[bank]["FINTS_HBCI_ENDPOINT"],
            FINTS_PRODUCT_ID,
        )

        file_prefix = f"{bank}_"

        ### accounts ###
        save_json(data=convert_objects_to_dicts(load_accounts(client))
                , file=args.data_path + file_prefix + "accounts.json")

        ### balance ###
        save_json(data=convert_objects_to_dicts(load_balances(client))
                , file=args.data_path + file_prefix + "balance.json")

        ### transactions ###
        start_date = args.start_date

        if start_date is None:
            start_date = (datetime.datetime.now() - relativedelta(months=1)).strftime('%Y-%m-%d')
        logging.info(f"Start date is set to {start_date}")
        save_json(data=convert_objects_to_dicts(load_transactions(client, datetime.datetime.strptime(start_date, "%Y-%m-%d")))
                , file=args.data_path + file_prefix + "transactions.json")

if __name__ == "__main__":
    main()
