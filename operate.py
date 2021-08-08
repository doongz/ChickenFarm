from service.data_service import add_fund, delete_fund, update_fund, show_fund
from prof_model.fund_types import Filed, Status


def main():
    # add_fund(code='519185', 
    #          filed=Filed.FINANCE, 
    #          buying=450, 
    #          selling=0, 
    #          position=387.73,
    #          status=Status.HOLD,
    #          comment='停止买入')


    # update_fund(code='165520', 
    #             update_data={'profit':418.91,
    #                          'profit_rate':0.2889})

    show_fund(code='165520')

if __name__ == "__main__":
    main()