"""
Reporting Module for vAuto Feature Verification System.

Handles:
- Execution report generation
- Notification sending
- Processing metrics logging
"""

import logging
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

class ReportingModule:
    """
    Module for generating reports and sending notifications.
    """
    
    def __init__(self, config):
        """
        Initialize the reporting module.
        
        Args:
            config (dict): System configuration
        """
        self.config = config
        self.reports_dir = "reports"
        
        # Create reports directory if it doesn't exist
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
            logger.info(f"Created reports directory: {self.reports_dir}")
    
    async def generate_report(self, dealer_config, stats):
        """
        Generate an execution report.
        
        Args:
            dealer_config (dict): Dealer configuration
            stats (dict): Processing statistics
            
        Returns:
            str: Path to generated report file
        """
        logger.info(f"Generating report for dealership: {dealer_config['name']}")
        
        # Create report data
        report_data = {
            "dealership": {
                "name": dealer_config['name'],
                "dealer_id": dealer_config['dealer_id']
            },
            "execution_time": datetime.now().isoformat(),
            "stats": stats
        }
        
        # Create report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dealer_name = dealer_config['name'].lower().replace(' ', '_')
        filename = f"{self.reports_dir}/{timestamp}_{dealer_name}_report.json"
        
        # Write report to file
        try:
            with open(filename, "w") as f:
                json.dump(report_data, f, indent=2)
            
            logger.info(f"Report generated: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise
    
    async def send_notification(self, dealer_config, stats, report_file=None):
        """
        Send notification email with execution results.
        
        Args:
            dealer_config (dict): Dealer configuration
            stats (dict): Processing statistics
            report_file (str, optional): Path to report file
            
        Returns:
            bool: True if notification sent successfully
        """
        logger.info(f"Sending notification for dealership: {dealer_config['name']}")
        
        # Get recipients
        recipients = dealer_config.get('report_recipients', [])
        if not recipients and 'email_recipients' in self.config['reporting']:
            recipients = self.config['reporting']['email_recipients']
        
        if not recipients:
            logger.warning("No notification recipients specified, skipping notification")
            return False
        
        # Create message
        try:
            message = self._create_notification_message(dealer_config, stats, recipients, report_file)
            
            # Mock sending email for now
            # In actual implementation, this would use smtplib to send the email
            logger.info(f"Would send notification to: {', '.join(recipients)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
    
    def _create_notification_message(self, dealer_config, stats, recipients, report_file=None):
        """
        Create notification email message.
        
        Args:
            dealer_config (dict): Dealer configuration
            stats (dict): Processing statistics
            recipients (list): List of email recipients
            report_file (str, optional): Path to report file
            
        Returns:
            MIMEMultipart: Email message
        """
        # Create message
        message = MIMEMultipart()
        message["From"] = "vauto-verification@example.com"
        message["To"] = ", ".join(recipients)
        message["Subject"] = f"vAuto Feature Verification Report - {dealer_config['name']}"
        
        # Create message body
        body = f"""
        <html>
        <body>
            <h2>vAuto Feature Verification Report</h2>
            <p><strong>Dealership:</strong> {dealer_config['name']}</p>
            <p><strong>Execution Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <h3>Processing Statistics</h3>
            <ul>
                <li><strong>Vehicles Processed:</strong> {stats['vehicles_processed']}</li>
                <li><strong>Successful Updates:</strong> {stats['successful_updates']}</li>
                <li><strong>Failed Updates:</strong> {stats['failed_updates']}</li>
                <li><strong>Features Found:</strong> {stats['features_found']}</li>
                <li><strong>Features Mapped:</strong> {stats['features_mapped']}</li>
                <li><strong>Checkboxes Updated:</strong> {stats['checkboxes_updated']}</li>
            </ul>
        """
        
        # Add error information if available
        if 'error' in stats:
            body += f"""
            <h3>Error Information</h3>
            <p style="color: red;">{stats['error']}</p>
            """
        
        # Add processing time if available
        if 'processing_time_minutes' in stats:
            body += f"""
            <p><strong>Processing Time:</strong> {stats['processing_time_minutes']:.2f} minutes</p>
            """
        
        # Close the HTML body
        body += """
        </body>
        </html>
        """
        
        # Attach message body
        message.attach(MIMEText(body, "html"))
        
        return message
    
    def log_metrics(self, dealer_config, stats):
        """
        Log processing metrics.
        
        Args:
            dealer_config (dict): Dealer configuration
            stats (dict): Processing statistics
        """
        logger.info(f"Logging metrics for dealership: {dealer_config['name']}")
        
        # In actual implementation, this could write to a database or metrics system
        # For now, just log the metrics
        log_str = f"Metrics for {dealer_config['name']}: " \
                f"Vehicles={stats['vehicles_processed']}, " \
                f"Success={stats['successful_updates']}, " \
                f"Failed={stats['failed_updates']}, " \
                f"Features={stats['features_found']}, " \
                f"Mapped={stats['features_mapped']}, " \
                f"Updated={stats['checkboxes_updated']}"
                
        if 'processing_time_minutes' in stats:
            log_str += f", Time={stats['processing_time_minutes']:.2f}min"
                
        logger.info(log_str)
        
        # Save metrics to CSV for historical tracking
        try:
            metrics_file = f"{self.reports_dir}/metrics.csv"
            file_exists = os.path.exists(metrics_file)
            
            with open(metrics_file, "a") as f:
                # Write header if file doesn't exist
                if not file_exists:
                    f.write("timestamp,dealer_name,dealer_id,vehicles_processed,successful_updates," \
                          "failed_updates,features_found,features_mapped,checkboxes_updated," \
                          "processing_time_minutes\n")
                
                # Write metrics
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{timestamp},{dealer_config['name']},{dealer_config['dealer_id']}," \
                      f"{stats['vehicles_processed']},{stats['successful_updates']}," \
                      f"{stats['failed_updates']},{stats['features_found']}," \
                      f"{stats['features_mapped']},{stats['checkboxes_updated']}," \
                      f"{stats.get('processing_time_minutes', 0):.2f}\n")
            
            logger.info(f"Metrics saved to: {metrics_file}")
            
        except Exception as e:
            logger.error(f"Error saving metrics: {str(e)}")
