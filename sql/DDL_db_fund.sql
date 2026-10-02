/******************************************/
/*   DatabaseName = db_fund               */
/*   TableName = tbl_funds_for_backtest   */
/******************************************/
CREATE TABLE `tbl_funds_for_backtest` (
  `name` varchar(256) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '名称',
  `code` char(6) NOT NULL COMMENT '代码',
  `filed` varchar(255) DEFAULT NULL COMMENT '领域',
  `order_index` int(11) DEFAULT NULL COMMENT '领域内排序',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '更新日期',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `comment` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL COMMENT '备注',
  `buy_rate` decimal(5,4) DEFAULT NULL COMMENT '买入费率',
  `sell_rate_info` varchar(255) DEFAULT NULL COMMENT '卖出费率信息',
  `url` varchar(255) DEFAULT NULL COMMENT '数据来源链接',
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='回测标的清单'
;
