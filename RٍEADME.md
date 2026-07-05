Odoo Custom SMS OTP Authentication

A custom authentication module for Odoo that extends the default login system by supporting SMS-based One-Time Password (OTP) verification alongside the traditional username/password login.

This project demonstrates how Odoo’s authentication flow can be customized to meet business-specific security and user experience requirements while remaining modular and maintainable.

⸻

✨ Features

* Custom SMS OTP authentication
* Username & Password login support
* Secure OTP verification flow
* Custom authentication controllers
* Configurable authentication behavior
* Clean and modular Odoo implementation
* Easy integration with external SMS providers
* Maintainable and extensible architecture

⸻

🚀 Business Use Case

Many organizations require a login experience that is different from Odoo’s default authentication system.

This module was designed for businesses that need:

* SMS verification during login
* Improved user authentication
* Localized login experience
* Flexible authentication workflows
* Better user convenience without sacrificing security

⸻

🛠 Technologies

* Odoo
* Python
* PostgreSQL
* XML
* QWeb
* Docker
* Git

⸻

📂 Project Structure

module/
├── controllers/
├── models/
├── security/
├── views/
├── static/
└── __manifest__.py

⸻

⚙️ Main Functionality

The authentication flow follows these steps:

1. User enters a mobile number or username.
2. The system validates the account.
3. An OTP is generated.
4. The OTP is sent through an SMS provider.
5. The user submits the verification code.
6. The system verifies the OTP.
7. A valid session is created and the user is redirected.
8. Additionally, the user can log in using their username and password registered in Odoo.
⸻

📸 Screenshots

Screenshots will be added soon.

Suggested screenshots:

* Login Page
* OTP Verification Screen
* Authentication Settings
* Successful Login Flow

⸻

💡 Technical Highlights

* Custom authentication workflow
* Odoo controller customization
* Business-oriented authentication design
* Modular architecture
* Clean separation of concerns
* Extensible implementation for future integrations

⸻

📦 Installation

1. Copy the module into your Odoo custom addons directory.
2. Update the Apps list.
3. Install the module from the Odoo Apps menu.
4. Configure your SMS provider.
5. Enable the custom authentication flow.

⸻

🔒 Security Note

This public repository is intended for demonstration and portfolio purposes.

Sensitive client information, credentials, API keys, and proprietary business logic have been removed before publication.

⸻

📈 Future Improvements

* Multi-provider SMS support
* Rate limiting for OTP requests
* Login attempt protection
* Expiration and retry configuration
* Two-Factor Authentication (2FA)
* Audit logs
* Unit and integration tests

⸻

👨‍💻 About

I’m an Odoo Developer focused on building custom business solutions, authentication systems, workflow automation, and ERP customizations using Odoo, Python, PostgreSQL, Docker, and Git.

If you’re looking for Odoo customization, module development, migrations, or business workflow automation, feel free to connect with me.