from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
import requests
import random
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    phone_number = fields.Char(string='Mobile Number', size=11, help='Iranian mobile number')
    is_phone_verified = fields.Boolean(string='Phone Verified', default=False)
    otp_code = fields.Char(string='OTP Code', size=6)
    otp_expiry = fields.Datetime(string='OTP Expiry Time')
    last_otp_request = fields.Datetime(string='Last OTP Request Time')


    @api.model
    def _signup_create_user(self, values):
        user = super()._signup_create_user(values)
        self._ensure_portal_user(user)
        return user
    def _ensure_portal_user(self, user):
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
        user_group = self.env.ref('base.group_user', raise_if_not_found=False)
        
        if portal_group:
            new_groups = [portal_group.id]
            
            if user_group and user_group.id in user.group_ids.ids:
                user.write({
                    'group_ids': [(3, user_group.id)]  
                })
            
            if portal_group.id not in user.group_ids.ids:
                user.write({
                    'group_ids': [(4, portal_group.id)]
                })
            
            _logger.info(f"User {user.login} has only Portal group")
        return user
    @api.constrains('phone_number')
    def _check_phone_number(self):
        for record in self:
            if record.phone_number:
                pattern = r'^(09|9)[0-9]{9}$'
                if not re.match(pattern, record.phone_number):
                    raise ValidationError(_('Please enter a valid Iranian phone number (e.g., 09123456789 or 9123456789)'))


    @api.model
    def get_or_create_user_by_phone(self, phone_number):

        if phone_number.startswith('9') and len(phone_number) == 10:
            phone_number = '0' + phone_number

        existing_user = self.sudo().search([('phone_number', '=', phone_number)], limit=1)
        if existing_user:
            self._ensure_portal_user(existing_user)
            return existing_user

        login_base = f"mobile_{phone_number}"
        login = login_base
        counter = 1
        while self.sudo().search([('login', '=', login)]):
            login = f"{login_base}_{counter}"
            counter += 1

        new_user = self.sudo().create({
            'name': f"User {phone_number}",
            'login': login,
            'phone_number': phone_number,
            'is_phone_verified': True,
            'active': True,
            'email': f"{phone_number}@temp.com",

        })

        new_user.action_reset_password()
        self._ensure_portal_user(new_user)
        return new_user

    def _get_default_portal_user(self):
        return self.env.ref('base.user_demo_portal')

    def generate_and_send_otp(self):
        self.ensure_one()

        if not self.phone_number:
            return False, "Phone number is not set"

        if self.last_otp_request:
            diff = fields.Datetime.now() - self.last_otp_request
            if diff.total_seconds() < 120:
                remaining = 120 - int(diff.total_seconds())
                return False, f"Please {remaining} Wait Second"

        otp = str(random.randint(100000, 999999))
        self.write({
            'otp_code': otp,
            'otp_expiry': fields.Datetime.now() + timedelta(minutes=5),
            'last_otp_request': fields.Datetime.now()
        })

        _logger.info(f"OTP generated for {self.phone_number}: {otp}")

        return self._send_sms_kaveh_negar(otp)

    def _send_sms_kaveh_negar(self, otp):
        try:
            ICP = self.env['ir.config_parameter'].sudo()
            api_key = ICP.get_param('otp_login.kaveh_negar_api_key', '')

            if not api_key:
                _logger.warning("Kaveh Negar API Key not configured - OTP logged only")
                return True, "OTP sent (test mode - no API key configured)"

            url = f"https://api.kavenegar.com/v1/{api_key}/verify/lookup.json"

            mobile = self.phone_number
            if mobile.startswith('0'):
                mobile = mobile[1:]

            payload = {
                'receptor': mobile,
                'token': otp,
                'template': 'otp-login'
            }

            response = requests.post(url, data=payload, timeout=10)

            if response.status_code == 200:
                _logger.info(f"OTP sent successfully to {self.phone_number}")
                return True, "OTP sent successfully"
            else:
                _logger.error(f"Kaveh Negar error: {response.text}")
                return False, f"SMS sending failed: {response.status_code}"

        except Exception as e:
            _logger.error(f"Error sending OTP: {str(e)}")
            return False, "Error sending OTP. Please try again later."

    def verify_otp(self, code):
        self.ensure_one()

        if not self.otp_code:
            return False, "No OTP request found. Please request a new code."

        if fields.Datetime.now() > self.otp_expiry:
            return False, "OTP has expired. Please request a new code."

        if self.otp_code != code:
            return False, "Invalid OTP code. Please try again."

        self.write({
            'otp_code': False,
            'otp_expiry': False,
            'is_phone_verified': True
        })

        return True, "OTP verified successfully"