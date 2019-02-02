#!/bin/bash

yunying_username="root"
yunying_password="root123"
gongan_ip="211.68.46.31"
count_path="/home/onoffline/count.txt"
txt_file="/home/onoffline/st_onoffline.txt"
log_file="/home/onoffline/onoffline.log"
mysqldump_path="/usr/bin/mysqldump"
#
echo -n `date "+%Y-%m-%d %H:%M:%S"` >> $log_file
echo ":Start to insert data!" >>$log_file
#读取count.txt的值 
count=`cat $count_path`
echo $count
#-u后面是运营端的数据库用户名，-p后面是运营端数据库的密码,根据实际情况来修改
$mysqldump_path -h localhost -u$yunying_username -p$yunying_password  wifi_operation st_onoffline -t -T/home/onoffline --fields-terminated-by='\t' --where=" id > $count "
echo $count
#211.68.46.31应该根据实际公安端修改ip
if [ ! -s "$txt_file" ]; then
	echo "当前已导出最新数据！"
	exit
fi
new=`sed -n '$p' $txt_file|awk '{print $1}'`
echo $new > $count_path
scp $txt_file root@${gongan_ip}:/home/gpadmin/data_dump
echo -n `date "+%Y-%m-%d %H:%M:%S"` >> $log_file
echo ":Finish to insert data!" >>$log_file

