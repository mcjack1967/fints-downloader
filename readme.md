# Python FinTS Loader

This script downloads the account, current balances and the transactions of these accounts and stores the data as csv-file. A automatic historization of the balances will be created. 

Are the transactions older than three month, you have to enter a TAN. For the next time the script will get the max transaction date and loads all transactions which are >= this date.

The following enviroment variables must be set via `.env`-file:

```
FINTS_PRODUCT_ID
FINTS_BANK_LOGINS='{"bank_1":{"FINTS_BANK_CODE":"bank_code_1",
                           "FINTS_LOGIN_NAME":"username_1",
                           "FINTS_LOGIN_PIN":"pin_1",
                           "FINTS_HBCI_ENDPOINT":"endpoint_1"},
                    "bank_2":{"FINTS_BANK_CODE":"bank_code_2",
                           "FINTS_LOGIN_NAME":"username_2",
                           "FINTS_LOGIN_PIN":"pin_2",
                           "FINTS_HBCI_ENDPOINT":"endpoint_2"}}'
```
How to fill these variables look in the [documentation](https://python-fints.readthedocs.io/en/latest/quickstart.html). 
The enviroment variable `FINTS_BANK_LOGINS` is a dictornary to load data from different banks.

You can also set the path for the data outputs via enviroment variable:

```
DATA_PATH="/usr/app/data/"
```

You can overwrite the data path with the argument `--data-path /usr/app/data/`. 
To set the start date for the transactions you can add the argument `--start-date 2000-01-01` 
otherwise the start date will set to today minus one month.

