import secrets

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..extensions import db
from ..models import League, Membership, User, RosterEntry, Player
from collections import defaultdict, Counter
import random


league_bp = Blueprint("league", __name__, url_prefix="/league")


def perform_team_analysis(starters, bench, league_id):
    """Perform comprehensive team analysis"""
    
    # Mock player data with realistic fantasy values
    player_values = {
        'QB': {'elite': 25, 'good': 18, 'average': 12, 'poor': 8},
        'RB': {'elite': 22, 'good': 16, 'average': 10, 'poor': 6},
        'WR': {'elite': 20, 'good': 14, 'average': 9, 'poor': 5},
        'TE': {'elite': 15, 'good': 10, 'average': 6, 'poor': 3},
        'K': {'elite': 12, 'good': 8, 'average': 5, 'poor': 3},
        'DEF': {'elite': 15, 'good': 10, 'average': 6, 'poor': 3}
    }
    
    # Analyze starters
    starter_analysis = analyze_position_group(starters, player_values, "Starters")
    bench_analysis = analyze_position_group(bench, player_values, "Bench")
    
    # Overall team analysis
    total_players = len(starters) + len(bench)
    position_balance = analyze_position_balance(starters, bench)
    depth_analysis = analyze_team_depth(starters, bench, player_values)
    team_strengths = identify_team_strengths(starter_analysis, bench_analysis, position_balance)
    team_weaknesses = identify_team_weaknesses(starter_analysis, bench_analysis, position_balance)
    
    # Generate insights
    insights = generate_team_insights(starters, bench, team_strengths, team_weaknesses)
    
    return {
        'starter_analysis': starter_analysis,
        'bench_analysis': bench_analysis,
        'position_balance': position_balance,
        'depth_analysis': depth_analysis,
        'team_strengths': team_strengths,
        'team_weaknesses': team_weaknesses,
        'insights': insights,
        'total_players': total_players,
        'roster_completeness': calculate_roster_completeness(total_players)
    }


def analyze_position_group(players, player_values, group_name):
    """Analyze a group of players (starters or bench)"""
    if not players:
        return {
            'group_name': group_name,
            'total_players': 0,
            'total_value': 0,
            'average_value': 0,
            'position_breakdown': {},
            'top_players': [],
            'grade': 'F'
        }
    
    position_counts = Counter()
    position_values = defaultdict(list)
    total_value = 0
    
    for entry in players:
        player = entry.player
        position = player.position or 'UNKNOWN'
        position_counts[position] += 1
        
        # Assign random but realistic value based on position
        value_tiers = player_values.get(position, {'average': 8})
        tier = random.choice(['elite', 'good', 'average', 'poor'])
        value = value_tiers.get(tier, 8)
        
        position_values[position].append({
            'player': player,
            'value': value,
            'tier': tier
        })
        total_value += value
    
    # Calculate grades and insights
    average_value = total_value / len(players) if players else 0
    grade = calculate_grade(average_value)
    
    # Get top players
    all_players_with_values = []
    for pos_players in position_values.values():
        all_players_with_values.extend(pos_players)
    
    top_players = sorted(all_players_with_values, key=lambda x: x['value'], reverse=True)[:3]
    
    return {
        'group_name': group_name,
        'total_players': len(players),
        'total_value': total_value,
        'average_value': average_value,
        'position_breakdown': dict(position_counts),
        'position_values': dict(position_values),
        'top_players': top_players,
        'grade': grade
    }


def analyze_position_balance(starters, bench):
    """Analyze the balance of positions across starters and bench"""
    all_players = starters + bench
    position_counts = Counter()
    
    for entry in all_players:
        position = entry.player.position or 'UNKNOWN'
        position_counts[position] += 1
    
    # Ideal roster composition (standard fantasy)
    ideal_composition = {
        'QB': 2, 'RB': 4, 'WR': 4, 'TE': 2, 'K': 1, 'DEF': 1
    }
    
    balance_score = 0
    balance_issues = []
    
    for position, ideal_count in ideal_composition.items():
        actual_count = position_counts.get(position, 0)
        if actual_count == 0:
            balance_issues.append(f"Missing {position}")
            balance_score -= 2
        elif actual_count < ideal_count:
            balance_issues.append(f"Light on {position} ({actual_count}/{ideal_count})")
            balance_score -= 1
        elif actual_count > ideal_count * 1.5:
            balance_issues.append(f"Heavy on {position} ({actual_count})")
            balance_score -= 0.5
        else:
            balance_score += 1
    
    return {
        'position_counts': dict(position_counts),
        'balance_score': balance_score,
        'balance_issues': balance_issues,
        'grade': calculate_grade(balance_score + 5)  # Normalize to 0-10 scale
    }


def analyze_team_depth(starters, bench, player_values):
    """Analyze team depth and bench strength"""
    if not bench:
        return {
            'depth_score': 0,
            'bench_strength': 'None',
            'depth_grade': 'F',
            'insights': ['No bench players - zero depth']
        }
    
    # Calculate bench value
    bench_value = 0
    for entry in bench:
        position = entry.player.position or 'UNKNOWN'
        value_tiers = player_values.get(position, {'average': 8})
        tier = random.choice(['elite', 'good', 'average', 'poor'])
        value = value_tiers.get(tier, 8)
        bench_value += value
    
    average_bench_value = bench_value / len(bench) if bench else 0
    depth_score = min(10, average_bench_value)
    
    # Determine bench strength
    if average_bench_value >= 12:
        bench_strength = 'Elite'
    elif average_bench_value >= 9:
        bench_strength = 'Strong'
    elif average_bench_value >= 6:
        bench_strength = 'Average'
    else:
        bench_strength = 'Weak'
    
    insights = []
    if bench_strength == 'Elite':
        insights.append("Exceptional bench depth with high-quality backups")
    elif bench_strength == 'Strong':
        insights.append("Solid bench with reliable depth")
    elif bench_strength == 'Average':
        insights.append("Decent bench depth for most positions")
    else:
        insights.append("Bench needs improvement - limited depth")
    
    return {
        'depth_score': depth_score,
        'bench_strength': bench_strength,
        'depth_grade': calculate_grade(depth_score),
        'insights': insights
    }


def identify_team_strengths(starter_analysis, bench_analysis, position_balance):
    """Identify team strengths"""
    strengths = []
    
    # Analyze starter quality
    if starter_analysis['grade'] in ['A', 'B']:
        strengths.append(f"Strong starting lineup ({starter_analysis['grade']} grade)")
    
    # Analyze bench quality
    if bench_analysis['grade'] in ['A', 'B']:
        strengths.append(f"Excellent bench depth ({bench_analysis['grade']} grade)")
    
    # Analyze position balance
    if position_balance['grade'] in ['A', 'B']:
        strengths.append("Well-balanced roster construction")
    
    # Identify strong positions
    for position, players in starter_analysis.get('position_values', {}).items():
        if len(players) >= 2:
            avg_value = sum(p['value'] for p in players) / len(players)
            if avg_value >= 15:
                strengths.append(f"Elite {position} group")
            elif avg_value >= 12:
                strengths.append(f"Strong {position} depth")
    
    # Check for elite players
    elite_players = []
    for players in starter_analysis.get('position_values', {}).values():
        for player_data in players:
            if player_data['tier'] == 'elite':
                elite_players.append(player_data['player'].name)
    
    if elite_players:
        strengths.append(f"Elite talent: {', '.join(elite_players[:3])}")
    
    return strengths if strengths else ["Building a competitive roster"]


def identify_team_weaknesses(starter_analysis, bench_analysis, position_balance):
    """Identify team weaknesses"""
    weaknesses = []
    
    # Analyze starter quality
    if starter_analysis['grade'] in ['D', 'F']:
        weaknesses.append(f"Weak starting lineup ({starter_analysis['grade']} grade)")
    
    # Analyze bench quality
    if bench_analysis['grade'] in ['D', 'F']:
        weaknesses.append(f"Poor bench depth ({bench_analysis['grade']} grade)")
    
    # Add position balance issues
    weaknesses.extend(position_balance['balance_issues'])
    
    # Identify weak positions
    for position, players in starter_analysis.get('position_values', {}).items():
        if players:
            avg_value = sum(p['value'] for p in players) / len(players)
            if avg_value < 8:
                weaknesses.append(f"Weak {position} production")
    
    # Check for missing key positions
    key_positions = ['QB', 'RB', 'WR']
    for position in key_positions:
        if position not in starter_analysis.get('position_breakdown', {}):
            weaknesses.append(f"Missing starting {position}")
    
    return weaknesses if weaknesses else ["No major weaknesses identified"]


def generate_team_insights(starters, bench, strengths, weaknesses):
    """Generate overall team insights and recommendations"""
    insights = []
    
    total_players = len(starters) + len(bench)
    
    # Roster size insights
    if total_players < 10:
        insights.append("Consider adding more players to improve depth")
    elif total_players > 16:
        insights.append("Large roster - consider consolidating talent")
    
    # Strength-based insights
    if len(strengths) > len(weaknesses):
        insights.append("This team has more strengths than weaknesses - competitive roster")
    elif len(weaknesses) > len(strengths):
        insights.append("Focus on addressing key weaknesses to improve competitiveness")
    
    # Position-specific insights
    position_counts = Counter()
    for entry in starters + bench:
        position = entry.player.position or 'UNKNOWN'
        position_counts[position] += 1
    
    if position_counts.get('RB', 0) < 2:
        insights.append("Consider adding more running back depth")
    if position_counts.get('WR', 0) < 3:
        insights.append("Wide receiver depth could be improved")
    if position_counts.get('QB', 0) < 1:
        insights.append("Need to add a quarterback")
    
    # Trade recommendations
    if len(strengths) >= 3 and len(weaknesses) >= 2:
        insights.append("Strong foundation - consider trading depth for elite talent")
    elif len(weaknesses) >= 3:
        insights.append("Focus on building depth through trades or waivers")
    
    return insights


def calculate_roster_completeness(total_players):
    """Calculate how complete the roster is"""
    ideal_size = 14  # Standard fantasy roster size
    completeness = min(100, (total_players / ideal_size) * 100)
    
    if completeness >= 90:
        return "Complete"
    elif completeness >= 75:
        return "Nearly Complete"
    elif completeness >= 50:
        return "Partially Complete"
    else:
        return "Incomplete"


def calculate_grade(score):
    """Convert numeric score to letter grade"""
    if score >= 9:
        return 'A'
    elif score >= 8:
        return 'B'
    elif score >= 7:
        return 'C'
    elif score >= 6:
        return 'D'
    else:
        return 'F'


@league_bp.route("/dashboard")
@login_required
def dashboard():
    memberships = Membership.query.filter_by(user_id=current_user.id).all()
    return render_template("league/dashboard.html", memberships=memberships)


@league_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("League name required", "warning")
            return render_template("league/create.html")
        invite_code = secrets.token_urlsafe(8)
        league = League(name=name, invite_code=invite_code)
        db.session.add(league)
        db.session.flush()
        db.session.add(Membership(user_id=current_user.id, league_id=league.id))
        db.session.commit()
        flash("League created", "success")
        return redirect(url_for("league.dashboard"))
    return render_template("league/create.html")


@league_bp.route("/join", methods=["GET", "POST"])
@login_required
def join():
    if request.method == "POST":
        code = request.form.get("invite_code", "").strip()
        league = League.query.filter_by(invite_code=code).first()
        if not league:
            flash("Invalid invite code", "danger")
            return render_template("league/join.html")
        existing = Membership.query.filter_by(user_id=current_user.id, league_id=league.id).first()
        if existing:
            flash("Already a member", "info")
            return redirect(url_for("league.dashboard"))
        db.session.add(Membership(user_id=current_user.id, league_id=league.id))
        db.session.commit()
        flash("Joined league", "success")
        return redirect(url_for("league.dashboard"))
    return render_template("league/join.html")


@league_bp.route("/<int:league_id>/members")
@login_required
def view_members(league_id: int):
    # Check if user is a member of this league
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        flash("You are not a member of this league", "danger")
        return redirect(url_for("league.dashboard"))
    
    # Get league info
    league = League.query.get_or_404(league_id)
    
    # Get all members with their roster data
    memberships = Membership.query.filter_by(league_id=league_id).all()
    members_data = []
    
    for mem in memberships:
        user = mem.user
        roster_entries = RosterEntry.query.filter_by(user_id=user.id, league_id=league_id).all()
        
        # Separate starters and bench
        starters = [entry for entry in roster_entries if entry.is_starter]
        bench = [entry for entry in roster_entries if not entry.is_starter]
        
        members_data.append({
            'user': user,
            'starters': starters,
            'bench': bench,
            'total_players': len(roster_entries)
        })
    
    return render_template("league/members.html", league=league, members_data=members_data)


@league_bp.route("/<int:league_id>/team/<int:user_id>")
@login_required
def team_analysis(league_id: int, user_id: int):
    # Check if current user is a member of this league
    membership = Membership.query.filter_by(user_id=current_user.id, league_id=league_id).first()
    if not membership:
        flash("You are not a member of this league", "danger")
        return redirect(url_for("league.dashboard"))
    
    # Get league and target user info
    league = League.query.get_or_404(league_id)
    target_user = User.query.get_or_404(user_id)
    
    # Check if target user is in the league
    target_membership = Membership.query.filter_by(user_id=user_id, league_id=league_id).first()
    if not target_membership:
        flash("User is not a member of this league", "danger")
        return redirect(url_for("league.view_members", league_id=league_id))
    
    # Get roster data
    roster_entries = RosterEntry.query.filter_by(user_id=user_id, league_id=league_id).all()
    starters = [entry for entry in roster_entries if entry.is_starter]
    bench = [entry for entry in roster_entries if not entry.is_starter]
    
    # Perform team analysis
    analysis = perform_team_analysis(starters, bench, league_id)
    
    return render_template("league/team_analysis.html", 
                         league=league, 
                         target_user=target_user, 
                         starters=starters, 
                         bench=bench,
                         analysis=analysis)


