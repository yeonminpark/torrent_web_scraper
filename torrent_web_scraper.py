import os
import sys
import time
from scraper.scraper_torrent import ScraperTorrent
pages_to_scrap = int(sys.argv[1]) if len(sys.argv) >= 2 else 3


def main():

    root_path = os.path.abspath(os.path.dirname(__file__)) + '/'
    local_machine_status_file = root_path + \
        'local_config/local_machine_configuration.json'
    local_machine_history_file = root_path + 'local_config/magnet_history.csv'
    local_machine_badsites_file = root_path + 'local_config/badsites.csv'
    scraper_configuration_file = root_path + 'scraper/scraper_configuration.json'
    scraper = ScraperTorrent(scraper_configuration_file, local_machine_status_file, local_machine_badsites_file,
                             local_machine_history_file, pages_to_scrap)

    print("\n{}".format(time.ctime()))
    goodsites = scraper.good_sites()

# 사용 가능한 토렌트 사이트가 5개 미만이 될 다시 토렌트 사이트 검색
# 간단히 ./local_config/badsites.csv 삭제해서 토렌트 사이트 재검색 할 수 있음
    if len(goodsites) < 5 or os.path.exists(local_machine_badsites_file) == False:
        print("Re-collecting torrent sites")
        if os.path.exists(local_machine_badsites_file) == True:
            os.remove(local_machine_badsites_file)
            goodsites = scraper.good_sites()
        for goodsite in goodsites:
            print(f"Checking {goodsite}")
            scraper.checking_sites(goodsite)
        goodsites = scraper.good_sites()

    # start = int(time.time())
    for i, goodsite in enumerate(goodsites):
        categories, sitename = scraper.aggregation_categories(goodsite)
        print(f"Scraper for {sitename.upper()}")
        if categories is not None:
            scraper.execute_scraper(categories)
        if i == 3:
            break
    # end = int(time.time())
    # print(f"{end-start}")

    scraper.end()
    sys.exit()


if __name__ == '__main__':
    main()
