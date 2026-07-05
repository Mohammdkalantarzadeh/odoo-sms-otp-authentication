from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
import re, random, logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class OTPLoginController(http.Controller):

    @http.route('/web/login', type='http', auth='public', website=True, csrf=False, sitemap=False)
    def custom_login_page(self, redirect=None, **kwargs):
        enable_otp = request.env['ir.config_parameter'].sudo().get_param(
            'otp_login.enable_otp_login', 'False'
        ) == 'True'

        if not enable_otp:
            return request.redirect('/login/standard')

        enable_native = request.env['ir.config_parameter'].sudo().get_param(
            'otp_login.enable_odoo_native_login', 'False'
        ) == 'True'

        values = {
            'enable_native_login': enable_native,
            'redirect': redirect or '/web',
            'error': kwargs.get('error', ''),
        }
        
        if hasattr(request, 'website'):
            values['website'] = request.website

        response = request.render('custom_otp_login.otp_login_page', values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return response

    @http.route('/login/standard', type='http', auth='public', website=True, csrf=False)
    def standard_login_handler(self, redirect=None, **kwargs):
        redirect = redirect or '/web'

        if request.httprequest.method == 'POST':
            login = (kwargs.get('login') or '').strip()
            password = kwargs.get('password') or ''

            if not login or not password:
                return request.render('custom_otp_login.standard_login_page', {
                    'redirect': redirect,
                    'error': 'Username and password are required',
                })

            try:
                _logger.info("LOGIN ATTEMPT: login=%r", login)

                credential = {
                    'type': 'password',
                    'login': login,
                    'password': password,
                }
                auth_info = request.session.authenticate(request.env, credential)
                uid = auth_info.get('uid') if isinstance(auth_info, dict) else auth_info

                if uid:
                    _logger.info("LOGIN SUCCESS: uid=%s", uid)
                    return request.redirect(redirect)
                else:
                    return request.render('custom_otp_login.standard_login_page', {
                        'redirect': redirect,
                        'error': 'Incorrect username or password',
                    })

            except AccessDenied:
                return request.render('custom_otp_login.standard_login_page', {
                    'redirect': redirect,
                    'error': 'Incorrect username or password',
                })
            except Exception as e:
                _logger.error("LOGIN EXCEPTION %s: %s", type(e).__name__, e, exc_info=True)
                return request.render('custom_otp_login.standard_login_page', {
                    'redirect': redirect,
                    'error': 'Incorrect username or password',
                })

        return request.render('custom_otp_login.standard_login_page', {
            'redirect': redirect,
            'error': kwargs.get('error', ''),
        })

    @http.route('/otp/send', type='json', auth='public', methods=['POST'], csrf=False)
    def send_otp(self, **kwargs):
        phone = kwargs.get('phone_number', '').strip()
        if not phone:
            return {'error': 'Mobile number is required.'}
        if phone.startswith('9') and len(phone) == 10:
            phone = '0' + phone
        if not re.match(r'^(09)[0-9]{9}$', phone):
            return {'error': 'The number is invalid.'}
        try:
            User = request.env['res.users'].sudo()
            user = User.get_or_create_user_by_phone(phone)
            User = request.env['res.users'].sudo()
            user = User.search([('phone_number', '=', phone)], limit=1)
            if not user:
                login = f"mobile_{phone}"
                counter = 1
                while User.search([('login', '=', login)], limit=1):
                    login = f"mobile_{phone}_{counter}"
                    counter += 1
                user = User.create({'name': f"User {phone}", 'login': login, 'phone_number': phone})

            if user.last_otp_request and (datetime.now() - user.last_otp_request).total_seconds() < 60:
                remaining = int(60 - (datetime.now() - user.last_otp_request).total_seconds())
                return {'error': f'please {remaining} Wait second'}

            otp = str(random.randint(100000, 999999))
            user.write({
                'otp_code': otp,
                'otp_expiry': datetime.now() + timedelta(minutes=5),
                'last_otp_request': datetime.now(),
            })


            api_key = request.env['ir.config_parameter'].sudo().get_param('otp_login.kaveh_negar_api_key', '')
            if api_key:
                try:
                    import requests as req
                    template = request.env['ir.config_parameter'].sudo().get_param('otp_login.otp_template_name', 'otp-login')
                    mobile = phone[1:] if phone.startswith('0') else phone
                    req.post(
                        f"https://api.kavenegar.com/v1/{api_key}/verify/lookup.json",
                        data={'receptor': mobile, 'token': otp, 'template': template},
                        timeout=10
                    )
                except Exception as sms_err:
                    _logger.error("Kaveh Negar error: %s", sms_err)

            res = {'success': True, 'user_id': user.id}
            if not api_key:
                res['test_otp'] = otp
            return res
        except Exception as e:
            _logger.error("send_otp error: %s", e)
            return {'error': str(e)}

    @http.route('/otp/verify', type='json', auth='public', methods=['POST'], csrf=False)
    def verify_otp(self, **kwargs):
        code = str(kwargs.get('code', '')).strip()
        user_id = kwargs.get('user_id')
        redirect_url = kwargs.get('redirect', '/web')

        if not code or not user_id:
            return {'error':"The information is incomplete."}

        try:
            user = request.env['res.users'].sudo().browse(int(user_id))
            if not user.exists():
                return {'error': 'User Not Found'}
            if not user.otp_code:
                return {'error': 'Unrequested verification code'}
            if datetime.now() > user.otp_expiry:
                user.write({'otp_code': False, 'otp_expiry': False})
                return {'error': 'Expired code'}
            if user.otp_code != code:
                return {'error': "The code is incorrect."}

            user.write({'otp_code': False, 'otp_expiry': False, 'is_phone_verified': True})


            env = request.env(user=user.id)
            user_context = dict(env['res.users'].context_get())

            request.session.should_rotate = True
            request.session.update({
                'db': request.db,
                'login': user.login,
                'uid': user.id,
                'context': user_context,
                'session_token': user.sudo()._compute_session_token(request.session.sid),
            })

            _logger.info("OTP login OK: %s (uid=%s)", user.login, user.id)
            return {'success': True, 'redirect': redirect_url}

        except Exception as e:
            _logger.error("verify_otp error: %s", e)
            return {'error': str(e)}