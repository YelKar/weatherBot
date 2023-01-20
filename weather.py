from cloudscraper import create_scraper
from bs4 import BeautifulSoup, element
from colorama import Fore, Style

import os


class Weather:
    def __init__(self, link=os.environ.get("Weather_bot_Home")):
        self.link = link
        while True:
            self.scraper = create_scraper()
            self.resp = self.scraper.get(self.link)
            self.soup: BeautifulSoup = BeautifulSoup(self.resp.text, "html.parser")

            articles = self.soup.select("article.card")
            self.days = list(filter(
                lambda block: block.select_one(".weather-table__body"),
                articles
            ))
            if self.days:
                break

    def update(self):
        while True:
            self.scraper = create_scraper()
            self.resp = self.scraper.get(self.link)
            self.soup: BeautifulSoup = BeautifulSoup(self.resp.text, "html.parser")

            articles = self.soup.select("article.card")
            self.days = list(filter(
                lambda block: block.select_one(".weather-table__body"),
                articles
            ))
            if self.days:
                break

    def get_all(self):
        for day in self.days:
            day_number = day.select_one(".forecast-details__day-number").text
            month = day.select_one(".forecast-details__day-month").text
            day_name = day.select_one(".forecast-details__day-name").text
            answer = {
                "day_number": day_number,
                "month": month,
                "day_name": day_name,
                "day": {}
            }
            for day_part in day.select(".weather-table__row"):
                day_part: element.Tag
                day_part_name = day_part.select_one(".weather-table__daypart").text
                temp = day_part.select(".temp__value.temp__value_with-unit")
                weather = day_part.select_one(".weather-table__body-cell.weather-table__body-cell_type_condition").text
                answer["day"][day_part_name] = {"min_temp": temp[0].text, "max_temp": temp[1].text, "weather": weather}
            yield answer

    def print_all(self):
        for day in self.get_all():
            print(
                f'\n{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}'
                f'{day["day_number"]} '
                f'{day["month"].title()}, '
                f'{day["day_name"].title()}'
                f'{Style.RESET_ALL}'
            )
            for day_part, weather in day["day"].items():
                print(f"{Fore.LIGHTRED_EX}{day_part.title():7}"
                      f"{Fore.BLUE} - "
                      f"от {Fore.GREEN}{weather['min_temp']:3} {Fore.BLUE}"
                      f"до {Fore.GREEN}{weather['max_temp']:3}{Fore.BLUE}\t->\t"
                      f"{Fore.RED}{weather['weather']:25}{Style.RESET_ALL}")

    def get_day(self, day: int or str, of_month: bool = False):
        days = list(self.get_all())
        if isinstance(day, int):
            if of_month:
                for d in days:
                    if d["day_number"] == str(day):
                        return d
            else:
                return days[day]
        elif isinstance(day, str):
            day = day.lower()
            for d in days:
                if d["day_name"] == day:
                    return d

    @staticmethod
    def print_day(day: dict):
        print(
            f'{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}'
            f'{day["day_number"]} '
            f'{day["month"].title()}, '
            f'{day["day_name"].title()}'
            f'{Style.RESET_ALL}'
        )
        for day_part, weather in day["day"].items():
            print(f"{Fore.LIGHTRED_EX}{day_part.title():7}"
                  f"{Fore.BLUE} - "
                  f"от {Fore.GREEN}{weather['min_temp']:3} {Fore.BLUE}"
                  f"до {Fore.GREEN}{weather['max_temp']:3}{Fore.BLUE}\t->\t"
                  f"{Fore.RED}{weather['weather']:25}{Style.RESET_ALL}")
