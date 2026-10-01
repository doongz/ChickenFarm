# 快速开始

本指南帮助你在本地完成 ChickenFarm 的安装、配置，并运行第一个任务。

## 环境要求

- macOS（项目在 macOS 上验证；Linux 类似）
- Python 3.10 及以上（推荐 3.12）
- MySQL 5.7+ / 8.0
- Google Chrome 与对应版本的 ChromeDriver（仅采集天天基金个人数据时需要）

## 1. 准备 MySQL 数据库

使用 Homebrew 安装并启动 MySQL（macOS）：

```bash
brew install mysql
brew services start mysql      # 启动
brew services restart mysql    # 重启
brew services stop mysql       # 停止
brew services info mysql       # 查看状态
```

需要创建以下三个数据库：

| 数据库 | 是否需要建表 | 用途 |
| :--- | :--- | :--- |
| `db_fund` | 是，使用 [DDL_db_fund.sql](../sql/DDL_db_fund.sql) | 个人统计数据（持仓、定投、历史） |
| `db_netvalue` | 否（程序自动建表） | 各基金爬取的历史净值 |
| `db_backtest` | 否（程序自动建表） | 回测结果数据 |

在 `db_fund` 中整库执行建表脚本：

```bash
mysql -u <user> -p -e "CREATE DATABASE IF NOT EXISTS db_fund DEFAULT CHARACTER SET utf8mb4;"
mysql -u <user> -p db_fund < sql/DDL_db_fund.sql
mysql -u <user> -p -e "CREATE DATABASE IF NOT EXISTS db_netvalue; CREATE DATABASE IF NOT EXISTS db_backtest;"
```

由于回测采用多进程并发写入，建议调大 MySQL 最大连接数。编辑
`/etc/mysql/my.cnf`（Linux/macOS）：

```ini
[mysqld]
max_connections = 500
```

## 2. 填写配置文件

复制并编辑项目根目录下的 [config.yaml](../config.yaml)，按注释填写：

```yaml
DB_USERNAME:           # 数据库账号
DB_PASSWORD:           # 数据库密码
DB_ADDRESS:            # 数据库地址，如 127.0.0.1
DB_PORT: 3306          # 数据库端口
DB_FUND:               # 个人统计库名，如 db_fund
DB_NETVALUE:           # 净值库名，如 db_netvalue
DB_BACKTEST:           # 回测库名，如 db_backtest

# 若不需要采集个人数据，仅做回测分析，可不用填写下方配置
TIANTIAN_USERNAME:     # 天天基金账号
TIANTIAN_PASSWORD:     # 天天基金交易密码
EXPORT_TABLE_PATH:     # 导出个人数据统计表的路径
EXPORT_CHART_PATH:     # 导出个人数据统计图的路径
EXPORT_AIP_PLOT_PATH:  # 导出回测分析图的路径
```

> 导出路径在运行时会自动追加一个以当天日期命名的子目录（`YYYY-MM-DD`）。

## 3. 配置环境变量

将项目父目录加入 `PYTHONPATH`（代码以 `ChickenFarm.xxx` 作为包导入），并指定配置文件路径：

```shell
echo "export PYTHONPATH=\$PYTHONPATH:<项目所在的父目录>" >> ~/.zshrc
echo "export FARM_CONFIG_PATH=<config.yaml 的绝对路径>" >> ~/.zshrc
source ~/.zshrc
```

- 例如项目路径为 `/Users/me/ChickenFarm`，则父目录为 `/Users/me`。
- 使用 bash 的用户请将 `~/.zshrc` 替换为 `~/.bash_profile`。

## 4. 安装依赖

推荐使用 [uv](https://docs.astral.sh/uv/) 管理虚拟环境：

```shell
uv venv --python 3.10          # 创建虚拟环境
source .venv/bin/activate      # 激活（macOS/Linux）
uv pip install -r requirements.txt
```

或直接使用 pip：

```shell
python3 -m pip install -r requirements.txt
```

> **重要**：`chinesecalendar` 与 `xalpha` 需要定期更新以保证节假日与数据接口可用：
>
> ```bash
> pip install -U chinesecalendar xalpha
> ```

### 安装 ChromeDriver（可选）

仅当需要自动登录天天基金抓取个人持仓/定投时安装。版本需与本地 Chrome 对应：

- 下载地址：https://developer.chrome.com/docs/chromedriver/downloads
- 安装到 PATH：

  ```shell
  cp chromedriver-mac-x64/chromedriver /usr/local/bin
  ```

如需关闭 Chrome 自动升级（避免与 ChromeDriver 版本不匹配）：

```shell
sudo defaults write com.google.Keystone.Agent checkInterval 0
sudo defaults write com.google.Keystone.Installer checkInterval 0
```

## 5. 运行第一个任务

### 回测分析

先把要分析的基金加入回测列表（只需添加一次，运行时按提示选择所属领域）：

```shell
python3 chick.py -add -c 005827
```

然后一键执行回测任务：

```shell
python3 chick.py -job backtest_job
```

该任务依次完成：

1. 把基金历史净值上传至 `db_netvalue`；
2. 运行回测并将结果写入 `db_backtest`；
3. 导出各领域回测小提琴图。

### 个人数据分析

```shell
python3 chick.py -job base_job
```

该任务依次完成：

1. 从天天基金抓取本周持仓与定投记录并更新数据库；
2. 记录各基金的持仓、净值、收益、收益率历史；
3. 导出个人数据统计表（CSV）；
4. 导出个人数据统计图。

完整命令说明请参阅 [命令行手册](./cli.md)，回测原理请参阅 [回测与算法](./backtest.md)。
