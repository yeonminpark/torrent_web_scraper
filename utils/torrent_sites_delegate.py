import os
import sys
import csv

from googlesearch import search


class TorrentSitesDelegate:
    def __init__(self, local_machine_badsites_file, web_delegate):
        self.__web_delegate = web_delegate
        self.__badsites_file = local_machine_badsites_file

    def google_torrentsites(self):
        torrent_sites = []
        query = "토렌트 순위"

        for g in search(query, tld='co.kr', num=10, stop=3):
            torrent_sites.append(g)
        return torrent_sites

    def check_goodsites(self, torrent_site):
        candidate_sites = []

        try:
            soup = self.__web_delegate.get_web_data(torrent_site)
            exclude = 'http://jaewook.net', 'https://lsrank.com', 'https://twitter.com', 'https://ps.devbj.com', \
                'https://torrentrank.net', 'https://github.com', 'https://www.torrentdia', 'https://www.instagram.com', \
                'https://xn', 'http://www.xn', 'http://xn'
            for anchor in soup.find_all('a'):
                href = anchor.get('href')
                if href.startswith('http') and not href.startswith(exclude) and not len(href) > 35:
                    if not href.endswith('/'):
                        href = href + '/'
                    candidate_sites.append(href)
        except:
            pass
        return candidate_sites

    def remove_badsites(self, anchors):
        badsites = []
        if os.path.exists(self.__badsites_file) == True:
            with open(self.__badsites_file, encoding='utf-8',  newline='') as f:
                for row in csv.reader(f):
                    badsites.append(row[0])
        else:
            badsites = []
        goodsites = list(set(anchors)-set(badsites))
        print(f"{len(goodsites)} Torrent sites")
        return goodsites

    def add_failsite_to_badsites(self, goodsite):
        with open(self.__badsites_file, 'a+', encoding='utf-8', newline='') as f:
            badsite = [[goodsite]]
            csv_writer = csv.writer(f)
            csv_writer.writerow(badsite[0])
            # print("\tThis site will be delisted")
