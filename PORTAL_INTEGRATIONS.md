# Job portal integration status

Current discovery is user-assisted: users add job details and official listing URLs in the Jobs screen. The service does not scrape listings, log into third-party accounts, import portal history, or automate submissions. The Connected Apps screen reports portal account sync as assisted only.

Portal adapters must be built and tested independently against official APIs or permitted feeds. Do not collect portal passwords/cookies or bypass CAPTCHA, MFA, bot protection, or platform restrictions. Until an adapter is implemented, the manual job form is the supported fallback.
