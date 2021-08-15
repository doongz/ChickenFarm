import os


LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "./logging.conf")


if os.getenv('POSITION_CSV_PATH', None):
    POSITION_CSV_PATH = os.getenv('POSITION_CSV_PATH')
else:
    POSITION_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "./position.csv")


EXPORT_TABLE_PATH = os.getenv('EXPORT_TABLE_PATH', None)


EXPORT_CHART_PATH = os.getenv('EXPORT_CHART_PATH', None)


EXPORT_AIP_PLOT_PATH = os.getenv('EXPORT_AIP_PLOT_PATH', None)