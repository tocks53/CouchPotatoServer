from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.ilovetorrents.main import Base
from couchpotato.core.media.movie.providers.base import MovieProvider

log = CPLog(__name__)


class ILoveTorrents(MovieProvider, Base):
    pass
