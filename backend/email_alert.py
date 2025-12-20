import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime
from config import Config

class EmailAlert:
    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.smtp_username = Config.SMTP_USERNAME
        self.smtp_password = Config.SMTP_PASSWORD
        self.admin_email = Config.ADMIN_EMAIL
        
        # Setup logging
        logging.basicConfig(
            filename=Config.LOG_FILE,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def send_alert(self, subject, message, to_email=None, alert_type='SECURITY'):
        """Send email alert"""
        if to_email is None:
            to_email = self.admin_email
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            msg['Subject'] = f"[{alert_type}] {subject}"
            
            # Email body
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
                    <h2 style="color: #d32f2f; border-bottom: 2px solid #f44336; padding-bottom: 10px;">
                        🔒 Security Alert: {subject}
                    </h2>
                    
                    <div style="background-color: #fff3e0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>Alert Type:</strong> {alert_type}</p>
                    </div>
                    
                    <div style="margin: 20px 0;">
                        <h3 style="color: #333;">Details:</h3>
                        <p style="background-color: #f5f5f5; padding: 15px; border-radius: 3px;">
                            {message}
                        </p>
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                        <p style="color: #666; font-size: 12px;">
                            This is an automated security alert from the Facial Recognition Auth System.
                            Please investigate this issue immediately.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"Alert email sent: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send alert email: {str(e)}")
            return False
    
    def send_lockout_alert(self, email, failed_attempts, lockout_duration="5 hours"):
        """Send lockout alert to admin"""
        subject = f"User Account Locked: {email}"
        message = f"""
        User <strong>{email}</strong> has been locked out due to multiple failed login attempts.
        
        Details:
        • Failed attempts: {failed_attempts}
        • Lockout duration: {lockout_duration}
        • Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Action Required:
        1. Review login attempts for suspicious activity
        2. Verify user identity if needed
        3. Account will auto-unlock after {lockout_duration}
        """
        
        return self.send_alert(subject, message, alert_type='LOCKOUT')
    
    def send_suspicious_login_alert(self, email, ip_address, user_agent, confidence):
        """Send alert for suspicious login attempt"""
        subject = f"Suspicious Login Attempt: {email}"
        message = f"""
        A suspicious login attempt was detected for user <strong>{email}</strong>.
        
        Details:
        • IP Address: {ip_address}
        • User Agent: {user_agent}
        • Face Match Confidence: {confidence:.2%}
        • Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        This attempt was blocked due to low facial recognition confidence or multiple failures.
        """
        
        return self.send_alert(subject, message, alert_type='SUSPICIOUS_LOGIN')
    
    def send_successful_login_alert(self, email, ip_address, user_agent):
        """Send alert for successful login from new device/location"""
        subject = f"Successful Login: {email}"
        message = f"""
        User <strong>{email}</strong> has successfully logged in.
        
        Details:
        • IP Address: {ip_address}
        • User Agent: {user_agent}
        • Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        This is for your information. No action required.
        """
        
        return self.send_alert(subject, message, alert_type='INFO')