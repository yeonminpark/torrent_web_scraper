from utils.config_manager import ConfigManager

class ScraperConfig():
    def __init__(self, scraper_configuration, local_machine):
        "scraper_configuration은 static, local_machine은 dynamic 성격을 가짐."
        self.__file_scraper_configuration = scraper_configuration
        self.__manager_scraper_configuration = ConfigManager(self.__file_scraper_configuration)
        self.__file_local_machine = local_machine
        self.__manager_local_machine = ConfigManager(self.__file_local_machine)

    def get_beautifulsoup_ingredients(self, sitename):
        find1 = self.get_config_scraper(sitename, 'find1')
        find2 = self.get_config_scraper(sitename, 'find2')
        findall1 = self.get_config_scraper(sitename, 'findall1')
        findall2 = self.get_config_scraper(sitename, 'findall2')
        findre = self.get_config_scraper(sitename, 'findre')        
        return find1, find2, findall1, findall2, findre

    def get_config_local(self, sitename, attr):
        attr = "%s-%s" % (sitename, attr)
        return self.__manager_local_machine.get_attr_config(attr)

    def set_config_local(self, sitename, attr, value):
        attr = "%s-%s" % (sitename, attr)
        self.__manager_local_machine.set_attr_config(attr, value)

    def get_config_scraper(self, sitename, attr):
        attr = "%s-%s" % (sitename, attr)
        return self.__manager_scraper_configuration.get_attr_config(attr)

    def set_config_scraper(self, sitename, attr, value):
        attr = "%s-%s" % (sitename, attr)
        self.__manager_scraper_configuration.set_attr_config(attr, value)
