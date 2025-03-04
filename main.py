import json
import logging
import ssl
from pathlib import Path

from utils.collect_product_data import collect_data
from utils.load_in_excel import write_data_to_excel
from utils.prepare_work import preparation_before_work
from utils.scroll import page_down
from utils.write_products_urls_in_file import write_products_urls

ssl._create_default_https_context = ssl._create_unverified_context  # noqa: SLF001
logger = logging.getLogger(__name__)


def main() -> None:
    """Функция запуска программы."""
    try:
        logging.warning("[INFO] Сбор данных начался. Пожалуйста, ожидайте...")
        driver = preparation_before_work(item_name="ВВГ-Пнг(А)-LS 3 x 1.5")

        products_urls_list = page_down(driver=driver, class_name="kj6_24")
        write_products_urls(products_urls=products_urls_list)
        path_urls_products = Path("products_urls_dict_small.json")
        with path_urls_products.open("r", encoding="utf-8") as file:
            products_urls = json.load(file)
        collect_data(products_urls=products_urls, driver=driver)

        driver.close()
        driver.quit()

        path_data_products = Path("PRODUCTS_DATA.json")
        with path_data_products.open("r", encoding="utf-8") as file:
            products_data = json.load(file)
        write_data_to_excel(products_data=products_data)
    except Exception as e:
        logging.error(e)
        logging.error("При выполнении программы произошла ошибка")
    else:
        logging.warning("Работа выполнена успешно!")


if __name__ == "__main__":
    main()
