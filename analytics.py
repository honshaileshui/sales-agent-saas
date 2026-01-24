import json
import os
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class AgentAnalytics:
    """
    Tracks and stores analytics data for the sales agent.
    Records metrics to help monitor performance and optimize the system.
    """
    
    def __init__(self, analytics_dir='analytics'):
        self.analytics_dir = analytics_dir
        self.current_run = {
            'run_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration_seconds': 0,
            'leads_processed': 0,
            'leads_skipped': 0,
            'leads_failed': 0,
            'research_successes': 0,
            'research_failures': 0,
            'email_gen_successes': 0,
            'email_gen_failures': 0,
            'config_used': {},
            'errors': [],
            'lead_processing_times': []
        }
        
        # Create analytics directory if it doesn't exist
        if not os.path.exists(analytics_dir):
            os.makedirs(analytics_dir)
            logger.info(f"Created analytics directory: {analytics_dir}")
    
    def start_run(self, config: Dict):
        """
        Called at the start of each agent run to record configuration.
        """
        self.current_run['config_used'] = {
            'email_template': config.get('email_settings', {}).get('template', 'unknown'),
            'email_tone': config.get('email_settings', {}).get('tone', 'unknown'),
            'research_depth': config.get('research_settings', {}).get('depth', 'unknown'),
            'max_leads': config.get('agent_settings', {}).get('max_leads_per_run', 0)
        }
        logger.info(f"Analytics tracking started for run: {self.current_run['run_id']}")
    
    def record_lead_start(self, lead_name: str):
        """
        Record when processing starts for a lead.
        """
        return {
            'lead_name': lead_name,
            'start_time': datetime.now()
        }
    
    def record_lead_complete(self, lead_timer: Dict, success: bool = True):
        """
        Record when lead processing completes.
        """
        if success:
            self.current_run['leads_processed'] += 1
        else:
            self.current_run['leads_failed'] += 1
        
        # Calculate processing time
        duration = (datetime.now() - lead_timer['start_time']).total_seconds()
        self.current_run['lead_processing_times'].append({
            'lead_name': lead_timer['lead_name'],
            'duration_seconds': duration,
            'success': success
        })
    
    def record_lead_skipped(self):
        """
        Record when a lead is skipped (already processed).
        """
        self.current_run['leads_skipped'] += 1
    
    def record_research_result(self, success: bool):
        """
        Track research operation success/failure.
        """
        if success:
            self.current_run['research_successes'] += 1
        else:
            self.current_run['research_failures'] += 1
    
    def record_email_gen_result(self, success: bool):
        """
        Track email generation success/failure.
        """
        if success:
            self.current_run['email_gen_successes'] += 1
        else:
            self.current_run['email_gen_failures'] += 1
    
    def record_error(self, error_type: str, error_message: str, lead_name: Optional[str] = None):
        """
        Record any errors that occur during processing.
        """
        self.current_run['errors'].append({
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'message': error_message,
            'lead_name': lead_name
        })
    
    def end_run(self):
        """
        Called at the end of the run to finalize and save metrics.
        """
        self.current_run['end_time'] = datetime.now().isoformat()
        
        start = datetime.fromisoformat(self.current_run['start_time'])
        end = datetime.fromisoformat(self.current_run['end_time'])
        self.current_run['duration_seconds'] = (end - start).total_seconds()
        
        # Calculate average processing time
        if self.current_run['lead_processing_times']:
            times = [t['duration_seconds'] for t in self.current_run['lead_processing_times']]
            self.current_run['avg_lead_processing_time'] = sum(times) / len(times)
        else:
            self.current_run['avg_lead_processing_time'] = 0
        
        # Calculate success rate
        total_attempted = self.current_run['leads_processed'] + self.current_run['leads_failed']
        if total_attempted > 0:
            self.current_run['success_rate'] = self.current_run['leads_processed'] / total_attempted
        else:
            self.current_run['success_rate'] = 0
        
        # Save to file
        self._save_run_data()
        
        # Update summary statistics
        self._update_summary_stats()
        
        logger.info(f"Analytics tracking completed for run: {self.current_run['run_id']}")
        
        return self.current_run
    
    def _save_run_data(self):
        """
        Save the current run's data to a JSON file.
        """
        filename = f"{self.analytics_dir}/run_{self.current_run['run_id']}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.current_run, f, indent=2)
            logger.info(f"Run analytics saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save analytics: {e}")
    
    def _update_summary_stats(self):
        """
        Update the cumulative summary statistics file.
        """
        summary_file = f"{self.analytics_dir}/summary_stats.json"
        
        # Load existing summary or create new one
        if os.path.exists(summary_file):
            try:
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
            except:
                summary = self._create_empty_summary()
        else:
            summary = self._create_empty_summary()
        
        # Update summary with current run data
        summary['total_runs'] += 1
        summary['total_leads_processed'] += self.current_run['leads_processed']
        summary['total_leads_skipped'] += self.current_run['leads_skipped']
        summary['total_leads_failed'] += self.current_run['leads_failed']
        summary['total_research_successes'] += self.current_run['research_successes']
        summary['total_research_failures'] += self.current_run['research_failures']
        summary['total_email_gen_successes'] += self.current_run['email_gen_successes']
        summary['total_email_gen_failures'] += self.current_run['email_gen_failures']
        summary['last_run_date'] = self.current_run['end_time']
        
        # Calculate overall success rate
        total_attempted = summary['total_leads_processed'] + summary['total_leads_failed']
        if total_attempted > 0:
            summary['overall_success_rate'] = summary['total_leads_processed'] / total_attempted
        
        # Save updated summary
        try:
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            logger.info("Summary statistics updated")
        except Exception as e:
            logger.error(f"Failed to update summary stats: {e}")
    
    def _create_empty_summary(self):
        """
        Create an empty summary statistics structure.
        """
        return {
            'total_runs': 0,
            'total_leads_processed': 0,
            'total_leads_skipped': 0,
            'total_leads_failed': 0,
            'total_research_successes': 0,
            'total_research_failures': 0,
            'total_email_gen_successes': 0,
            'total_email_gen_failures': 0,
            'overall_success_rate': 0,
            'first_run_date': datetime.now().isoformat(),
            'last_run_date': None
        }
    
    def get_summary_report(self) -> str:
        """
        Generate a human-readable summary report of the current run.
        """
        report = [
            "\n" + "="*70,
            "AGENT PERFORMANCE SUMMARY",
            "="*70,
            f"Run ID: {self.current_run['run_id']}",
            f"Duration: {self.current_run['duration_seconds']:.2f} seconds",
            "",
            "LEAD PROCESSING:",
            f"  Processed Successfully: {self.current_run['leads_processed']}",
            f"  Skipped (Already Done): {self.current_run['leads_skipped']}",
            f"  Failed: {self.current_run['leads_failed']}",
            f"  Success Rate: {self.current_run.get('success_rate', 0)*100:.1f}%",
            "",
            "COMPONENT PERFORMANCE:",
            f"  Research Successes: {self.current_run['research_successes']}",
            f"  Research Failures: {self.current_run['research_failures']}",
            f"  Email Gen Successes: {self.current_run['email_gen_successes']}",
            f"  Email Gen Failures: {self.current_run['email_gen_failures']}",
            "",
            "TIMING:",
            f"  Average Time Per Lead: {self.current_run.get('avg_lead_processing_time', 0):.2f} seconds",
            "",
            "CONFIGURATION:",
            f"  Template: {self.current_run['config_used'].get('email_template', 'N/A')}",
            f"  Tone: {self.current_run['config_used'].get('email_tone', 'N/A')}",
            f"  Research Depth: {self.current_run['config_used'].get('research_depth', 'N/A')}",
        ]
        
        if self.current_run['errors']:
            report.extend([
                "",
                f"ERRORS ENCOUNTERED: {len(self.current_run['errors'])}",
                "  (Check detailed logs for specifics)"
            ])
        
        report.append("="*70)
        
        return "\n".join(report)


def load_summary_stats(analytics_dir='analytics') -> Optional[Dict]:
    """
    Load the cumulative summary statistics.
    """
    summary_file = f"{analytics_dir}/summary_stats.json"
    
    if not os.path.exists(summary_file):
        return None
    
    try:
        with open(summary_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load summary stats: {e}")
        return None