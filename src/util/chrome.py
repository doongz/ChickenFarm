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
        self.driver.find_element(By.ID, 'tbname').send_keys(
            config.tiantian_username)

        time.sleep(0.5)
        self.driver.find_element(By.ID, 'tbpwd').send_keys(
            config.tiantian_password)
        self.driver.find_element(By.ID, 'protocolCheckbox').click()
        self.driver.find_element(By.ID, 'btn_login').click()

        # TODO: 登陆时滑窗验证码解决
        # https://zhuanlan.zhihu.com/p/558564102

    def _wait(self, by, value, timeout=10, frequency=0.5, message='Element not found'):
        WebDriverWait(driver=self.driver, timeout=timeout, poll_frequency=frequency) \
            .until(lambda x: x.find_element(by=by, value=value),
                   message=message)

    @retry(exceptions=(TimeoutException, StaleElementReferenceException), tries=3, delay=3)
    def query_assets(self):
        '''
        获取仓位数据
        '''
        url = "https://trade.1234567.com.cn/MyAssets/hold"
        self._login(url)
        self._wait(by=By.ID, value='fundlist')
        time.sleep(3) # 强行等数据刷出来，上面一行没用等到也没数据

        timeout = 5
        positions = []
        while True:
            # 这里网站里的元素变化了，这里要重新改
            tag_elements = self.driver.find_element(By.ID, 'fundlist').find_elements(By.TAG_NAME, 'ul')
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

        positions = positions[1:]  # 去除标题列名
        logger.info(f"Query assets: {len(positions)} success.")
        return positions

    @retry(exceptions=(TimeoutException, StaleElementReferenceException), tries=3, delay=3)
    def query_investments(self):
        """
        获取定投数据
        """
        try:
            url = "https://trade.1234567.com.cn/Investment/default"
            self._login(url)
            self._wait(by=By.CLASS_NAME, value='mctb')

            timeout = 5
            while True:
                investments = []
                tables = self.driver.find_elements(By.CLASS_NAME, 'mctb')
                for table in tables:
                    tag_elements = table.find_elements(By.TAG_NAME, 'tr')
                    for tag in tag_elements:
                        investments.append(tag.text)

                if "数据加载中" not in "".join(investments):
                    break
                elif timeout < 0:
                    raise Exception(f"Query position timeout.")
                else:
                    logger.warning(f"数据加载中..., 正在重试。")
                    time.sleep(1)
                    timeout -= 1

        finally:
            self.driver.quit()
        logger.info(f"Query assets: {len(investments)} success.")
        return investments
