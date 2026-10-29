import sqlite3

conn = sqlite3.connect("vehicle_history.db")
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS master_te1")
#cursor = conn.cursor()
#cursor.execute('''
#UPDATE parts_history
#SET eta = substr(eta, 1, 10)
#    '''
#)

conn.commit()
conn.close()
print("Timestamps updated successfully.")
