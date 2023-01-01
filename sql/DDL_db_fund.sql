/******************************************/
/*   DatabaseName = db_fund_test   */
/*   TableName = tbl_assets   */
/******************************************/
CREATE TABLE `tbl_assets` (
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '名称',
  `code` char(6) NOT NULL COMMENT '代码',
  `filed` varchar(255) DEFAULT NULL COMMENT '领域',
  `position` decimal(10,2) DEFAULT '0.00' COMMENT '持仓',
  `netvalue` decimal(10,4) DEFAULT '0.0000' COMMENT '净值',
  `profit` decimal(10,2) DEFAULT '0.00' COMMENT '收益',
  `profit_rate` decimal(5,4) DEFAULT '0.0000' COMMENT '收益率',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '更新日期',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `comment` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '备注',
  `buy_rate` decimal(5,4) DEFAULT NULL COMMENT '买入费率',
  `sell_rate_info` varchar(255) DEFAULT NULL COMMENT '卖出费率信息',
  `url` varchar(255) DEFAULT NULL COMMENT '爬虫链接',
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='基金的各项最新数据'
;

CREATE TABLE `tbl_investments` (
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '名称',
  `code` char(6) NOT NULL COMMENT '代码',
  `amount` decimal(10,2) DEFAULT '0.00' COMMENT '每期金额',
  `period` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '扣款周期',
  `data` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '扣款日期',
  `state` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '计划状态',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '更新日期',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='基金的各项最新数据'
;

/******************************************/
/*   DatabaseName = db_fund_test   */
/*   TableName = tbl_funds_for_backtest   */
/******************************************/
CREATE TABLE `tbl_funds_for_backtest` (
  `name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '名称',
  `code` char(6) NOT NULL COMMENT '代码',
  `filed` varchar(255) DEFAULT NULL COMMENT '领域',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '更新日期',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `comment` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '备注',
  `buy_rate` decimal(5,4) DEFAULT NULL COMMENT '买入费率',
  `sell_rate_info` varchar(255) DEFAULT NULL COMMENT '卖出费率信息',
  `url` varchar(255) DEFAULT NULL COMMENT '爬虫链接',
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='回测基金列表'
;

/******************************************/
/*   DatabaseName = db_fund_test   */
/*   TableName = tbl_history   */
/******************************************/
CREATE TABLE `tbl_history` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `code` char(6) NOT NULL COMMENT '代码',
  `position` decimal(10,2) DEFAULT '0.00' COMMENT '持仓',
  `netvalue` decimal(10,4) DEFAULT '0.0000' COMMENT '净值',
  `profit` decimal(10,2) DEFAULT '0.00' COMMENT '收益',
  `profit_rate` decimal(5,4) DEFAULT '0.0000' COMMENT '收益率',
  `record_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=124 DEFAULT CHARSET=utf8 COMMENT='各项的基金历史数据'
;
