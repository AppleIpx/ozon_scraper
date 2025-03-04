import time as tm

from bs4 import BeautifulSoup, Tag
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By


def _get_stars_reviews(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """Функция для получения рейтинга и отзывов продавца."""
    try:
        product_statistic = soup.find(
            "div",
            attrs={"data-widget": "webSingleProductScore"},
        )
        if product_statistic:
            product_statistic = product_statistic.text.strip()
            if (
                product_statistic
                and " • " in product_statistic  # type:ignore[operator]
            ):
                product_stars = product_statistic.split(  # type:ignore[attr-defined]
                    " • ",
                )[0].strip()
                product_reviews = product_statistic.split(  # type:ignore[attr-defined]
                    " • ",
                )[1].strip()
                return product_stars, product_reviews

        return None, None

    except AttributeError:
        return None, None


def _get_sale_price(soup: BeautifulSoup) -> str | None:
    """Функция для получения цены с Ozon Картой."""

    price_element = soup.find("span", string="c Ozon Картой")
    if not price_element or not price_element.parent:
        return None

    price_container = price_element.parent.find("div")
    if not price_container:
        return None

    price_span = price_container.find("span")  # type:ignore[attr-defined]
    if not price_span or not price_span.text:
        return None

    return price_span.text.strip().replace("\u2009", "")


def _get_full_prices(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """Функция для получения цены до скидок и без Ozon Карты."""

    price_element = soup.find("span", string="без Ozon Карты")
    if not price_element or not price_element.parent or not price_element.parent.parent:
        return None, None

    try:
        price_containers = price_element.parent.parent.find("div")
        if not price_containers:
            return None, None
        price_spans = price_containers.find_all("span")  # type:ignore[attr-defined]
    except AttributeError:
        return None, None

    def _clean_price(price: str) -> str:
        """Функция, которая удаляет ненужные символы из строки, представляющей цену."""
        return price.replace("\u2009", "").replace("₽", "").strip() if price else ""

    product_discount_price = (
        _clean_price(price_spans[0].text.strip()) if price_spans else None
    )
    product_base_price = (
        _clean_price(price_spans[1].text.strip()) if len(price_spans) > 1 else None
    )

    return product_discount_price, product_base_price


def _get_product_name(soup: BeautifulSoup) -> str:
    """Функция для получения имени продукта."""
    heading_div = soup.find("div", attrs={"data-widget": "webProductHeading"})

    if not isinstance(heading_div, Tag):
        return ""

    title_element = heading_div.find("h1")

    if not isinstance(title_element, Tag):
        return ""

    return title_element.text.strip().replace("\t", "").replace("\n", " ")


def _get_salesman_name(soup: BeautifulSoup) -> str | None:
    """Функция для получения имени продавца."""
    try:
        return soup.find_all("div", class_="l5k_28")[0].text
    except AttributeError:
        return None


def _get_product_id(driver: WebDriver) -> str:
    """Функция для получения артикула товара."""
    return driver.find_element(
        By.XPATH,
        '//div[contains(text(), "Артикул: ")]',
    ).text.split("Артикул: ")[1]


def get_characteristics(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """Функция для получения длины и ширины товара."""
    all_characteristics = soup.find_all("dl", class_="ok9_28")
    length, weight = None, None
    for char in all_characteristics:
        if not isinstance(char, Tag):
            continue

        title_element = char.find("dt")
        value_element = char.find("dd")

        title = (
            title_element.get_text(strip=True)
            if isinstance(title_element, Tag)
            else None
        )
        value = (
            value_element.get_text(strip=True)
            if isinstance(value_element, Tag)
            else None
        )

        if title == "Длина, м":
            length = value
        elif title == "Вес товара, г":
            weight = value

    return length, weight


def collect_product_info(driver: WebDriver, url: str) -> dict[str, str | None]:
    """
    Функция для сбора информации о товаре.

    Функция парсит данные со страницы и возвращает словарь данных,
    при условии, что не были найдены похожие товары.

    Также может вернуть список из словарей, при нахождении похожих товаров.
    """
    driver.switch_to.new_window("tab")

    tm.sleep(1)
    driver.get(url=url)
    tm.sleep(1)
    page_source = str(driver.page_source)
    soup = BeautifulSoup(page_source, "lxml")

    product_id = _get_product_id(driver)
    product_name = _get_product_name(soup)
    product_stars, product_reviews = _get_stars_reviews(soup)
    product_ozon_card_price = _get_sale_price(soup)
    product_discount_price, product_base_price = _get_full_prices(soup)
    salesman = _get_salesman_name(soup)
    characteristics = get_characteristics(soup)

    product_data = {
        "product_id": product_id,
        "product_name": product_name,
        "product_ozon_card_price": product_ozon_card_price,
        "product_discount_price": product_discount_price,
        "product_base_price": product_base_price,
        "product_length": characteristics[0],
        "product_weight": characteristics[1],
        "product_stars": product_stars,
        "product_reviews": product_reviews,
        "salesman": salesman,
        "product_url": url,
    }

    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    return product_data
