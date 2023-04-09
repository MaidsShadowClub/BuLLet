import scrapy  # type: ignore
import logging
import socket
import time
import datetime
from scrapy.loader import ItemLoader
from Bullet.items import BulletCVE


def is_valid(value):
    return True


class SamCVEScraper(scrapy.Spider):
    name = "SamsungCVE"

    def start_requests(self):
        url = "https://security.samsungmobile.com/securityUpdate.smsb"
        curr_year = datetime.datetime.now().year
        headers = {
            'Content-Type':
            'application/x-www-form-urlencoded'
        }
        for i in range(2015, curr_year+1):
            yield scrapy.http.Request(url,
                                      method="POST",
                                      headers=headers,
                                      body="year=%d" % i,
                                      )

    def parse(self, response: scrapy.http.Response):
        """ This function parses a samsung security bulletin

        @url https://security.samsungmobile.com/securityUpdate.smsb
        @scrapes cve_id title descr affected severity patch
        @scrapes url project spider server date
        @return items
        """
        # TODO: add cache check
        # TODO: add existense check
        vulns: scrapy.Selector
        bullet_title: scrapy.Selector

        bullet_titles = response.xpath("//div[@class='acc_title']")
        for bullet_title in bullet_titles:
            if not is_valid(bullet_title):
                continue

            sel = "following-sibling::div[1]" +\
                "//strong" +\
                "/font[starts-with(text(), 'SVE-')]"
            vulns = bullet_title.xpath(sel)
            for vuln in vulns:
                item = ItemLoader(BulletCVE(), vuln)
                item.add_value("bullet_title", bullet_title.get())
                txt = vuln.get()
                item.add_value("cve_id", txt)
                item.add_value("title", txt)

                xpath = ".." +\
                        "/following-sibling::br[1]" +\
                        "/following-sibling::text()[%d]"
                item.add_xpath("severity", xpath % 1)
                item.add_xpath("affected", xpath % 2)
                item.add_xpath("descr", xpath % 5)
                item.add_xpath("patch", xpath % 6)

                item.add_value("url", response.url)
                item.add_value("project", self.settings.get(
                    "BOT_NAME", "unknown"))
                item.add_value("spider", self.name)
                item.add_value("server", socket.gethostname())
                item.add_value("date", int(time.time()))

                i = item.load_item()
                self.log("%s - %s" % (i["cve_id"], i["title"]), logging.INFO)
                yield i
