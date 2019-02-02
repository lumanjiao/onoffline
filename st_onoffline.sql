/*
Navicat PGSQL Data Transfer

Source Server         : 203公安端
Source Server Version : 80215
Source Host           : localhost:5432
Source Database       : police_center_src_db
Source Schema         : audit_data

Target Server Type    : PGSQL
Target Server Version : 80215
File Encoding         : 65001

Date: 2018-08-17 21:09:41
*/


-- ----------------------------
-- Table structure for st_onoffline
-- ----------------------------
DROP TABLE IF EXISTS "audit_data"."st_onoffline";
CREATE TABLE "audit_data"."st_onoffline" (
"routermac" varchar(128) NOT NULL,
"endmac" varchar(128) NOT NULL,
"ip" varchar(32),
"last_online" int8,
"last_offline" int8
)
WITH (OIDS=FALSE)

;
