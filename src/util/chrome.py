import time
from retry import retry

from selenium import webdriver
from selenium.webdriver.common.by import By    
# By.CLASS_NAME, CSS_SELECTOR, ID, LINK_TEXT, NAME, PARTIAL_LINK_TEXT, TAG_NAME, XPATH
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

from ChickenFarm.src.util.config import Config 
from ChickenFarm.src.util.log import get_logger


config = Config()
logger = get_logger(__file__)


class ChromeDriver():

    def __init__(self):
        pass

    def _login(self, url):
        self.driver = webdriver.Chrome()
        self.driver.get(url)
        self._wait(by=By.ID, value='tbname')

        time.sleep(0.5)
        self.driver.find_element_by_id('tbname').send_keys(config.tiantian_username)
        time.sleep(0.5)
        self.driver.find_element_by_id('tbpwd').send_keys(config.tiantian_password)
        self.driver.find_element_by_id('btn_login').click()

    def _wait(self, by, value, timeout=10, frequency=0.5, message='Element not found'):
        WebDriverWait(driver=self.driver, timeout=timeout, poll_frequency=frequency) \
            .until(lambda x: x.find_element(by=by, value=value), \
                   message=message)


    @retry(exceptions=(TimeoutException, StaleElementReferenceException), tries=3, delay=3)
    def query_position(self):
        '''
        获取仓位数据
        '''
        try:
            url = "https://trade.1234567.com.cn/MyAssets/hold"
            self._login(url)
            self._wait(by=By.CLASS_NAME, value='table-hold')
            
            timeout = 5
            while True:
                positions = []
                tag_elements = self.driver.find_element(By.CLASS_NAME, 'table-hold').find_elements(By.TAG_NAME, 'tr')
                for tag in tag_elements:
                    positions.append(tag.text)

                if "数据加载中" not in "".join(positions):
                    break
                elif timeout < 0:
                    raise Exception(f"Query position timeout.")
                else:
                    logger.warning(f"数据加载中..., 正在重试。")
                    time.sleep(1)
                    timeout -= 1

        finally:
            self.driver.quit()
        
        positions = positions[1:]
        logger.info(f"Query positions:{len(positions)} success.")
        return positions


    @retry(exceptions=(TimeoutException), tries=3, delay=3)
    def query_trade_records(self):
        '''
        默认选取近一周的交易记录
        '''
        try:
            url = "https://query.1234567.com.cn/"
            self._login(url)

            records = []
            while True:
                self._wait(by=By.CLASS_NAME, value='ui-pager')
                tag_elements = self.driver.find_element(By.ID, 'tb_delegate').find_elements(By.TAG_NAME, 'tr')
                for tag in tag_elements[1:]:
                    records.append(tag.text)

                try:
                    self.driver.find_element(By.CSS_SELECTOR, "[class='ui-pager-item ui-pager-next IE6']").click()
                    time.sleep(0.5)
                except NoSuchElementException as error:
                    break
        finally: 
            self.driver.quit()

        logger.info(f"Query trade records:{len(records)} success.")
        return records



