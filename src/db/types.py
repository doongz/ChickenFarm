class Filed:

    FACTURE = "manufacturing"
    RESOURCE = "resource"
    SEMI = "semiconductor"
    MEDICAL = "medical_institutions"
    CONSUME = "consumption"
    FINANCE = "finance_estate"
    HK = "Hongkong_stocks"
    US = "US_stocks"

    def get_fileds(self):
        fileds = []
        for attr in self.__dir__():
            if attr.startswith('_') or attr.startswith('get'):
                continue
            fileds.append(getattr(Filed, attr))
        return fileds


class Status:

    HOLD = "Holding"
    CLEAR = "Clearance"


class OperateType:

    ADD = 'add'
    BUY = 'buy'
    SELL = 'sell'
    UPDATE = 'update'
    DELETE = 'delete'
