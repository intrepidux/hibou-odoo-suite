from odoo import http, exceptions
from ..models.res_users import check_admin_auth_login

from logging import getLogger
_logger = getLogger(__name__)


class AuthAdmin(http.Controller):

    @http.route(['/auth_admin'], type='http', auth='public', website=True)
    def index(self, *args, **post):
        u = post.get('u')
        e = post.get('e')
        o = post.get('o')
        h = post.get('h')

        if not all([u, e, o, h]):
            exceptions.Warning('Invalid Request')

        u = str(u)
        e = str(e)
        o = str(o)
        h = str(h)

        try:
            user = check_admin_auth_login(http.request.env, u, e, o, h)
            
            http.request.session.uid = user.id
            http.request.session.pre_login = user.login
            # http.request.session.pre_uid = pre_uid

            with registry.cursor() as cr:
                env = odoo.api.Environment(cr, user.id, {})

                # if 2FA is disabled we finalize immediately
                user = env['res.users'].browse(user.id)
                # TODO RFC do we want to allow this mechanism with mfa?
                if not user._mfa_url():
                    http.request.session.finalize(env)

            if request and request.db == dbname:
                # Like update_env(user=request.session.uid) but works when uid is None
                request.env = odoo.api.Environment(request.env.cr, http.request.session.uid, http.request.session.context)
                request.update_context(**http.request.session.context)

            # http.request.session.uid = user.id
            # http.request.session.login = user.login
            # http.request.session.password = ''
            # http.request.session.auth_admin = int(o)
            # http.request.uid = user.id
            # uid = http.request.session.authenticate(http.request.session.db, user.login, 'x')
            # if uid is not False:
            #     http.request.params['login_success'] = True
            #     return http.request.redirect('/my/home')
            return http.request.redirect('/my/home')
        except (exceptions.Warning, ) as e:
            return http.Response(e.message, status=400)
