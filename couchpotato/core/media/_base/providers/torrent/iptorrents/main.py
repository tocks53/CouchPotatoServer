from bs4 import BeautifulSoup
from couchpotato.core.helpers.encoding import tryUrlencode
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
import traceback
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
import six

log = CPLog(__name__)


class Base(TorrentProvider):

    urls = {
        'test': 'https://www.iptorrents.com/',
        'base_url': 'https://www.iptorrents.com',
        'login': 'https://www.iptorrents.com/torrents/',
        'login_check': 'https://www.iptorrents.com/inbox.php',
        'search': 'https://www.iptorrents.com/torrents/?l%d=1%s&q=%s&qf=ti&p=%d',
    }

    http_time_between_calls = 1 #seconds
    cat_backup_id = None

    def buildUrl(self, title, media, quality):
        return self._buildUrl(title.replace(':', ''), quality['identifier'])

    def _buildUrl(self, query, quality_identifier):

        cat_ids = self.getCatId(quality_identifier)

        if not cat_ids:
            log.warning('Unable to find category ids for identifier "%s"', quality_identifier)
            return None

        return self.urls['search'] % ("&".join(("l%d=" % x) for x in cat_ids), tryUrlencode(query).replace('%', '%%'))

    def _searchOnTitle(self, title, media, quality, results):

        freeleech = '' if not self.conf('freeleech') else '&free=on'

        base_url = self.buildUrl(title, media, quality)
        if not base_url: return

        pages = 1
        current_page = 1
        while current_page <= pages and not self.shuttingDown():
            data = self.getHTMLData(base_url % (freeleech, current_page))

            if data:
                html = BeautifulSoup(data)

                try:
                    page_nav = html.find('span', attrs = {'class' : 'page_nav'})
                    if page_nav:
                        next_link = page_nav.find("a", text = "Next")
                        if next_link:
                            final_page_link = next_link.previous_sibling.previous_sibling
                            pages = int(final_page_link.string)

                    result_table = html.find('table', attrs = {'class' : 'torrents'})

                    if not result_table or 'nothing found!' in data.lower():
                        return

                    entries = result_table.find_all('tr')

                    for result in entries[1:]:

                        torrent = result.find_all('td')
                        if len(torrent) <= 1:
                            break

                        torrent = torrent[1].find('a')

                        torrent_id = torrent['href'].replace('/details.php?id=', '')
                        torrent_name = six.text_type(torrent.string)
                        torrent_download_url = self.urls['base_url'] + (result.find_all('td')[3].find('a'))['href'].replace(' ', '.')
                        torrent_details_url = self.urls['base_url'] + torrent['href']
                        torrent_size = self.parseSize(result.find_all('td')[5].string)
                        torrent_seeders = tryInt(result.find('td', attrs = {'class' : 'ac t_seeders'}).string)
                        torrent_leechers = tryInt(result.find('td', attrs = {'class' : 'ac t_leechers'}).string)

                        results.append({
                            'id': torrent_id,
                            'name': torrent_name,
                            'url': torrent_download_url,
                            'detail_url': torrent_details_url,
                            'size': torrent_size,
                            'seeders': torrent_seeders,
                            'leechers': torrent_leechers,
                        })

                except:
                    log.error('Failed to parsing %s: %s', (self.getName(), traceback.format_exc()))
                    break

            current_page += 1

    def getLoginParams(self):
        return {
            'username': self.conf('username'),
            'password': self.conf('password'),
            'login': 'submit',
        }

    def loginSuccess(self, output):
        return 'don\'t have an account' not in output.lower()

    def loginCheckSuccess(self, output):
        return '/logout.php' in output.lower()
