#!/usr/bin/env python3
"""
Script to fix existing trade proposal analysis data that has nested dictionary issues.
"""

import json
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import TradeProposal

def fix_analysis_data():
    """Fix nested dictionary issues in existing trade proposal analysis data."""
    app = create_app()
    
    with app.app_context():
        # Get all trade proposals with analysis data
        proposals = TradeProposal.query.filter(TradeProposal.analysis_data.isnot(None)).all()
        
        print(f"Found {len(proposals)} trade proposals with analysis data")
        
        fixed_count = 0
        
        for proposal in proposals:
            try:
                # Parse the existing analysis data
                if isinstance(proposal.analysis_data, str):
                    analysis_data = json.loads(proposal.analysis_data)
                else:
                    analysis_data = proposal.analysis_data
                
                # Check if this needs fixing (has nested risk_assessment)
                if (analysis_data.get('risk_analysis') and 
                    isinstance(analysis_data['risk_analysis'].get('risk_assessment'), dict)):
                    
                    print(f"Fixing proposal {proposal.id}...")
                    
                    # Extract the nested data
                    risk_analysis = analysis_data['risk_analysis']
                    nested_risk = risk_analysis['risk_assessment']
                    
                    # Fix the structure
                    analysis_data['risk_analysis'] = {
                        "offered_avg_risk": risk_analysis.get('offered_avg_risk', 0),
                        "requested_avg_risk": risk_analysis.get('requested_avg_risk', 0),
                        "risk_delta": risk_analysis.get('risk_delta', 0),
                        "risk_assessment": nested_risk.get('risk_assessment', 'unknown'),
                        "injury_risk_change": nested_risk.get('injury_risk_change', {}),
                        "high_risk_players": nested_risk.get('high_risk_players', {}),
                    }
                    
                    # Update the proposal
                    proposal.analysis_data = json.dumps(analysis_data)
                    fixed_count += 1
                    
            except Exception as e:
                print(f"Error fixing proposal {proposal.id}: {e}")
                continue
        
        # Commit all changes
        if fixed_count > 0:
            db.session.commit()
            print(f"Successfully fixed {fixed_count} trade proposals")
        else:
            print("No proposals needed fixing")

if __name__ == "__main__":
    fix_analysis_data()
