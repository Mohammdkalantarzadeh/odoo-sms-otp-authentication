from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    enable_otp_login = fields.Boolean(
        string="Enable OTP Login",
        config_parameter='otp_login.enable_otp_login',
        help="Enable login with phone number and OTP via SMS"
    )
    
    enable_odoo_native_login = fields.Boolean(
        string="Enable Native Odoo Login", 
        config_parameter='otp_login.enable_odoo_native_login',
        help="Show traditional username/password login form"
    )
    
    kaveh_negar_api_key = fields.Char(
        string="Kaveh Negar API Key",
        config_parameter='otp_login.kaveh_negar_api_key',
        help="Your API key from Kaveh Negar panel"
    )
    
    sender_number = fields.Char(
        string="Sender Number",
        config_parameter='otp_login.sender_number',
        default="1000596446",
        help="Your sender number registered in Kaveh Negar"
    )
    
    otp_template_name = fields.Char(
        string="OTP Template Name",
        config_parameter='otp_login.otp_template_name',
        default="otp-login",
        help="Template name for OTP in Kaveh Negar panel"
    )
    
    otp_status_html = fields.Html(
        string="OTP Status",
        compute='_compute_otp_status',
        readonly=True
    )
    
    @api.depends('kaveh_negar_api_key', 'sender_number')
    def _compute_otp_status(self):
        for record in self:
            if record.kaveh_negar_api_key and record.sender_number:
                record.otp_status_html = """
                    <div style="display: inline-flex; align-items: center; gap: 8px; background: #dcfce7; padding: 6px 12px; border-radius: 20px;">
                        <i class="fa fa-check-circle" style="color: #16a34a; font-size: 14px;"></i>
                        <span style="color: #166534; font-size: 13px; font-weight: 500;">The settings are complete.</span>
                    </div>
                """
            else:
                record.otp_status_html = """
                    <div style="display: inline-flex; align-items: center; gap: 8px; background: #fee2e2; padding: 6px 12px; border-radius: 20px;">
                        <i class="fa fa-exclamation-triangle" style="color: #dc2626; font-size: 14px;"></i>
                        <span style="color: #991b1b; font-size: 13px; font-weight: 500;"> The settings are incomplete.</span>
                    </div>
                """
    
    def action_test_otp_connection(self):
        try:
            if not self.kaveh_negar_api_key:
                raise UserError("Please enter the Kavenegar API Key first.")
            
            url = f"https://api.kavenegar.com/v1/{self.kaveh_negar_api_key}/account/info.json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': "Connection to the Kaveh Negar service was successfully established",
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError("The API key is invalid. Please check it")
                
        except Exception as e:
            raise UserError(f'Error connecting to Kavenegar: {str(e)}')