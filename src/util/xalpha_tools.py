import xalpha as xa


def get_fundinfo_from_xalpha(code):
    fundinfo = xa.fundinfo(code)
    return fundinfo