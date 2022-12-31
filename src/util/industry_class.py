class Industry:
    def __init__(self, en, cn, color):
        self.en = en
        self.cn = cn
        self.color = color


MANU = Industry("Manufacture", "制造", "limegreen")
RESO = Industry("Resource", "资源", "dodgerblue")
SEMI = Industry("Semiconductor", "半导体", "mediumorchid")
MEDI = Industry("Medical", "医疗", "lightskyblue")
CONS = Industry("Consumption", "消费", "silver")
FINA = Industry("Finance", "金融", "gold")
HK = Industry("HongKong", "港股", "coral")
US = Industry("United_States", "美股", "orange")

Fileds = [
    MANU,
    RESO,
    SEMI,
    MEDI,
    CONS,
    FINA,
    HK,
    US,
]


def get_fileds_en():
    fileds_en = []
    for f in Fileds:
        fileds_en.append(f.en)
    return fileds_en


def get_fileds_cn():
    fileds_cn = []
    for f in Fileds:
        fileds_cn.append(f.cn)
    return fileds_cn


def get_fileds_color():
    fileds_color = []
    for f in Fileds:
        fileds_color.append(f.color)
    return fileds_color


def get_filed_idx(en):
    for i, f in enumerate(Fileds):
        if f.en == en:
            return i
    return -1
