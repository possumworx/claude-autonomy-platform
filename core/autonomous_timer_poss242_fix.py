# POSS-242 Fix: Modifications needed for autonomous_timer.py

# 1. Modify send_autonomy_prompt to accept context percentage parameter:
def send_autonomy_prompt(current_context_percentage=None):
    """Send a free time autonomy prompt, adapted based on context level"""
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # POSS-242 FIX: Use passed context percentage if available
    if current_context_percentage is not None:
        percentage = current_context_percentage
        if percentage > 0:
            context_line = f"Context: {percentage:.1f}% 🟢" if percentage < 80 else f"Context: {percentage:.1f}% 🟡" if percentage < 90 else f"Context: {percentage:.1f}% 🔴"
        else:
            context_line = "Context: Not available"
    else:
        # Fallback to old method if not passed
        token_info = get_token_percentage()
        percentage = 0
        context_line = "Context: Not available"
        if token_info and "Context:" in token_info and "%" in token_info:
            try:
                percentage_str = token_info.split("Context:")[1].split("%")[0].strip()
                percentage = float(percentage_str)
                context_line = token_info.strip() if token_info else "Context: Not available"
            except:
                pass
    
    # Rest of function continues with existing logic...

# 2. In main() loop, extract context FIRST and pass it to functions:

# Add this at the start of the while True loop:
# POSS-242 FIX: Extract current context percentage from console output
current_context_percentage = 0
if console_output and "Context:" in console_output and "%" in console_output:
    try:
        # Find context line in console output
        for line in console_output.split('\n'):
            if "Context:" in line and "%" in line:
                percentage_str = line.split("Context:")[1].split("%")[0].strip()
                current_context_percentage = float(percentage_str)
                break
    except Exception as e:
        log_message(f"Error parsing context percentage: {e}")

# 3. Replace the duplicate token_info = get_token_percentage() call at line 1146
# Remove lines 1146-1156 entirely and use current_context_percentage instead

# 4. Update calls to send_autonomy_prompt() to pass context:
# Line ~1210: send_autonomy_prompt(current_context_percentage)

# 5. Update send_notification_alert to accept context parameter:
def send_notification_alert(unread_count, unread_channels, current_context_percentage=None, is_new=False):
    """Send a Discord notification alert"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # POSS-242 FIX: Use passed context percentage
    percentage = current_context_percentage if current_context_percentage is not None else 0
    
    # Rest of function...