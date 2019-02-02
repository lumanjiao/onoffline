#encoding=utf-8
import os
import psycopg2
file_path = '/home/gpadmin/data_dump/st_onoffline.txt'
def two(cursor):
		num = 0
		with open(file_path, 'r') as f:
				for l in f:
						tup = l.rstrip('\n').rstrip().split('\t')
						print tup
						if checkgp(cursor,tup)==1:
							print "查询结果为空"
							insertgp(cursor,tup)
						num = num+1
		print num

def insertgp(cursor,data):
		query = 'Insert into audit_data.st_onoffline values(\''+data[1]+'\',\''+data[2]+'\',\''+data[3]+'\',\''+data[4]+'\',\''+data[5]+'\')'
		print query
		cursor.execute(query)
		
def checkgp(cursor,data):
	query = 'select last_online, last_offline from audit_data.st_onoffline where routermac=\''+data[1]+'\'and endmac=\''+ data[2]+'\'and ip=\''+data[3]+'\'and last_online=\''+data[4]+'\'and last_offline=\''+data[5]+'\''
	print query
	cursor.execute(query)
	rows = cursor.fetchall()
	if rows:
		print "check any"
		print rows
		return 0
	else:
		print "check none"
		return 1
			

print "start"
conn = psycopg2.connect(database="police_center_src_db", user="gpadmin",password="gpadmin", host="127.0.0.1", port="5432")
cursor = conn.cursor()
two(cursor)
conn.commit()
cursor.close()
conn.close()
print "over"
