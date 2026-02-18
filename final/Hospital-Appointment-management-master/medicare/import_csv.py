import sqlite3, sys, pandas as pd

if len(sys.argv)<2:
    print('Usage: python import_csv.py <file.csv>')
    sys.exit(1)

file=sys.argv[1]
df=pd.read_csv(file)

conn=sqlite3.connect('hospital.db')
for _,row in df.iterrows():
    conn.execute('INSERT INTO appointments (patient_id,date,time,status) VALUES (?,?,?,?)',
                 (1,row.get('date','2025-01-01'),row.get('time','10:00'),'Scheduled'))
conn.commit()
conn.close()
print('Imported CSV into appointments')
