/*
Navicat MySQL Data Transfer

Source Server         : 180
Source Server Version : 50629
Source Host           : localhost:3306
Source Database       : wifi_operation

Target Server Type    : MYSQL
Target Server Version : 50629
File Encoding         : 65001

Date: 2018-08-19 16:27:53
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for st_onoffline
-- ----------------------------
DROP TABLE IF EXISTS `st_onoffline`;
CREATE TABLE `st_onoffline` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `routermac` char(128) NOT NULL,
  `endmac` char(128) NOT NULL,
  `ip` char(32) NOT NULL,
  `last_online` int(11) NOT NULL,
  `last_offline` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=215 DEFAULT CHARSET=utf8;
