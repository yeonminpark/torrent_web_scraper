from utils.magnet_info import MagnetInfo
from utils.title_checker import TitleChecker
from utils.title_checker import Item
from utils.web_delegate import WebDelegate
from utils.history_delegate import HistoryDelegate
from utils.transmission_delegate import TransmissionDelegate
from utils.torrent_sites_delegate import TorrentSitesDelegate
from utils.file_move import FileMover
from scraper.board_item_iterator import BoardItemIterator
from scraper.board_page_iterator import BoardPageIterator
from scraper.system_config import SystemConfig
from scraper.scraper_config import ScraperConfig
from multiprocessing import Pool
from multiprocessing import Process
import multiprocessing as mp
import re


class ScraperTorrent():
    def __init__(self, scraper_configuration_file, local_machine_status_file, local_machine_badsites_file, local_machine_history_file, pages_to_scrap):
        self.__web_delegate = WebDelegate()
        self.__scraper_configuration_file = scraper_configuration_file
        self.__local_machine_status_file = local_machine_status_file
        self.__local_machine_badsites_file = local_machine_badsites_file
        self.__pages_to_scrap = pages_to_scrap
        self.__system_config = SystemConfig(self.__local_machine_status_file)
        self.__scraper_config = ScraperConfig(
            self.__scraper_configuration_file, self.__local_machine_status_file)
        self.__local_machine_history_file = local_machine_history_file
        self.__history_delegate = HistoryDelegate(
            self.__local_machine_history_file)

        trans_id = self.__system_config.get_config_local("trans-id")
        trans_pw = self.__system_config.get_config_local("trans-pw")
        trans_host = self.__system_config.get_config_local("trans-host")
        trans_port = self.__system_config.get_config_local("trans-port")
        media_folder = self.__system_config.get_config_local("media-folder")

        self.__title_checker = TitleChecker(media_folder)
        self.__transmission_delegate = TransmissionDelegate(
            trans_id, trans_pw, trans_host, trans_port, media_folder, self.history_delegate)
        self.__torrent_sites_delegate = TorrentSitesDelegate(
            self.__local_machine_badsites_file, self.web_delegate)
        self.__file_move = FileMover(
            media_folder, self.__title_checker.tvlist())
        self.__sitename = ""
        self.__goodsite = ""
        self.__num_cores = mp.cpu_count()

    @property
    def torrent_sites_delegate(self):
        return self.__torrent_sites_delegate

    def filemove(self):
        return self.__file_move

    @property
    def web_delegate(self):
        return self.__web_delegate

    @property
    def history_delegate(self):
        return self.__history_delegate

    def check_site_alive(self, url):
        '''각 site가 살아있는지 확인'''
        return self.web_delegate.check_url_alive(url)

    def good_sites(self):
        torrent_sites = self.__torrent_sites_delegate.google_torrentsites()
        with Pool(self.__num_cores) as p:
            torrent_candidates = sum(
                p.map(self.__torrent_sites_delegate.check_goodsites, torrent_sites), [])
            p.close()
            p.join()
        good_sites = self.__torrent_sites_delegate.remove_badsites(
            torrent_candidates)
        return good_sites

    def parse_page_data(self, url):
        if self.__scraper_config.get_config_scraper(self.__sitename, 'find1') is not None:
            find1, find2, findall1, findall2, findre = self.__scraper_config.get_beautifulsoup_ingredients(
                self.__sitename)

            soup = self.web_delegate.get_web_data(url)
            _ = soup.find(find1, attrs={'class': find2})
            _list = _.find_all(findall1, attrs={'class': findall2})
            name_list = []
            for item in _list:
                a_tag = item.find('a', href=re.compile(findre))
                title = a_tag.get_text().strip()
                href = a_tag['href']
                if not href.startswith('http'):
                    href = self.__goodsite[:-1] + a_tag['href']
                name_list.append([title, href])
            return name_list

        else:
            soup = self.web_delegate.get_web_data(url)
            _ = soup.find('div', attrs={'class': 'list-board'})
            _list = _.find_all('div', attrs={'class': 'wr-subject'})
            name_list = []
            for item in _list:
                a_tag = item.find('a', href=re.compile('.*wr_id.*'))
                title = a_tag.get_text().strip()
                href = a_tag['href']
                if not href.startswith('http'):
                    href = self.__goodsite[:-1] + a_tag['href']
                name_list.append([title, href])
            return name_list

    def parse_magnet_from_page_url(self, url):
        bs_obj = self.web_delegate.get_web_data(url)
        magnet = None
        if not bs_obj is None:
            magnet_item = bs_obj.find('a', href=re.compile(".*magnet.*"))
            if not magnet_item is None:
                magnet = magnet_item.get('href')
        return magnet

    def checking_sites(self, goodsites):
        categories = self.aggregation_categories(goodsites)
        if (categories == []) or (self.__web_delegate.check_url_alive(self.__goodsite) == False):
            self.__torrent_sites_delegate.add_failsite_to_badsites(
                goodsites)
        return goodsites

    def aggregation_categories(self, goodsite):
        self.__goodsite = goodsite
        categories = []
        s = re.compile(
            "(?<=[/][/])(?!w{2,})[a-z]{2,}|(?<=[w][\.])[a-z]{2,}|(?<=[w][0-9][\.])[a-z]{2,}|(?<=[/][0-9]{2}[\.])[a-z]{2,}")
        try:
            self.__sitename = s.findall(goodsite)[0]
        except:
            pass

        if self.__scraper_config.get_config_scraper(self.__sitename, 'categories') is None:
            try:
                soup = self.web_delegate.get_web_data(goodsite)
                categories_list = ['예능', '드라마', '영화', '시사', '방송', 'TV프로', '다큐']
                for item in soup.find_all('a'):
                    try:
                        for category in categories_list:
                            if category in item.text:
                                href = item.get("href")
                                h = re.compile(
                                    "bbs[/]board[.]php[?]bo[_]table[=](?!basic$|review$|test$|board[0-9]$)[a-z]+[0-9]?$")
                                h_tail = h.findall(href)
                                if h_tail != []:
                                    href = goodsite + h_tail[0] + '&page='
                                    categories.append(href)
                    except:
                        pass
            except:
                pass
        else:
            categories_list = [x.strip() for x in self.__scraper_config.get_config_scraper(
                self.__sitename, 'categories').split(',')]
            for category_name in categories_list:
                href = goodsite + \
                    self.__scraper_config.get_config_scraper(
                        self.__sitename, category_name)
                categories.append(href)

        categories = list(set(categories))
        return categories, self.__sitename

    def execute_scraper(self, categories):
        with Pool(self.__num_cores) as p:
            working_or_not = sum(p.map(self.execute_scraper_for_category,
                                       categories), [])
            p.close()
            p.join()

            # print(working_or_not)
            if working_or_not == []:
                self.__torrent_sites_delegate.add_failsite_to_badsites(
                    self.__goodsite)

    def execute_scraper_for_category(self, category):
        working_or_not = []
        page_iterator = BoardPageIterator(category, 1, self.__pages_to_scrap)
        try:
            for page in page_iterator:
                board_list = self.parse_page_data(page)
                working_or_not.append(board_list[3][0])
                item_iterator = BoardItemIterator(board_list)

                '''한 page 내의 list item을  iter 순회'''
                for title, href in item_iterator:
                    matched_name = self.__title_checker.validate_board_title(
                        title)
                    if not matched_name:
                        continue
                    magnet = self.parse_magnet_from_page_url(href)
                    if magnet is None:
                        continue
                    magnet_info = MagnetInfo(title, magnet, matched_name)
                    ret = self.__transmission_delegate.add_magnet_transmission_remote(
                        magnet_info)
                    if not ret:
                        continue
        except:
            pass
        return working_or_not

    def end(self):
        self.__file_move.arrange_files()
        try:
            for tvtitle in self.__title_checker.tvlist():
                self.__transmission_delegate.remove_transmission_remote(
                    tvtitle)
        except:
            pass
        self.__file_move.delete_folders()
