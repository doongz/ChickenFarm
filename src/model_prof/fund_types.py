class Filed:
    
    ENERGY = "new_energy"
    SEMI = "semiconductor"
    METALS = "Non_ferrous_metals"
    MEDICAL = "medical_institutions"
    SPIRIT = "white_spirit"
    HK = "Hongkong_stocks"
    US = "US_stocks"
    BLUE = "blue_chip"
    FINANCE = "finance_estate"
    MILITARY = "military_industry"


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