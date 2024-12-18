import pandas, sqlite3
import sys, os

database_fn = sys.argv[1]

db_sqlite_conn = sqlite3.connect(database_fn)
data = pandas.read_csv('./data-preparation/resources/QSWATPlus/SWATPlus/Databases/plant.csv')

data.to_sql('plant', db_sqlite_conn, if_exists='replace', index=False)
data.to_sql('plants_plt', db_sqlite_conn, if_exists='replace', index=False)

db_sqlite_conn.close()