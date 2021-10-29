/******************************************/
/*   DatabaseName = db_fund   */
/*   TableName = tbl_depository   */
/******************************************/
CREATE TABLE `tbl_depository` (
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '名称',
  `code` char(6) NOT NULL COMMENT '代码',
  `filed` varchar(255) DEFAULT NULL COMMENT '领域',
  `buying` decimal(10,2) DEFAULT '0.00' COMMENT '投入',
  `selling` decimal(10,2) DEFAULT '0.00' COMMENT '赎回',
  `position` decimal(10,2) DEFAULT '0.00' COMMENT '持仓',
  `profit` decimal(10,2) DEFAULT '0.00' COMMENT '收益',
  `profit_rate` decimal(5,4) DEFAULT '0.0000' COMMENT '收益率',
  `priority` int(2) DEFAULT '0' COMMENT '优先级',
  `status` varchar(32) NOT NULL DEFAULT 'Holding' COMMENT '持仓状态',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '更新日期',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `comment` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '备注',
  `buy_rate` decimal(5,4) DEFAULT NULL COMMENT '买入费率',
  `sell_rate_info` varchar(255) DEFAULT NULL COMMENT '卖出费率信息',
  `url` varchar(255) DEFAULT NULL COMMENT '爬虫链接',
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='基金的各项最新数据'
;

/******************************************/
/*   DatabaseName = db_fund   */
/*   TableName = tbl_history_buying   */
/******************************************/
CREATE TABLE `tbl_history_buying` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `date` datetime DEFAULT CURRENT_TIMESTAMP,
  `total` decimal(10,2) DEFAULT NULL,
  `manufacturing` decimal(10,2) DEFAULT NULL,
  `resource` decimal(10,2) DEFAULT NULL,
  `semiconductor` decimal(10,2) DEFAULT NULL,
  `medical_institutions` decimal(10,2) DEFAULT NULL,
  `consumption` decimal(10,2) DEFAULT NULL,
  `finance_estate` decimal(10,2) DEFAULT NULL,
  `Hongkong_stocks` decimal(10,2) DEFAULT NULL,
  `US_stocks` decimal(10,2) DEFAULT NULL,
  `comment` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8 COMMENT='投入的历史'
;

/******************************************/
/*   DatabaseName = db_fund   */
/*   TableName = tbl_history_position   */
/******************************************/
CREATE TABLE `tbl_history_position` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `date` datetime DEFAULT CURRENT_TIMESTAMP,
  `total` decimal(10,2) DEFAULT NULL,
  `manufacturing` decimal(10,2) DEFAULT NULL,
  `resource` decimal(10,2) DEFAULT NULL,
  `semiconductor` decimal(10,2) DEFAULT NULL,
  `medical_institutions` decimal(10,2) DEFAULT NULL,
  `consumption` decimal(10,2) DEFAULT NULL,
  `finance_estate` decimal(10,2) DEFAULT NULL,
  `Hongkong_stocks` decimal(8,2) DEFAULT NULL,
  `US_stocks` decimal(10,2) DEFAULT NULL,
  `comment` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC COMMENT='持仓的历史'
;

/******************************************/
/*   DatabaseName = db_fund   */
/*   TableName = tbl_history_profit   */
/******************************************/
CREATE TABLE `tbl_history_profit` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `date` datetime DEFAULT CURRENT_TIMESTAMP,
  `total` decimal(10,2) DEFAULT NULL,
  `manufacturing` decimal(10,2) DEFAULT NULL,
  `resource` decimal(10,2) DEFAULT NULL,
  `semiconductor` decimal(10,2) DEFAULT NULL,
  `medical_institutions` decimal(10,2) DEFAULT NULL,
  `consumption` decimal(10,2) DEFAULT NULL,
  `finance_estate` decimal(10,2) DEFAULT NULL,
  `Hongkong_stocks` decimal(8,2) DEFAULT NULL,
  `US_stocks` decimal(10,2) DEFAULT NULL,
  `comment` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC COMMENT='收益的历史'
;

/******************************************/
/*   DatabaseName = db_fund   */
/*   TableName = tbl_operation_record   */
/******************************************/
CREATE TABLE `tbl_operation_record` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `operate_id` varchar(20) NOT NULL,
  `name` varchar(255) NOT NULL,
  `code` varchar(6) NOT NULL,
  `operate_type` varchar(32) NOT NULL,
  `amount` decimal(10,2) DEFAULT NULL,
  `operate_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `comment` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `info_after_change` varchar(2048) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `info_before_change` varchar(2048) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=550 DEFAULT CHARSET=utf8 COMMENT='买、卖、更新、删除基金的操作记录'
;

/******************************************/
/*   DatabaseName = db_fund   */
/*   TableName = tbl_total_for_field   */
/******************************************/
CREATE TABLE `tbl_total_for_field` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `filed` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `filed_cn` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `buying` decimal(10,2) DEFAULT NULL,
  `selling` decimal(10,2) DEFAULT NULL,
  `position` decimal(10,2) DEFAULT NULL,
  `profit` decimal(10,2) DEFAULT NULL,
  `profit_rate` decimal(5,4) DEFAULT NULL,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8 COMMENT='每个领域的合计'
;
