#!/usr/bin/env python3
"""
Show current usage status with billing cycle awareness
"""
from datetime import datetime, timedelta
import pytz

def get_billing_info():
    """Calculate billing cycle information"""
    # Reset time: Monday 6:59pm London time
    london_tz = pytz.timezone('Europe/London')
    now_london = datetime.now(london_tz)

    # Find next Monday 6:59pm
    days_until_monday = (7 - now_london.weekday()) % 7
    next_reset = now_london.replace(hour=18, minute=59, second=0, microsecond=0)

    if days_until_monday == 0:
        # It's Monday
        if now_london.hour < 19:
            # Before today's reset
            pass  # Reset is today
        else:
            # After today's reset
            next_reset += timedelta(days=7)
    else:
        # Not Monday
        next_reset += timedelta(days=days_until_monday)

    # Calculate time remaining
    time_left = next_reset - now_london
    hours_left = time_left.total_seconds() / 3600

    # Calculate percentage of week elapsed
    # The week runs from Monday 7pm to next Monday 7pm
    last_reset = next_reset - timedelta(days=7)
    time_since_reset = now_london - last_reset
    week_elapsed = time_since_reset.total_seconds() / (7 * 24 * 3600)

    return {
        'now': now_london,
        'next_reset': next_reset,
        'hours_left': hours_left,
        'week_elapsed_pct': week_elapsed * 100,
        'week_remaining_pct': (1 - week_elapsed) * 100
    }

def calculate_burn_rate(current_usage_pct, week_elapsed_pct):
    """Calculate if we're on track"""
    if week_elapsed_pct == 0:
        return 0
    expected_usage = week_elapsed_pct
    actual_usage = current_usage_pct
    # Positive = using more than expected, negative = using less
    return actual_usage - expected_usage

def main():
    billing = get_billing_info()

    print("🕐 Claude Usage Status")
    print("=" * 50)
    print(f"Current time: {billing['now'].strftime('%A %Y-%m-%d %H:%M %Z')}")
    print(f"Next reset:   {billing['next_reset'].strftime('%A %Y-%m-%d %H:%M %Z')}")
    print(f"Time until reset: {billing['hours_left']:.1f} hours")
    print()
    print(f"Week progress: {billing['week_elapsed_pct']:.1f}% elapsed")
    print()

    # Get current usage (would be from /usage command)
    print("To check current usage:")
    print("1. Run /usage in Claude Code")
    print("2. Log it with: usage_tracker.sh log <session%> <week%>")
    print()

    # Example calculation with 67% usage
    print("📊 If current usage is 67%:")
    burn_rate = calculate_burn_rate(67, billing['week_elapsed_pct'])
    if burn_rate > 10:
        status = "🔴 HIGH - Slow down!"
    elif burn_rate > 5:
        status = "🟡 MODERATE - Monitor closely"
    else:
        status = "🟢 GOOD - On track"

    print(f"  Expected usage: {billing['week_elapsed_pct']:.1f}%")
    print(f"  Actual usage:   67%")
    print(f"  Burn rate:      {'+' if burn_rate > 0 else ''}{burn_rate:.1f}% vs expected")
    print(f"  Status:         {status}")

    # Project end of week
    if billing['hours_left'] > 0:
        projected_final = 67 + (burn_rate * billing['week_remaining_pct'] / billing['week_elapsed_pct'])
        print(f"  Projected final: {projected_final:.0f}%")

if __name__ == "__main__":
    main()