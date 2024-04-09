import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

data_one = pd.read_excel("./BankOperationMockData_银行经营数据-1-bank-overview.xlsx")
engine = create_engine('mysql+pymysql://<username>:<password>@localhost:3306/bank_operation_demo')

if not database_exists(engine.url):
    create_database(engine.url)
    
data_one.to_sql(name='bank_overview', con=engine, if_exists='replace', index=False)

data_two = pd.read_excel("./BankOperationMockData_银行经营数据-2-bank-segment.xlsx")
engine = create_engine('mysql+pymysql://<username>:<password>@localhost:3306/bank_operation_demo')
data_two.to_sql(name='bank_segment', con=engine, if_exists='replace', index=False)