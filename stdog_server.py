#!/usr/local/bin/python3
#coding=utf-8

#version:1.2.1
#release notes:
#1.add wechat support
import sys,os
import socket
import select
#import multiprocessing
import time,datetime
import errno
import struct
import threading
#from M2Crypto import RSA
import traceback
import pymysql as MySQLdb
from urllib import request,parse
import random
#import rsa
import re
import json
import copy
import subprocess
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool


MySQLdb.install_as_MySQLdb()

default_auth_eff_time=86400
default_sms_eff_time=120
phone_authes={}
wechat_authes={}
devices={}
configs={}

#def rsa_pass_callback():
#	return "pwd123"

def mutex_acquire(tmutex):
	try:
		tmutex.acquire()
		return 0
	except:
		return 1

def mutex_release(tmutex):
	try:
		tmutex.release()
	except:
		pass

def isphone(phone):
	if len(str(phone)) != 11:#phone length is 11
		return 1
	if not re.match("^1[0-9]{10}$",str(phone)):
		return 1
	return 0

def ismac(mac):
	if len(str(mac)) != 17:#mac length is 17
		return 1
	if not re.match("^[0-9a-zA-Z]{2}:[0-9a-zA-Z]{2}:[0-9a-zA-Z]{2}:[0-9a-zA-Z]{2}:[0-9a-zA-Z]{2}:[0-9a-zA-Z]{2}$",str(mac)):
		return 1
	return 0

def iscode(code):
	if len(str(code)) != 6:#code length is 6
		return 1
	if not re.match("^[0-9]{6}$",str(code)):
		return 1
	return 0

def mac2long2str(mac):
	try:
		return str(int("0x"+str(mac).replace(":",""),16))
	except:
		traceback.print_exc()
		return 0

def long2mac2str(nummac):
	try:
		tmphex=str(hex(int(nummac)))[2:].upper()
		if len(tmphex) < 12:
			tmphex="0"*(12-len(tmphex))+tmphex
		elif len(tmphex) > 12:
			return ""
		return str(tmphex[0:2]+":"+tmphex[2:4]+":"+tmphex[4:6]+":"+tmphex[6:8]+":"+tmphex[8:10]+":"+tmphex[10:12]).upper()
	except:
		traceback.print_exc()
		return ""

def clean_fileno(fileno):
	global conn_state
	global conn_time
	global conn_addr
	global recv_data
	global send_data
	global gmutex
	try:
		mutex_acquire(gmutex)
		try:
			ep.unregister(fileno)
		except:
			pass

		try:
			try:
				conn_state[fileno].shutdown(2)
			except:
				pass
			try:
				conn_state[fileno].close()
			except:
				pass
			del conn_state[fileno]
#			if 0==len(conn_state.keys()):
#				conn_state.clear()
		except:
			pass

		try:
			del recv_data[fileno]
#			if 0==len(recv_data.keys()):
#				recv_data.clear()
		except:
			pass

		try:
			del send_data[fileno]
#			if 0==len(send_data.keys()):
#				send_data.clear()
		except:
			pass

		try:
			del conn_addr[fileno]
#			if 0==len(conn_addr.keys()):
#				conn_addr.clear()
		except:
			pass

		try:
			del conn_time[fileno]
#			if 0==len(conn_time.keys()):
#				conn_time.clear()
		except:
			pass
		mutex_release(gmutex)
	except:
		traceback.print_exc()

def clean_fileno_with_time(fileno):
	global conn_state
	global conn_time
	global conn_addr
	global recv_data
	global send_data
	global gmutex
	try:
		mutex_acquire(gmutex)
		tnow=int(time.time())
		if fileno not in conn_time.keys() or conn_time[fileno]+60>=tnow:
			mutex_release(gmutex)
			return
		try:
			ep.unregister(fileno)
		except:
			pass
		print("timeout:",fileno,conn_time[fileno])
		try:
			try:
				conn_state[fileno].shutdown(2)
			except:
				pass
			try:
				conn_state[fileno].close()
			except:
				pass
			del conn_state[fileno]
#			if 0==len(conn_state.keys()):
#				conn_state.clear()
		except:
			pass

		try:
			del recv_data[fileno]
#			if 0==len(recv_data.keys()):
#				recv_data.clear()
		except:
			pass

		try:
			del send_data[fileno]
#			if 0==len(send_data.keys()):
#				send_data.clear()
		except:
			pass

		try:
			del conn_addr[fileno]
#			if 0==len(conn_addr.keys()):
#				conn_addr.clear()
		except:
			pass

		try:
			del conn_time[fileno]
#			if 0==len(conn_time.keys()):
#				conn_time.clear()
		except:
			pass
		mutex_release(gmutex)
	except:
		traceback.print_exc()			
			
def close_timeout(arg):
	global conn_state
	global conn_time
	global conn_addr
	global recv_data
	global send_data
	global gmutex
	while True:
		try:
			now=int(time.time())
			already_timeout=[]
			mutex_acquire(gmutex)
			for key,value in conn_time.items():
				if value+60<now:
					already_timeout.append(key)
			mutex_release(gmutex)
			for fileno in already_timeout:
				clean_fileno_with_time(fileno)
		except:
			traceback.print_exc()
		time.sleep(60)
			
def mysql_init(mysql_host,mysql_port,mysql_user,mysql_pwd,mysql_db):
	try:
		conn=MySQLdb.connect(host=mysql_host,port=mysql_port,user=mysql_user,passwd=mysql_pwd,db=mysql_db,charset="utf8")
		return conn
	except:
		traceback.print_exc()
		return None

def mysql_close(cur,conn):
	try:
		if cur:
			cur.close()
	except:
		pass
		
	try:
		if conn:
			conn.commit()
	except:
		pass
		
	try:
		if conn:
			conn.close()
	except:
		pass
		
def mysql_get_cur(conn):
	try:
		cur=conn.cursor()
		cur.execute('SET NAMES utf8')
		cur.execute('SET CHARACTER SET utf8')
		cur.execute('SET character_set_connection=utf8')
		return cur
	except:
		traceback.print_exc()
		return None

def get_random_str(num):
	try:
		if num <= 0:
			return ""
		seed = "1234567890"#abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
		rstr=""
		for i in range(num):
			rstr+=str(random.choice(seed))
		return rstr
	except:
		traceback.print_exc()
		return ""
#function define
def _send_code_aliyun(phone):
	try:
		code=get_random_str(6)
		if not code:
			return ""
		if 0!=isphone(phone):
			return ""
		ret=subprocess.call("/usr/bin/python2 /root/alidayu/alidayu_python2.py "+str(phone)+" "+str(code),shell=True)
		if 0!=ret:
			return ""
		else:
			return code
	except:
		traceback.print_exc()
		return ""
def _send_code(phone):
	try:
		code=get_random_str(6)
		if not code:
			return ""
		postdata=parse.urlencode({"account":code_account,"pswd":code_pswd,"mobile":phone,"msg":code_msg+str(code)+code_msg_1}).encode('utf-8')
		req=request.Request(code_url,data=postdata)
		response=request.urlopen(req).read().decode('utf-8')
		if 0 != int(response.split(",")[1].strip()):
			return ""
	except:
		traceback.print_exc()
		return ""
	return code

#认证有效时间检查
def check_auth_time(last_auth_time,authed_channel,authed_place,authed_routermac):
	mutex_acquire(cmutex)
	authed_routermac=long2mac2str(int(authed_routermac))
	try:
		for config in configs['auth_eff_time']:
			try:
				if 'channel' in config['rule'].keys():#包含渠道配置
					if "-"+str(authed_channel) in config['rule']['channel']:#配置为非，设备肯定不在配置内，跳到下一个配置
						continue
					if str(authed_channel) in config['rule']['channel']:#已有认证信息的设备在配置内
						if config['time']+last_auth_time > int(time.time()):#认证在有效期
							mutex_release(cmutex)
							return 0
						else:#认证不在有效期
							mutex_release(cmutex)
							return 1
				if 'place' in config['rule'].keys():#包含场所配置
					if "-"+str(authed_place) in config['rule']['place']:#配置为非，设备肯定不在配置内，跳到下一个配置
						continue
					if str(authed_place) in config['rule']['place']:#已有认证信息的设备在配置内
						if config['time']+last_auth_time > int(time.time()):#认证在有效期
							mutex_release(cmutex)
							return 0
						else:#认证不在有效期
							mutex_release(cmutex)
							return 1
				if 'device' in config['rule'].keys():#包含设备配置
					if "-"+str(authed_routermac) in config['rule']['device']:#配置为非，设备肯定不在配置内，跳到下一个配置
						continue
					if str(authed_routermac) in config['rule']['device']:#已有认证信息的设备在配置内
						if config['time']+last_auth_time > int(time.time()):#认证在有效期
							mutex_release(cmutex)
							return 0
						else:#认证不在有效期
							mutex_release(cmutex)
							return 1
			except:
				None
	except:
		None
	try:
		#到这儿说明此设备没有对应的配置或出错，咱使用默认配置
		if default_auth_eff_time+last_auth_time > int(time.time()):#认证在有效期
			mutex_release(cmutex)
			return 0
	except:
		None
	mutex_release(cmutex)
	return 1
	
#短信验证码有效期检查
def check_sms_time(last_req_time):
	mutex_acquire(cmutex)
	try:
		if configs['sms_eff_time'][0]+last_req_time > int(time.time()):#上次验证码仍在有效期，验证码有效时间是全局的
			mutex_release(cmutex)
			return 0
		else:
			mutex_release(cmutex)
			return 1
	except:
		None
	try:
		#到这儿说明此设备没有对应的配置或出错，咱使用默认配置
		if default_sms_eff_time+last_req_time > int(time.time()):#认证在有效期
			mutex_release(cmutex)
			return 0
	except:
		None
	mutex_release(cmutex)
	return 1

#漫游范围检查
def check_roam(authed_routermac,authed_place,authed_channel,unauthed_routermac,unauthed_place,unauthed_channel):
	authed_routermac=long2mac2str(int(authed_routermac))
	unauthed_routermac=long2mac2str(int(unauthed_routermac))
	mutex_acquire(cmutex)
	try:
		for config in configs['roam']:
			try:
				if config['type'] == 'global':#全局配置，只第一个配置有效，如后有配置，则无效
					if config['rule'] == 'all':#完全漫游
						mutex_release(cmutex)
						return 0
					elif config['rule'] == 'channel':#同渠道漫游
						if str(authed_channel) == str(unauthed_channel):
							mutex_release(cmutex)
							return 0
					elif config['rule'] == 'place':#同场所漫游
						if str(authed_place) == str(unauthed_place):
							mutex_release(cmutex)
							return 0
					else:#device 或其它的都视为无漫游
						if str(authed_routermac) == str(unauthed_routermac):
							mutex_release(cmutex)
							return 0
					mutex_release(cmutex)
					return 1
				elif config['type'] == 'special':#定制配置，可有多个配置，按照配置由新到老做检测，如有非（-）配置且匹配，则直接返回非漫游
					authed_flag=0
					unauthed_flag=0
					if 'channel' in config['rule'].keys():#包含渠道配置
						if "-"+str(authed_channel) in config['rule']['channel'] or "-"+str(unauthed_channel) in config['rule']['channel']:#配置为非，两设备肯定不在同一漫游配置内，直接返回非漫游
							mutex_release(cmutex)
							return 1
						if str(authed_channel) in config['rule']['channel']:#已有认证信息的设备在配置内
							authed_flag=1
						if str(unauthed_channel) in config['rule']['channel']:#新认证设备在配置内
							unauthed_flag=1
					if 'place' in config['rule'].keys():#包含场所配置
						if "-"+str(authed_place) in config['rule']['place'] or "-"+str(unauthed_place) in config['rule']['place']:#配置为非，两设备肯定不在同一漫游配置内，直接返回非漫游
							mutex_release(cmutex)
							return 1
						if 0==authed_flag:#再检测
							if str(authed_place) in config['rule']['place']:#已有认证信息的设备在配置内
								authed_flag=1
						if 0==unauthed_flag:#再检测
							if str(unauthed_place) in config['rule']['place']:#新认证设备在配置内
								unauthed_flag=1
					if 'device' in config['rule'].keys():#包含设备配置
						if "-"+str(authed_routermac) in config['rule']['device'] or "-"+str(unauthed_routermac) in config['rule']['device']:#配置为非，两设备肯定不在同一漫游配置内，直接返回非漫游
							mutex_release(cmutex)
							return 1
						if 0==authed_flag:#再检测
							if str(authed_routermac) in config['rule']['device']:#已有认证信息的设备在配置内
								authed_flag=1
						if 0==unauthed_flag:#再检测
							if str(unauthed_routermac) in config['rule']['device']:#新认证设备在配置内
								unauthed_flag=1
					if authed_flag and unauthed_flag:#配置检测通过
						mutex_release(cmutex)
						return 0
					#如本配置未命中，走向下一个配置
			except:
				None
	except:
		None
	try:
		#到这儿说明此设备没有对应的配置或出错，咱使用默认配置（device）
		if str(authed_routermac) == str(unauthed_routermac):#为同设备
			mutex_release(cmutex)
			return 0
	except:
		None
	mutex_release(cmutex)
	return 1

def save_wechat(wechat_id,tid,openId,endmac,routermac,src_ip,src_port):
	try:
		if not wechat_id or not tid or not openId or not endmac or not routermac or 0!=ismac(endmac) or 0!=ismac(routermac):
			return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]
			
		conn=mysql_init(mysql_host,mysql_port,mysql_user,mysql_pwd,mysql_db)
		if not conn:
			return []
		cur=mysql_get_cur(conn)
		if not cur:
			mysql_close(cur,conn)
			return []
			
		tn=int(time.mktime(datetime.datetime.now().timetuple()))
		cur.execute("insert into st_auth_wechat(routermac,endmac,wc_openId,wc_encrypt_phone,auth_time,src_ip,src_port) values('"+mac2long2str(routermac)+"','"+mac2long2str(endmac)+"','"+str(openId)+"','"+str(tid)+"','"+str(tn)+"','"+str(src_ip)+"','"+str(src_port)+"') on duplicate key update wc_encrypt_phone='"+str(tid)+"',auth_time='"+str(tn)+"',src_ip='"+str(src_ip)+"',src_port='"+str(src_port)+"'")
		mysql_close(cur,conn)
		return [bytearray('success',"utf-8")]
	except:
		traceback.print_exc()
		mysql_close(cur,conn)
		return [bytearray('fail',"utf-8"),bytearray('insert failed',"utf-8")]

	
def check_openId(wechat_id,routermac,idmacs,src_ip,src_port):
	try:
		rtl=[]
		if len(idmacs)%2 != 0:
			return []
			
		conn=mysql_init(mysql_host,mysql_port,mysql_user,mysql_pwd,mysql_db)
		if not conn:
			return []
		cur=mysql_get_cur(conn)
		if not cur:
			mysql_close(cur,conn)
			return []
			
		cur.execute("select app_id,app_secretkey,app_token,app_token_time from wechat_appid where app_id='"+str(wechat_id)+"'")
		if cur.rowcount <= 0:
			mysql_close(cur,conn)
			return []
		row=cur.fetchone()
		if not row:
			mysql_close(cur,conn)
			return []
		appid=row[0]
		appsecret=row[1]
		app_token=row[2]
		app_token_time=int(row[3])
		if app_token_time < int(time.time()):
			req=request.Request("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid="+str(appid)+"&secret="+str(appsecret))
			response=json.loads(request.urlopen(req).read().decode('utf-8'))
			if "access_token" not in response.keys() or "expires_in" not in response.keys():
				rtl.append(bytearray('fail',"utf-8"))
				mysql_close(cur,conn)
				return rtl
			app_token=response['access_token']
			app_token_time=int(response['expires_in'])+int(time.time())
			cur.execute("update wechat_appid set app_token='%s',app_token_time='%s' where app_id='%s'"%(str(app_token),str(app_token_time),str(appid)))
			cur.execute("commit")
		for i in range(int(len(idmacs)/2)):
			openId=idmacs[len(idmacs)-i*2-2]
			endmac=idmacs[len(idmacs)-i*2-1]
			req=request.Request("https://api.weixin.qq.com/cgi-bin/user/info?access_token="+str(app_token)+"&openid="+str(openId))
			response=json.loads(request.urlopen(req).read().decode('utf-8'))
			if "subscribe" not in response.keys():
				rtl.append(bytearray('fail',"utf-8"))
				continue
			if int(response["subscribe"]) == 1:
				rnow=int(time.time())
				if mac2long2str(endmac) not in wechat_authes.keys():
					wechat_authes[mac2long2str(endmac)]=[]
				templist=[]
				templist.append(mac2long2str(routermac))
				templist.append(rnow)
				tempflag=1
				for k in range(0,len(wechat_authes[mac2long2str(endmac)])):
					if wechat_authes[mac2long2str(endmac)][k][0] == templist[0]:
						if int(templist[1]) > int(wechat_authes[mac2long2str(endmac)][k][1]):
							wechat_authes[mac2long2str(endmac)][k][1]=templist[1]
							tempflag=0
				if tempflag:
					wechat_authes[mac2long2str(endmac)].append(templist)
				wc_subscribe=""
				if "subscribe" in response.keys():
					wc_subscribe=response['subscribe']
				wc_subscribe_time=""
				if "subscribe_time" in response.keys():
					wc_subscribe_time=response['subscribe_time']
				wc_nickname=""
				if "nickname" in response.keys():
					wc_nickname=response['nickname']
				wc_sex=""
				if "sex" in response.keys():
					wc_sex=response['sex']
				wc_language=""
				if "language" in response.keys():
					wc_language=response['language']
				wc_country=""
				if "country" in response.keys():
					wc_country=response['country']
				wc_city=""
				if "city" in response.keys():
					wc_city=response['city']
				wc_province=""
				if "province" in response.keys():
					wc_province=response['province']
				wc_headimgurl=""
				if "headimgurl" in response.keys():
					wc_headimgurl=response['headimgurl']
				try:
					try:
						cur.execute("update st_auth_wechat set wc_subscribe='"+str(wc_subscribe)+"',wc_subscribe_time='"+str(wc_subscribe_time)+"',wc_nickname='"+MySQLdb.escape_string(wc_nickname)+"',wc_sex='"+str(wc_sex)+"',wc_language='"+wc_language+"',wc_country='"+wc_country+"',wc_province='"+wc_province+"',wc_city='"+wc_city+"',wc_headimgurl='"+wc_headimgurl+"',auth_time='"+str(rnow)+"',src_ip='"+str(src_ip)+"',src_port='"+str(src_port)+"' where routermac='%s' and endmac='%s' and wc_openId='%s'"%(mac2long2str(routermac),mac2long2str(endmac),str(openId)))
					except:
						pass
					try:
						cur.execute("insert into st_auth_wechat(routermac,endmac,wc_openId,wc_subscribe,wc_subscribe_time,wc_nickname,wc_sex,wc_language,wc_country,wc_province,wc_city,wc_headimgurl,auth_time,src_ip,src_port) values('"+mac2long2str(routermac)+"','"+mac2long2str(endmac)+"','"+str(openId)+"','"+str(wc_subscribe)+"','"+str(wc_subscribe_time)+"','"+MySQLdb.escape_string(str(wc_nickname))+"','"+str(wc_sex)+"','"+wc_language+"','"+wc_country+"','"+wc_province+"','"+wc_city+"','"+wc_headimgurl+"','"+str(rnow)+"','"+str(src_ip)+"','"+str(src_port)+"')")
					except:
						pass
					try:
						cur.execute("commit")
					except:
						pass
				except:
					traceback.print_exc()
					pass
				rtl.append(bytearray('success',"utf-8"))
				continue
			else:
				rtl.append(bytearray('fail',"utf-8"))
				continue
		mysql_close(cur,conn)
		return rtl
	except:
		traceback.print_exc()
		mysql_close(cur,conn)
		return []

def check_mac(endmac,routermac):
	try:
		rtw=check_mac_wechat(endmac,routermac)
		if rtw and rtw[0].decode('utf-8') == "success":
			print("check_mac_wechat:",endmac,routermac,rtw)
			return rtw
		rtp=check_mac_phone(endmac,routermac)
		if rtp and rtp[0].decode('utf-8') == "success":
			print("check_mac_phone:",endmac,routermac,rtp)
			return rtp
		#fail
		return rtp#or rtw
	except:
		traceback.print_exc()
		return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]

def check_mac_phone(endmac,routermac):
	global devices
	global phone_authes
	try:
		endmac=endmac.decode()
		routermac=routermac.decode()
		if not endmac or not routermac or 0!=ismac(endmac) or 0!=ismac(routermac):
			return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]
		
		#获取是否有已认证条目及相关信息
		try:
			autheds=phone_authes[mac2long2str(endmac)]
		except:
			return [bytearray('fail',"utf-8"),bytearray('not authed',"utf-8")]
		#是否漫游及是否在有效认证期
		for authed in autheds:
			#dmutex.acquire()
			try:
				authed_place=devices[long2mac2str(authed[0])]['place']
				authed_channel=devices[long2mac2str(authed[0])]['channel']
				unauthed_place=devices[long2mac2str(mac2long2str(routermac))]['place']
				unauthed_channel=devices[long2mac2str(mac2long2str(routermac))]['channel']
				#dmutex.release()
				if 0 == check_roam(authed[0],authed_place,authed_channel,mac2long2str(routermac),unauthed_place,unauthed_channel) and 0 == check_auth_time(authed[1],authed_channel,authed_place,authed[0]):
					return [bytearray('success',"utf-8")]
			except:
				pass
		return [bytearray('fail',"utf-8"),bytearray('not authed',"utf-8")]
	except:
		return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]

def check_mac_wechat(endmac,routermac):
	global devices
	global wechat_authes
	try:
		endmac=endmac.decode()
		routermac=routermac.decode()
		if not endmac or not routermac or 0!=ismac(endmac) or 0!=ismac(routermac):
			return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]
		
		#获取是否有已认证条目及相关信息
		try:
			autheds=wechat_authes[mac2long2str(endmac)]
		except:
			return [bytearray('fail',"utf-8"),bytearray('not authed',"utf-8")]
		#是否漫游及是否在有效认证期
		#dmutex.acquire()
		for authed in autheds:
			try:
				authed_place=devices[long2mac2str(authed[0])]['place']
				authed_channel=devices[long2mac2str(authed[0])]['channel']
				unauthed_place=devices[long2mac2str(mac2long2str(routermac))]['place']
				unauthed_channel=devices[long2mac2str(mac2long2str(routermac))]['channel']
				#dmutex.release()
				if 0 == check_roam(authed[0],authed_place,authed_channel,mac2long2str(routermac),unauthed_place,unauthed_channel) and 0 == check_auth_time(authed[1],authed_channel,authed_place,authed[0]):
					return [bytearray('success',"utf-8")]
			except:
				pass
		return [bytearray('fail',"utf-8"),bytearray('not authed',"utf-8")]
	except:
		return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]

def send_code(rphone,rendmac,rroutermac,src_ip,src_port):
	try:
		phone=rphone.decode()
		endmac=rendmac.decode()
		routermac=rroutermac.decode()
		tn=int(time.mktime(datetime.datetime.now().timetuple()))
		if not endmac or not phone or not routermac or 0!=isphone(phone) or 0!= ismac(endmac) or 0!=ismac(routermac):
			return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]
		
		conn=mysql_init(mysql_host,mysql_port,mysql_user,mysql_pwd,mysql_db)
		if not conn:
			return [bytearray('fail',"utf-8"),bytearray('connect to database failed',"utf-8")]
		cur=mysql_get_cur(conn)
		if not cur:
			mysql_close(cur,conn)
			return [bytearray('fail',"utf-8"),bytearray('connect to database failed',"utf-8")]

		cur.execute("select r.auth_time,r.auth_state,r.routermac,d.place_code,p.channel from (( select auth_time,auth_state,routermac from st_auth_phone where routermac='"+mac2long2str(routermac)+"' and endmac='"+mac2long2str(endmac)+"' and phone='"+str(phone)+"' order by auth_time desc limit 1) as r inner join (select device_mac,place_code from pu_device) as d on r.routermac=d.device_mac inner join (select channel,place_code from pu_place) as p on d.place_code=p.place_code) limit 1")
		if cur.rowcount == 1:#已有记录
			row=cur.fetchone()
			#查看上次认证是否仍在有效期，如仍在有效期，则不能再发送短信
			if int(row[1]) == 1:#已认证
				if 0==check_auth_time(int(row[0]),str(row[4]),str(row[3]),str(row[2])):#在认证时间段内
					mysql_close(cur,conn)
					return [bytearray('fail',"utf-8"),bytearray('auth is still effective',"utf-8")]
			#查看上次短信是否还在有效期
			if 0==check_sms_time(int(row[0])):
				mysql_close(cur,conn)
				return [bytearray('fail',"utf-8"),bytearray('code is still effective',"utf-8")]
		#send code here , then update code and auth_time
		#	when there is no mac&phone in database
		#	when there is mac&phone , but code is not effective
		#	when there is mac&phone , but auth is not effective
		#cur.execute("insert or update into st_auth_phone values(mac,phone,code,auth_state=0,auth_time=tn,conf_id)")
		#code=_send_code(phone)
		code=_send_code_aliyun(phone)
		if not code:
			print("send code fail",phone)
			mysql_close(cur,conn)
			return [bytearray('fail',"utf-8"),bytearray('send code fail',"utf-8")]
		try:
			cur.execute("insert into st_auth_phone values('"+mac2long2str(routermac)+"','"+mac2long2str(endmac)+"','"+str(phone)+"','"+str(code)+"',0,'"+str(tn)+"','"+str(src_ip)+"','"+str(src_port)+"')")
			print("insert",code,routermac,endmac,phone)
		except:
			try:
				cur.execute("update st_auth_phone set code='"+str(code)+"',auth_time='"+str(tn)+"',auth_state=0 where routermac='"+mac2long2str(routermac)+"' and endmac='"+mac2long2str(endmac)+"' and phone='"+str(phone)+"'")
				print("update",code,routermac,endmac,phone)
			except:
				pass
		mysql_close(cur,conn)
		return [bytearray('success',"utf-8")]
	except:
		traceback.print_exc()
		mysql_close(cur,conn)
		return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]

def check_code(rcode,rphone,rendmac,rroutermac):
	global phone_authes
	try:
		code=rcode.decode()
		phone=rphone.decode()
		endmac=rendmac.decode()
		routermac=rroutermac.decode()
		if not routermac or not endmac or not phone or not code or 0!=iscode(code) or 0!=isphone(phone) or 0!=ismac(endmac) or 0!=ismac(routermac):
			return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]
			
		conn=mysql_init(mysql_host,mysql_port,mysql_user,mysql_pwd,mysql_db)
		if not conn:
			return [bytearray('fail',"utf-8"),bytearray('connect to database failed',"utf-8")]
		cur=mysql_get_cur(conn)
		if not cur:
			mysql_close(cur,conn)
			return [bytearray('fail',"utf-8"),bytearray('connect to database failed',"utf-8")]
			
		cur.execute("select r.auth_time,r.auth_state,r.code,r.routermac,d.place_code,p.channel from (( select auth_time,code,auth_state,routermac from st_auth_phone where routermac='"+mac2long2str(routermac)+"' and endmac='"+mac2long2str(endmac)+"' and phone='"+str(phone)+"' and auth_state=0 order by auth_time desc limit 1) as r inner join (select device_mac,place_code from pu_device) as d on r.routermac=d.device_mac inner join (select channel,place_code from pu_place) as p on d.place_code=p.place_code) limit 1")
		if cur.rowcount != 1:
			mysql_close(cur,conn)
			return [bytearray('fail',"utf-8"),bytearray('not authenticated',"utf-8")]
		else:
			row=cur.fetchone()
			#此处仍然需要做是否有效认证过的判断，如果不判断，可能出现短信有效期内，重复此请求可更新数据库认证时间的问题
			#查看上次认证是否仍在有效期，如仍在有效期
			if int(row[1]) == 1:#已认证
				if 0==check_auth_time(int(row[0]),str(row[5]),str(row[4]),str(row[3])):#在认证时间段内
					mysql_close(cur,conn)
					return [bytearray('fail',"utf-8"),bytearray('auth is still effective',"utf-8")]
			if 0!=check_sms_time(int(row[0])):#查看上次短信是否还在有效期
				mysql_close(cur,conn)
				return [bytearray('fail',"utf-8"),bytearray('code is overtime',"utf-8")]
			elif str(code) != str(row[2]):#验证码没过期，查看验证码是否正确
				mysql_close(cur,conn)
				return [bytearray('fail',"utf-8"),bytearray('code is wrong',"utf-8")]
			else:#验证码有效，且验证码正确
				rnow=int(time.time())
				try:
					print("update st_auth_phone set auth_state=1,auth_time="+str(rnow)+" where routermac='"+mac2long2str(routermac)+"' and endmac='"+mac2long2str(endmac)+"' and phone='"+str(phone)+"'")
					cur.execute("update st_auth_phone set auth_state=1,auth_time="+str(rnow)+" where routermac='"+mac2long2str(routermac)+"' and endmac='"+mac2long2str(endmac)+"' and phone='"+str(phone)+"'")
				except:
					traceback.print_exc()
				mysql_close(cur,conn)
				if mac2long2str(endmac) not in phone_authes.keys():
					phone_authes[mac2long2str(endmac)]=[]
				templist=[]
				templist.append(mac2long2str(routermac))
				templist.append(rnow)
				tempflag=1
				for k in range(0,len(phone_authes[mac2long2str(endmac)])):
					if phone_authes[mac2long2str(endmac)][k][0] == templist[0]:
						if int(templist[1]) > int(phone_authes[mac2long2str(endmac)][k][1]):
							phone_authes[mac2long2str(endmac)][k][1]=templist[1]
							tempflag=0
				if tempflag:
					phone_authes[mac2long2str(endmac)].append(templist)
				return [bytearray('success',"utf-8")]
		mysql_close(cur,conn)
		return [bytearray('fail',"utf-8"),bytearray('not authenticated',"utf-8")]
	except:
		traceback.print_exc()
		mysql_close(cur,conn)
		return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]

def save_onoffline(jsonstr):
	try:	
		conn=mysql_init(mysql_host,mysql_port,mysql_user,mysql_pwd,mysql_db)
		if not conn:
			return [bytearray('fail',"utf-8"),bytearray('connect to database failed',"utf-8")]
		cur=mysql_get_cur(conn)
		if not cur:
			mysql_close(cur,conn)
			return [bytearray('fail',"utf-8"),bytearray('connect to database failed',"utf-8")]
			
		ojson=json.loads(jsonstr)
		print('11111111111111111111',ojson)
		if 'data' not in ojson.keys():
			mysql_close(cur,conn)
			return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]
		if 'list' not in ojson['data'].keys():
			mysql_close(cur,conn)
			return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]
		for item in ojson['data']['list']:
		#	try:
		#		cur.execute("update st_onoffline set last_offline='%s' where routermac='%s' and endmac='%s' and ip='%s' and last_online='%s'"%(str(item['last_offline']),str(item['conn_ap']),str(item['mac']),str(item['ip']),str(item['last_online'])))
		#	except:
		#		None
			try:
				cur.execute("insert into st_onoffline (routermac,endmac,ip,last_online,last_offline) values('%s','%s','%s','%s','%s')"%(str(item['conn_ap']),str(item['mac']),str(item['ip']),str(item['last_online']),str(item['last_offline'])))
			except:
				None
		mysql_close(cur,conn)
		return [bytearray('success',"utf-8")]
	except:
		traceback.print_exc()
		mysql_close(cur,conn)
		return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]

def get_wechatinfo(routermac,ssid):
	try:
		if not routermac or 0!=ismac(routermac) or not ssid:
			return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]
			
		conn=mysql_init(mysql_host,mysql_port,mysql_user,mysql_pwd,mysql_db)
		if not conn:
			return [bytearray('fail',"utf-8"),bytearray('connect to database failed',"utf-8")]
		cur=mysql_get_cur(conn)
		if not cur:
			mysql_close(cur,conn)
			return [bytearray('fail',"utf-8"),bytearray('connect to database failed',"utf-8")]
			
		try:
			cur.execute("update wechat_device set ssid='"+str(ssid)+"' where device_mac='"+mac2long2str(routermac)+"'")
		except:
			None
		try:
			cur.execute("insert into st_device values('%s','%s','%s') on duplicate key update mac='%s',ssid='%s',utime='%s'"%(mac2long2str(routermac),str(ssid),int(time.time()),mac2long2str(routermac),str(ssid),int(time.time())))
		except:
			None
		cur.execute("select secretkey,app_id,shop_id from wechat_device where device_mac='"+mac2long2str(routermac)+"'")
		#cur.execute("select wp.secretkey,wp.app_id,wp.shop_id  from wechat_device as wd inner join wechat_device as wp on wd.poi_id=wp.poi_id where wd.device_mac='%s'"%(mac2long2str(routermac),))
		if cur.rowcount <=0:
			mysql_close(cur,conn)
			return [bytearray('fail',"utf-8"),bytearray('no such device',"utf-8")]
		else:
			row=cur.fetchone()
			if not row:
				mysql_close(cur,conn)
				return [bytearray('fail',"utf-8"),bytearray('no such device',"utf-8")]
			key=str(row[0])
			appid=str(row[1])
			shopid=str(row[2])
			mysql_close(cur,conn)
			return [bytearray('success',"utf-8"),bytearray(appid,"utf-8"),bytearray(key,"utf-8"),bytearray(shopid,"utf-8")]
	except:
		traceback.print_exc()
		mysql_close(cur,conn)
		return [bytearray('fail',"utf-8"),bytearray('exe failed',"utf-8")]
		
def check_app(routermac,endmac,phone,token,src_ip,src_port):
	try:
		if not routermac or 0!=ismac(routermac) or not endmac or 0!=ismac(endmac) or not phone or 0!=isphone(phone) or not token:
			return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]
			
		conn=mysql_init(mysql_host,mysql_port,mysql_user,mysql_pwd,mysql_db)
		if not conn:
			return [bytearray('fail',"utf-8"),bytearray('connect to database failed',"utf-8")]
		cur=mysql_get_cur(conn)
		if not cur:
			mysql_close(cur,conn)
			return [bytearray('fail',"utf-8"),bytearray('connect to database failed',"utf-8")]
			
		app_url="http://119.23.207.87:8088/AppWeb/Bll/AppInfo.ashx?operation=CheckTel&Tel="+str(phone)+"&Token="+str(token)
		#postdata=parse.urlencode({"account":code_account,"pswd":code_pswd,"mobile":phone,"msg":code_msg+str(code)+code_msg_1}).encode('utf-8')
		req=request.Request(app_url)
		response=json.loads(request.urlopen(req).read().decode('utf-8'))
		if response['ReturnCode'] == "success":
			try:
				cur.execute("insert into st_auth_app values('"+mac2long2str(routermac)+"','"+mac2long2str(endmac)+"','"+str(phone)+"','"+str(time.time())+"','"+str(src_ip)+"','"+str(src_port)+"')")
				cur.execute("commit")
			except:
				None
			mysql_close(cur,conn)
			return [bytearray('success',"utf-8")]
		else:
			mysql_close(cur,conn)
			return [bytearray('fail',"utf-8"),bytearray('auth failed',"utf-8")]
	except:
		mysql_close(cur,conn)
		return [bytearray('fail',"utf-8"),bytearray('unknown',"utf-8")]

def db2mem(arg):
	global devices
	global configs
	global cmutex
	global phone_authes
	global wechat_authes
	phone_flag=0
	while True:
		try:
			newdevices={}
			newconfigs={}
			new_phone_authes={}
			new_wechat_authes={}
			conn=mysql_init(mysql_host,mysql_port,mysql_user,mysql_pwd,mysql_db)
			cur=mysql_get_cur(conn)
			try:
				if 0 == phone_flag:
					cur.execute("select distinct endmac,routermac,auth_time from st_auth_phone where auth_state=1")
					for row in cur.fetchall():
						if str(row[0]) not in new_phone_authes.keys():
							new_phone_authes[str(row[0])]=[]
						templist=[]
						templist.append(row[1])
						templist.append(int(row[2]))
						tempflag=1
						for k in range(0,len(new_phone_authes[str(row[0])])):
							if new_phone_authes[str(row[0])][k][0] == templist[0]:
								if int(templist[1]) > int(new_phone_authes[str(row[0])][k][1]):
									new_phone_authes[str(row[0])][k][1]=templist[1]
									tempflag=0
						if tempflag:
							new_phone_authes[str(row[0])].append(templist)
					phone_authes=new_phone_authes
					cur.execute("select distinct endmac,routermac,auth_time from st_auth_wechat where wc_subscribe=1")
					for row in cur.fetchall():
						if str(row[0]) not in new_wechat_authes.keys():
							new_wechat_authes[str(row[0])]=[]
						templist=[]
						templist.append(row[1])
						templist.append(int(row[2]))
						tempflag=1
						for k in range(0,len(new_wechat_authes[str(row[0])])):
							if new_wechat_authes[str(row[0])][k][0] == templist[0]:
								if int(templist[1]) > int(new_wechat_authes[str(row[0])][k][1]):
									new_wechat_authes[str(row[0])][k][1]=templist[1]
									tempflag=0
						if tempflag:
							new_wechat_authes[str(row[0])].append(templist)
					wechat_authes=new_wechat_authes
					phone_flag=1
			except:
				pass
			try:
				mutex_acquire(cmutex)
				#从数据库标记已下发的一次性命令
				try:
					if 'cmd' in configs.keys():
						for i in range(0,len(configs['cmd'])): 
							if configs['cmd'][i]['done']:#已下发
								try:
									cur.execute("update st_auth_config set cenabled=0 where cid='%s'"%(str(configs['cmd'][i]['id'])))#如果命令下发比较多，这块可能会长时间锁
									cur.execute("commit")
								except:
									traceback.print_exc()
				except:
					pass
				mutex_release(cmutex)
				#设备信息同步（仅设备、场所、渠道）
				cur.execute("select distinct d.device_mac,p.place_code,p.channel from pu_device as d inner join (select channel,place_code from pu_place) as p on d.place_code=p.place_code")
				for row in cur.fetchall():
					newdevices[long2mac2str(row[0])]={}
					newdevices[long2mac2str(row[0])]['place']=row[1]
					newdevices[long2mac2str(row[0])]['channel']=row[2]
				#规则同步
				cur.execute("select * from st_auth_config where cenabled=1 order by cid desc")
				for row in cur.fetchall():
					if row[1]:#规则为启用状态
						try:
							oneconfig=json.loads(row[3])
							if row[2] == 'cmd':#命令都为一次性的，加入下发标识字段"done"，默认为0（未下发）
								oneconfig['done']=0
								oneconfig['id']=row[0]
							if row[2] not in newconfigs.keys():
								newconfigs[row[2]]=[]
							newconfigs[row[2]].append(oneconfig)
						except:
							traceback.print_exc()
				mysql_close(cur,conn)
				#一次性命令需要单独处理，同步到新configs
				mutex_acquire(cmutex)
				try:
					if 'cmd' in configs.keys():
						for config in configs['cmd']:
							if 'done' in config.keys() and config['done'] == 0:#还未下发
								if 'cmd' not in newconfigs.keys():
									newconfigs['cmd']=[]
								if config not in newconfigs['cmd']:#且新列表也不存在，加入新列表
									newconfigs['cmd'].append(config)
				except:
					pass
				mutex_release(cmutex)
			except:#出果查询出错，不做任何配置更新
				mysql_close(cur,conn)
				time.sleep(1)
				continue
			#更新规则
			mutex_acquire(cmutex)
			configs=newconfigs
			mutex_release(cmutex)
			#dmutex.acquire()
			devices=newdevices
			#dmutex.release()
		except:
			traceback.print_exc()
		time.sleep(1)

def sync_config(routermac):
	global devices
	global configs
	global cmutex
	routermac=str(routermac).upper()
	mutex_acquire(cmutex)
	try:
		rd={}
		for config in configs['config']:
			try:
				#根据区域进行配置下发
				inflag=0
				#dmutex.acquire()
				if 'channel' in config['area'].keys():
					if devices[str(routermac)]['channel'] in config['area']['channel']:
						inflag=1
				if 0==inflag:
					if 'place' in config['area'].keys():
						if devices[str(routermac)]['place'] in config['area']['place']:
							inflag=1
				#dmutex.release()
				if 0==inflag:
					if 'device' in config['area'].keys():
						if str(routermac) in config['area']['device']:
							inflag=1
				if inflag:#此mac在配置范围内
					for key,value in config['rule'].items():
						if key not in rd.keys():#保证最小规则不重复
							rd[key]=value
			except:
				pass
		rl=[]
		for key,value in rd.items():
			rl.append(bytearray(key,"utf-8"))
			rl.append(bytearray(value,"utf-8"))
		mutex_release(cmutex)
		return rl
	except:
		pass
	mutex_release(cmutex)
	return []

def sync_white(routermac):
	global devices
	global configs
	global cmutex
	routermac=str(routermac).upper()
	mutex_acquire(cmutex)
	try:
		rl=[]
		for config in configs['white']:
			try:
				#根据区域进行配置下发
				inflag=0
				#dmutex.acquire()
				if 'channel' in config['area'].keys():
					if devices[str(routermac)]['channel'] in config['area']['channel']:
						inflag=1
				if 0==inflag:
					if 'place' in config['area'].keys():
						if devices[str(routermac)]['place'] in config['area']['place']:
							inflag=1
				#dmutex.release()
				if 0==inflag:
					if 'device' in config['area'].keys():
						if str(routermac) in config['area']['device']:
							inflag=1
				if inflag:#此mac在配置范围内
					for value in config['rule']:
						if value not in rl:
							rl.append(bytearray(value,"utf-8"))
			except:
				pass
		mutex_release(cmutex)
		return rl
	except:
		pass
	mutex_release(cmutex)
	return []

def sync_cmd(routermac):
	global configs
	global cmutex
	routermac=str(routermac).upper()
	mutex_acquire(cmutex)
	try:
		rl=[]
		for i in range(0,len(configs['cmd'])):
			try:
				#根据区域进行配置下发
				config=configs['cmd'][i]
				#只能针对设备，且一条配置只能一个设备
				if 0!=int(config['done']):#只处理还未下发的命令
					continue
				if str(routermac) == config['area']:#为此设备的命令配置
					if config['rule'] not in rl:
						rl.append(bytearray(config['rule'],"utf-8"))
					configs['cmd'][i]['done']=1#更改下发状态为已下发
			except:
				pass
		mutex_release(cmutex)
		return rl
	except:
		pass
	mutex_release(cmutex)
	return []

def analyze_data(indata):
	try:
		#RSA decrypt
		rtdata=[]
		datalen=len(indata[:])
		#rsa_pri=RSA.load_key(rsa_private_file,rsa_pass_callback)
		#andata=rsa_pri.private_decrypt(indata,RSA.pkcs1_padding)
		andata=indata
		donelen=0
		while donelen < datalen:
			tmpdata={}
			if datalen-donelen < 4:
				break
			tmpdata['len'],=struct.unpack('I',andata[donelen:donelen+4])
			donelen+=4
			if donelen+tmpdata['len']>datalen:
				break
			tmpdata['data']=andata[donelen:donelen+tmpdata['len']]
			donelen+=tmpdata['len']
			rtdata.append(tmpdata)
		return rtdata
	except:
		traceback.print_exc()
		return []
		

def _thread_worker(args):
	try:
		andata=analyze_data(args['data'])
		rsdata=bytearray()
		#get ip/port
		src_ip=conn_addr[args['fileno']][0]
		src_port=conn_addr[args['fileno']][1]
		#do things
		rsdata.extend(struct.pack("I",args['type']))
		if RTYPE['rcheckmac'] == args['type']:#check mac
			if len(andata) < 2:#endmac,routermac
				clean_fileno(args['fileno'])
				return -1
			rtdata=check_mac(andata[0]['data'],andata[1]['data'])
			#if rtdata[0].decode() == "success":#save information if check_mac success
			#	rtdata=save_mac(andata[0]['data'],andata[1]['data'],src_ip,src_port)
			for onertdata in rtdata[::-1]:
				rsdata.extend(struct.pack("I",len(onertdata)))
				rsdata.extend(onertdata)
		elif RTYPE['rauthphone'] == args['type']:
			if len(andata) < 1:#step
				clean_fileno(args['fileno'])
				return -1
			step,=struct.unpack("I",andata[-1]['data'][0:4])
			if RPHONESTEP['rsendcode'] == step:
				if len(andata) < 4:#phone,endmac,routermac,step
					clean_fileno(args['fileno'])
					return -1
				rtdata=send_code(andata[0]['data'],andata[1]['data'],andata[2]['data'],src_ip,src_port)
				print("send_code:",rtdata)
				for onertdata in rtdata[::-1]:
					rsdata.extend(struct.pack("I",len(onertdata)))
					rsdata.extend(onertdata)
				rsdata.extend(struct.pack("I",4))
				rsdata.extend(struct.pack("I",RPHONESTEP['rsendcode']))
			elif RPHONESTEP['rcheckcode'] == step:
				if len(andata) < 5:#code,phone,endmac,routermac,step
					clean_fileno(args['fileno'])
					return -1
				rtdata=check_code(andata[0]['data'],andata[1]['data'],andata[2]['data'],andata[3]['data'])
				print("check_code:",rtdata)
				for onertdata in rtdata[::-1]:
					rsdata.extend(struct.pack("I",len(onertdata)))
					rsdata.extend(onertdata)
				rsdata.extend(struct.pack("I",4))
				rsdata.extend(struct.pack("I",RPHONESTEP['rcheckcode']))
		elif RTYPE['rauthwechat'] == args['type']:
			if len(andata) < 1:#step
				clean_fileno(args['fileno'])
				return -1
			step,=struct.unpack("I",andata[-1]['data'][0:4])
			if RWECHATSTEP['rsaveinfo'] == step:#step 1
				if len(andata) < 6:#wechat_id,tid,openId,endmac,routermac,step
					clean_fileno(args['fileno'])
					return -1
				rtdata=save_wechat(andata[0]['data'].decode('utf-8'),andata[1]['data'].decode('utf-8'),andata[2]['data'].decode('utf-8'),andata[3]['data'].decode('utf-8'),andata[4]['data'].decode('utf-8'),src_ip,src_port)
				for onertdata in rtdata[::-1]:
					rsdata.extend(struct.pack("I",len(onertdata)))
					rsdata.extend(onertdata)
				rsdata.extend(struct.pack("I",4))
				rsdata.extend(struct.pack("I",RWECHATSTEP['rsaveinfo']))
			elif RWECHATSTEP['rcheckopenId'] == step:#step 2
				if len(andata) < 5:#wechat_id,openId,endmac,routermac,step
					clean_fileno(args['fileno'])
					return -1
				rtdata=check_openId(andata[0]['data'].decode('utf-8'),andata[1]['data'].decode('utf-8'),[txx['data'].decode('utf-8') for txx in andata[2:-1]],src_ip,src_port)
				for onertdata in rtdata[::-1]:
					rsdata.extend(struct.pack("I",len(onertdata)))
					rsdata.extend(onertdata)
				rsdata.extend(struct.pack("I",4))
				rsdata.extend(struct.pack("I",RWECHATSTEP['rcheckopenId']))
		#暂时去除上下线功能
		elif RTYPE['ronoffline'] == args['type']:
			if len(andata) < 1:#json string
				clean_fileno(args['fileno'])
				return -1
			rtdata=save_onoffline(andata[0]['data'].decode('utf-8'))
			print("接收到的数据stdog_onoffline",rtdata)
			for onertdata in rtdata[::-1]:
				rsdata.extend(struct.pack("I",len(onertdata)))
				rsdata.extend(onertdata)
				#print("接收到的数据stdog_onoffline_rt",rtdata)
			#print("接收到的数据stdog_onoffline_one",onerdata
		elif RTYPE['rwechatinfo'] == args['type']:
			if len(andata) < 2:#routermac,ssid
				clean_fileno(args['fileno'])
				return -1
			rtdata=get_wechatinfo(andata[0]['data'].decode('utf-8'),andata[1]['data'].decode('utf-8'))
			for onertdata in rtdata[::-1]:
				rsdata.extend(struct.pack("I",len(onertdata)))
				rsdata.extend(onertdata)
		elif RTYPE['rauthapp'] == args['type']:
			if len(andata) < 4:#routermac,endmac,phone,token
				clean_fileno(args['fileno'])
				return -1
			rtdata=check_app(andata[3]['data'].decode('utf-8'),andata[2]['data'].decode('utf-8'),andata[1]['data'].decode('utf-8'),andata[0]['data'].decode('utf-8'),src_ip,src_port)
			for onertdata in rtdata[::-1]:
				rsdata.extend(struct.pack("I",len(onertdata)))
				rsdata.extend(onertdata)
		elif RTYPE['rsdconfig'] == args['type']:
			if len(andata) < 1:#routermac
				clean_fileno(args['fileno'])
				return -1
			rtdata=sync_config(andata[0]['data'].decode('utf-8'))
			#print("sync_config",rtdata)
			for onertdata in rtdata[::-1]:
				rsdata.extend(struct.pack("I",len(onertdata)))
				rsdata.extend(onertdata)
		elif RTYPE['rsdwhite'] == args['type']:
			if len(andata) < 1:#routermac
				clean_fileno(args['fileno'])
				return -1
			rtdata=sync_white(andata[0]['data'].decode('utf-8'))
			#print("sync_white",rtdata)
			for onertdata in rtdata[::-1]:
				rsdata.extend(struct.pack("I",len(onertdata)))
				rsdata.extend(onertdata)
		elif RTYPE['rsdcmd'] == args['type']:
			if len(andata) < 1:#routermac
				clean_fileno(args['fileno'])
				return -1
			rtdata=sync_cmd(andata[0]['data'].decode('utf-8'))
			#print("sync_cmd",rtdata)
			for onertdata in rtdata[::-1]:
				rsdata.extend(struct.pack("I",len(onertdata)))
				rsdata.extend(onertdata)
		else:#will not come here
			clean_fileno(args['fileno'])
			return -1
		send_data[args['fileno']]=bytearray()
		send_data[args['fileno']].extend(struct.pack("I",len(rsdata)))
		send_data[args['fileno']].extend(rsdata)
		xl=[]
		for i in send_data[args['fileno']]:
			xl.append(str(i))
		ep.modify(args['fileno'], select.EPOLLOUT | select.EPOLLHUP | select.EPOLLET)
		return 0
	except:
		traceback.print_exc()
		try:
			clean_fileno(args['fileno'])
		except:
			pass
		return -1

def thread_worker(args):
	_thread_worker(args)

def myaccept(fileno):
	try:
		while True:
			try:
				connection,address=sockfd.accept()
				connection.setblocking(0)
				ep.register(connection.fileno(),select.EPOLLIN | select.EPOLLHUP | select.EPOLLET)
				mutex_acquire(gmutex)
				try:
					conn_state[connection.fileno()]=connection
					conn_time[connection.fileno()]=int(time.time())
					conn_addr[connection.fileno()]=address
					recv_data[connection.fileno()]=bytearray()
					send_data[connection.fileno()]=bytearray()
				except:
					pass
				mutex_release(gmutex)
			except:
				break
	except:
		pass

def myrecv(fileno):
	data=bytearray()
	try:
		try:
			while True:
				tmpdata=conn_state[fileno].recv(1024)
				if 0 == len(tmpdata[:]):#not raise and recv data len is 0,means connection is closed
					return 0
				data.extend(tmpdata[:])
		except socket.error as msg:
			if msg.errno == errno.EAGAIN:#read all data out for now
				pass
			else:
				return -1
	except:
		return -1
	try:
		#if there is one request,then send it to handle queue
		recv_data[fileno].extend(data)
		if len(recv_data[fileno]) >= 4:
			need_len,=struct.unpack("I",recv_data[fileno][0:4])
			if need_len > recv_max_len:
				return -1
			if len(recv_data[fileno]) >= 8:
				rtype,=struct.unpack("I",recv_data[fileno][4:8])
				if rtype not in RTYPE.values():
					return -1
			if need_len <= len(recv_data[fileno])-4:#deal with each request when all(over) data is received
				tp.map_async(thread_worker,[{'data':recv_data[fileno][8:need_len+4],'type':rtype,'fileno':fileno}])
				recv_data[fileno]=recv_data[fileno][need_len+4:]#cut other data
		return len(data)
	except:
		return 0

def mysend(fileno):
	sbytes=0
	try:
		try:
			while True:
				sbytes+=conn_state[fileno].send(send_data[fileno][sbytes:])
				if sbytes == len(send_data[fileno][:]):
					return 0
		except socket.error as msg:
			if msg.errno == errno.EAGAIN:
				pass
			else:
				return -1
		send_data[fileno]=send_data[fileno][sbytes:]
	except:
		clean_fileno(fileno)
	return sbytes

#variable define
atc_ip='120.77.92.180'
atc_port=8091
recv_max_len=20480
pool_size=500

mysql_host="127.0.0.1"
mysql_port=3306
mysql_user="root"
mysql_pwd="root123"
mysql_db="wifi_operation"

RTYPE={'rcheckmac':0,'rauthphone':1,'rauthwechat':3,'rwechatinfo':4,'rauthapp':5,'ronoffline':101,'rsdconfig':10001,'rsdwhite':10002,'rsdcmd':10003}
RPHONESTEP={'rsendcode':1,'rcheckcode':2}
RWECHATSTEP={'rsaveinfo':1,'rcheckopenId':2}
#WECHAT_ID={'10001':{'appid':'wxa24a28077c67906e','appsec':'3ce0f13be73084e14ebc1f7612788618'},'10010':{'appid':'wxa24a28077c67906e','appsec':'3ce0f13be73084e14ebc1f7612788618'},'10011':{'appid':'wxbd5f418224c26cfb','appsec':'774acbde4f10d1203044b96944e8bf5b'}}

code_url="http://222.73.117.158/msg/HttpBatchSendSM?"
code_account="guangdao"
code_pswd="Guangdao123"
code_msg="尊敬的用户，您的验证码是:"
code_msg_1="，本验证码2分钟内有效，感谢您的使用。"

sockfd=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sockfd.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
sockfd.bind((atc_ip,atc_port))
sockfd.listen(1000)
sockfd.setblocking(0)
sockfd.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
ep=select.epoll()
ep.register(sockfd.fileno(),select.EPOLLIN | select.EPOLLET)


#init thread pool
tp=ThreadPool(pool_size)
#mpool=multiprocessing.Pool(processes=10)

conn_state={}
conn_time={}
conn_addr={}
recv_data={}
send_data={}
gmutex=threading.Lock()
cmutex=threading.Lock()
#dmutex=threading.Lock()
#基础信息同步线程
tp.map_async(db2mem,[""])
#超时检测线程
tp.map_async(close_timeout,[""])

while True:
	events=ep.poll()
	for fileno,event in events:
		try:
			if fileno == sockfd.fileno():#new connection come
				myaccept(fileno)
			elif event & select.EPOLLIN:#just deal with recv msgs,then handle over them to thread_worker
				rlen=myrecv(fileno)
				if 0==rlen or -1 == rlen:
					clean_fileno(fileno)
			elif event & select.EPOLLOUT:
				rlen=mysend(fileno)
				if 0 == rlen or -1 == rlen:
					clean_fileno(fileno)
			else:
				clean_fileno(fileno)
		except:
			try:
				if fileno != sockfd.fileno():
					clean_fileno(fileno)
			except:
				pass

tp.wait()
#mpool.close()
ep.close()
