from apollo.src.service.data_service import add_fund, delete_fund, update_fund, show_fund
from apollo.src.service.tsp_service import upload_netvalue_and_info
from apollo.src.prof_model.fund_types import Filed, Status
from apollo.src.db_model.tbl_info import InfoTable
from apollo.src.service.aip_service import invest_week, invest_month


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

    # show_fund(code='165520')

    # upload_netvalue_and_info(code = '005827')
    # print(InfoTable.get_by_code('005827').name)
    # invest_week('005827', '2020-08-04', '2021-08-03', 100)
    invest_month('005827', '2020-08-04', '2021-08-06', 400)

if __name__ == "__main__":
    main()
    Total for each field
    tbl_total_for_field