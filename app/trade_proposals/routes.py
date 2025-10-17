from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import json

from ..extensions import db
from ..models import TradeProposal, RosterEntry, Player, Membership, User
from ..services.analysis import analyze_trade

trade_proposals_bp = Blueprint("trade_proposals", __name__, url_prefix="/trade-proposals")


@trade_proposals_bp.route("/<int:league_id>")
@login_required
def list_proposals(league_id: int):
    """List all trade proposals for the current user"""
    # Check membership
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        flash("You are not a member of this league", "danger")
        return redirect(url_for("league.dashboard"))
    
    # Get proposals where user is proposer or recipient
    proposals = TradeProposal.query.filter(
        (TradeProposal.league_id == league_id) &
        ((TradeProposal.proposer_id == current_user.id) | (TradeProposal.recipient_id == current_user.id))
    ).order_by(TradeProposal.created_at.desc()).all()
    
    # Add player data to each proposal
    for proposal in proposals:
        # Get offered players
        offered_entry_ids = proposal.offered_player_ids.split(',')
        proposal.offered_entries = RosterEntry.query.filter(RosterEntry.id.in_(offered_entry_ids)).all()
        
        # Get requested players
        requested_entry_ids = proposal.requested_player_ids.split(',')
        proposal.requested_entries = RosterEntry.query.filter(RosterEntry.id.in_(requested_entry_ids)).all()
    
    return render_template("trade_proposals/list.html", league_id=league_id, proposals=proposals)


@trade_proposals_bp.route("/<int:league_id>/create", methods=["GET", "POST"])
@login_required
def create_proposal(league_id: int):
    """Create a new trade proposal"""
    # Check membership
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        flash("You are not a member of this league", "danger")
        return redirect(url_for("league.dashboard"))
    
    # Get league members (excluding current user)
    league_members = User.query.join(Membership).filter(
        Membership.league_id == league_id,
        User.id != current_user.id
    ).all()
    
    # Get current user's roster
    my_roster = RosterEntry.query.filter_by(
        user_id=current_user.id, 
        league_id=league_id
    ).join(Player).order_by(Player.position, Player.name).all()
    
    if request.method == "POST":
        recipient_id = request.form.get("recipient_id")
        offered_entry_ids = request.form.getlist("offered_players")
        requested_entry_ids = request.form.getlist("requested_players")
        message = request.form.get("message", "").strip()
        
        if not recipient_id or not offered_entry_ids or not requested_entry_ids:
            flash("Please select a recipient and players for the trade", "warning")
            return render_template("trade_proposals/create.html", 
                                 league_id=league_id, 
                                 league_members=league_members,
                                 my_roster=my_roster)
        
        # Validate that all offered players belong to current user
        for entry_id in offered_entry_ids:
            entry = RosterEntry.query.filter_by(
                id=entry_id, 
                user_id=current_user.id, 
                league_id=league_id
            ).first()
            if not entry:
                flash("Invalid player selection", "danger")
                return render_template("trade_proposals/create.html", 
                                     league_id=league_id, 
                                     league_members=league_members,
                                     my_roster=my_roster)
        
        # Validate that all requested players belong to recipient
        for entry_id in requested_entry_ids:
            entry = RosterEntry.query.filter_by(
                id=entry_id, 
                user_id=recipient_id, 
                league_id=league_id
            ).first()
            if not entry:
                flash("Invalid player selection", "danger")
                return render_template("trade_proposals/create.html", 
                                     league_id=league_id, 
                                     league_members=league_members,
                                     my_roster=my_roster)
        
        # Create trade proposal
        proposal = TradeProposal(
            league_id=league_id,
            proposer_id=current_user.id,
            recipient_id=recipient_id,
            offered_player_ids=','.join(offered_entry_ids),
            requested_player_ids=','.join(requested_entry_ids),
            message=message
        )
        
        # Generate trade analysis
        try:
            offered_entries = RosterEntry.query.filter(RosterEntry.id.in_(offered_entry_ids)).all()
            requested_entries = RosterEntry.query.filter(RosterEntry.id.in_(requested_entry_ids)).all()
            
            # Convert to player dictionaries for analysis
            offered_players = []
            for entry in offered_entries:
                player_dict = {
                    'name': entry.player.name,
                    'position': entry.player.position,
                    'team': entry.player.team,
                    'external_id': entry.player.external_id
                }
                offered_players.append(player_dict)
            
            requested_players = []
            for entry in requested_entries:
                player_dict = {
                    'name': entry.player.name,
                    'position': entry.player.position,
                    'team': entry.player.team,
                    'external_id': entry.player.external_id
                }
                requested_players.append(player_dict)
            
            print(f"Analyzing trade: {len(offered_players)} offered, {len(requested_players)} requested")
            analysis = analyze_trade(offered_players, requested_players)
            proposal.analysis_data = json.dumps(analysis)
            print(f"Analysis completed: {analysis.get('recommendation', 'Unknown')}")
        except Exception as e:
            print(f"Trade analysis failed: {e}")
            import traceback
            traceback.print_exc()
            proposal.analysis_data = json.dumps({"error": f"Analysis failed: {str(e)}"})
        
        db.session.add(proposal)
        db.session.commit()
        
        flash("Trade proposal sent successfully", "success")
        return redirect(url_for("trade_proposals.list_proposals", league_id=league_id))
    
    return render_template("trade_proposals/create.html", 
                         league_id=league_id, 
                         league_members=league_members,
                         my_roster=my_roster)


@trade_proposals_bp.route("/<int:league_id>/view/<int:proposal_id>")
@login_required
def view_proposal(league_id: int, proposal_id: int):
    """View a specific trade proposal"""
    # Check membership
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        flash("You are not a member of this league", "danger")
        return redirect(url_for("league.dashboard"))
    
    # Get proposal
    proposal = TradeProposal.query.filter_by(
        id=proposal_id, 
        league_id=league_id
    ).first_or_404()
    
    # Check if user is involved in this trade
    if proposal.proposer_id != current_user.id and proposal.recipient_id != current_user.id:
        flash("You are not authorized to view this trade proposal", "danger")
        return redirect(url_for("trade_proposals.list_proposals", league_id=league_id))
    
    # Get player details
    offered_entry_ids = proposal.offered_player_ids.split(',')
    requested_entry_ids = proposal.requested_player_ids.split(',')
    
    offered_entries = RosterEntry.query.filter(RosterEntry.id.in_(offered_entry_ids)).all()
    requested_entries = RosterEntry.query.filter(RosterEntry.id.in_(requested_entry_ids)).all()
    
    # Parse analysis data
    analysis_data = {}
    if proposal.analysis_data:
        try:
            analysis_data = json.loads(proposal.analysis_data)
        except:
            analysis_data = {"error": "Could not parse analysis"}
    
    return render_template("trade_proposals/view.html", 
                         league_id=league_id, 
                         proposal=proposal,
                         offered_entries=offered_entries,
                         requested_entries=requested_entries,
                         analysis_data=analysis_data)


@trade_proposals_bp.route("/<int:league_id>/respond/<int:proposal_id>", methods=["POST"])
@login_required
def respond_to_proposal(league_id: int, proposal_id: int):
    """Respond to a trade proposal (accept/reject)"""
    # Check membership
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({"error": "Not a member of this league"}), 403
        flash("You are not a member of this league", "danger")
        return redirect(url_for("league.dashboard"))
    
    # Get proposal
    proposal = TradeProposal.query.filter_by(
        id=proposal_id, 
        league_id=league_id
    ).first_or_404()
    
    # Check if user is the recipient
    if proposal.recipient_id != current_user.id:
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({"error": "Not authorized to respond to this proposal"}), 403
        flash("You are not authorized to respond to this proposal", "danger")
        return redirect(url_for("trade_proposals.list_proposals", league_id=league_id))
    
    # Check if proposal is still pending
    if proposal.status != "pending":
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({"error": "This proposal has already been responded to"}), 400
        flash("This proposal has already been responded to", "warning")
        return redirect(url_for("trade_proposals.view_proposal", league_id=league_id, proposal_id=proposal_id))
    
    action = request.form.get("action") or request.json.get("action") if request.is_json else None
    
    if action == "accept":
        # Execute the trade
        try:
            execute_trade(proposal)
            proposal.status = "accepted"
            db.session.commit()
            
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({"success": True, "message": "Trade accepted successfully"})
            flash("Trade accepted and executed successfully", "success")
            
        except Exception as e:
            db.session.rollback()
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({"error": f"Failed to execute trade: {str(e)}"}), 500
            flash(f"Failed to execute trade: {str(e)}", "danger")
    
    elif action == "reject":
        proposal.status = "rejected"
        db.session.commit()
        
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({"success": True, "message": "Trade rejected"})
        flash("Trade rejected", "info")
    
    else:
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({"error": "Invalid action"}), 400
        flash("Invalid action", "danger")
    
    return redirect(url_for("trade_proposals.list_proposals", league_id=league_id))


@trade_proposals_bp.route("/<int:league_id>/cancel/<int:proposal_id>", methods=["POST"])
@login_required
def cancel_proposal(league_id: int, proposal_id: int):
    """Cancel a trade proposal (only proposer can cancel)"""
    # Check membership
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({"error": "Not a member of this league"}), 403
        flash("You are not a member of this league", "danger")
        return redirect(url_for("league.dashboard"))
    
    # Get proposal
    proposal = TradeProposal.query.filter_by(
        id=proposal_id, 
        league_id=league_id
    ).first_or_404()
    
    # Check if user is the proposer
    if proposal.proposer_id != current_user.id:
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({"error": "Not authorized to cancel this proposal"}), 403
        flash("You are not authorized to cancel this proposal", "danger")
        return redirect(url_for("trade_proposals.list_proposals", league_id=league_id))
    
    # Check if proposal is still pending
    if proposal.status != "pending":
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({"error": "This proposal has already been responded to"}), 400
        flash("This proposal has already been responded to", "warning")
        return redirect(url_for("trade_proposals.view_proposal", league_id=league_id, proposal_id=proposal_id))
    
    proposal.status = "cancelled"
    db.session.commit()
    
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({"success": True, "message": "Trade proposal cancelled"})
    flash("Trade proposal cancelled", "info")
    return redirect(url_for("trade_proposals.list_proposals", league_id=league_id))


def execute_trade(proposal):
    """Execute a trade by swapping players between rosters"""
    offered_entry_ids = proposal.offered_player_ids.split(',')
    requested_entry_ids = proposal.requested_player_ids.split(',')
    
    # Get all roster entries involved
    offered_entries = RosterEntry.query.filter(RosterEntry.id.in_(offered_entry_ids)).all()
    requested_entries = RosterEntry.query.filter(RosterEntry.id.in_(requested_entry_ids)).all()
    
    # Validate that all entries still exist and belong to correct users
    for entry in offered_entries:
        if entry.user_id != proposal.proposer_id or entry.league_id != proposal.league_id:
            raise ValueError("Invalid offered player")
    
    for entry in requested_entries:
        if entry.user_id != proposal.recipient_id or entry.league_id != proposal.league_id:
            raise ValueError("Invalid requested player")
    
    # Swap the players
    for offered_entry in offered_entries:
        offered_entry.user_id = proposal.recipient_id
    
    for requested_entry in requested_entries:
        requested_entry.user_id = proposal.proposer_id
    
    # Commit the changes
    db.session.commit()
