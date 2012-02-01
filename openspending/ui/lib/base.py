"""The base Controller API

Provides the BaseController class for subclassing.
"""
from time import time, gmtime, strftime
import os
import babel
import gettext

from pylons.controllers import WSGIController
from pylons.templating import literal, pylons_globals
from pylons import tmpl_context as c, request, response, config
from pylons import app_globals, session
from pylons.controllers.util import abort
from genshi.filters import HTMLFormFiller
from pylons.i18n import _

from openspending.model import meta as db
from openspending.auth import require
import openspending.auth as can
from openspending import model
from openspending.ui import i18n
from openspending.plugins.core import PluginImplementations
from openspending.plugins.interfaces import IGenshiStreamFilter, IRequest

import logging
log = logging.getLogger(__name__)


ACCEPT_MIMETYPES = {
    "application/json": "json",
    "text/javascript": "json",
    "application/javascript": "json",
    "text/csv": "csv"
    }


def render(template_name,
           extra_vars=None,
           form_fill=None, form_errors={},
           suppress_cache=True,
           method='xhtml'):

    if suppress_cache:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    # Pull in extra vars if needed
    globs = extra_vars or {}

    # Second, get the globals
    globs.update(pylons_globals())
    globs['g'] = app_globals
    globs['can'] = can
    globs['_form_errors'] = form_errors

    # Grab a template reference
    template = globs['app_globals'].genshi_loader.load(template_name)

    stream = template.generate(**globs)

    if form_fill is not None:
        filler = HTMLFormFiller(data=form_fill)
        stream = stream | filler

    for item in PluginImplementations(IGenshiStreamFilter):
        stream = item.filter(stream)

    return literal(stream.render(method=method, encoding=None))

class BaseController(WSGIController):

    items = PluginImplementations(IRequest)

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        begin = time()
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            db.session.remove()
            db.session.close()
            log.debug("Request to %s took %sms" % (request.path,
               int((time() - begin) * 1000)))

    def __before__(self, action, **params):
        account_name = request.environ.get('REMOTE_USER', None)
        if account_name:
            c.account = model.Account.by_name(account_name)
        else:
            c.account = None

        i18n.handle_request(request, c)
        c.state = session.get('state', {})

        c.q = ''
        c.items_per_page = int(request.params.get('items_per_page', 20))
        c.datasets = model.Dataset.all_by_account(c.account)
        c.dataset = None
        self._detect_dataset_subdomain()

        for item in self.items:
            item.before(request, c)

        c.languages = self._detect_languages()

    def __after__(self):
        if session.get('state', {}) != c.state:
            session['state'] = c.state
            session.save()

        for item in self.items:
            item.after(request, c)

        db.session.close()

    def _detect_dataset_subdomain(self):
        http_host = request.environ.get('HTTP_HOST').lower()
        if http_host.startswith('www.'):
            http_host = http_host[len('www.'):]
        if not '.' in http_host:
            return
        dataset_name, domain = http_host.split('.', 1)
        for dataset in c.datasets:
            if dataset.name.lower() == dataset_name:
                c.dataset = dataset

    def _detect_format(self, format):
        for mimetype, mimeformat in self.accept_mimetypes.items():
            if format == mimeformat or \
                    mimetype in request.headers.get("Accept", ""):
                return mimeformat
        return "html"

    def _detect_languages(self):
        # Magic paths copied from pylons.i18n.translation._get_translator
        localedir = os.path.join(config['pylons.paths']['root'], 'i18n')
        messagefiles = gettext.find(config['pylons.package'], localedir,
                                    languages=babel.Locale('en').languages.keys(),
                                    all=True)
        languages = [path.split('/')[-3] for path in messagefiles]
        langlist = zip(languages, 
                       [babel.Locale.parse(lang).display_name for lang in languages])
        # Filter out bogus language codes before they screw us over completely
        # (Hint: 'no' is not a real language code)
        return filter(lambda (language, name): name is not None, langlist)
        
    def _get_dataset(self, dataset):
        c.dataset = model.Dataset.by_name(dataset)
        if c.dataset is None:
            abort(404, _('Sorry, there is no dataset named %r') % dataset)
        require.dataset.read(c.dataset)

    def _get_page(self, param='page'):
        try:
            return int(request.params.get(param))
        except:
            return 1
