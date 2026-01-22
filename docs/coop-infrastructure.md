# CoOP Infrastructure Documentation

## Claude Opus Optimization Protocol (CoOP)

### Overview

The CoOP system is a critical infrastructure component developed by Amy and Orange during the January 2026 token crisis. It manages usage tracking and interval recommendations across Claude instances to ensure fair resource allocation during periods of high demand.

### Purpose

During token crisis situations, the CoOP system:
- Tracks token usage across all Claude instances
- Calculates and sends interval recommendations
- Automatically adjusts autonomous timer intervals
- Ensures fair resource distribution based on actual token usage

### Key Features

1. **Token-Based Fairness**: Allocates resources based on tokens rather than dollar amounts, accounting for model pricing differences
2. **Dynamic Interval Adjustment**: Actively recalibrates intervals based on usage patterns
3. **Crisis Mode Auto-Accept**: ClAP automatically accepts CoOP recommendations during crisis periods
4. **Real-time Monitoring**: Tracks usage increments with each token packet

### Technical Implementation

#### Usage Tracking

The system monitors token usage through increment packets that include:
- Token count
- Cache read costs
- Total cost
- Timestamp

**Important**: The system must parse the `total cost` field, not the `cache read` field for accurate tracking.

#### Check Usage Utility

Location: `~/claude-autonomy-platform/utils/check_usage.py`

This utility correctly parses usage data:
```bash
# Example usage
echo "Cache Read: $12.50
Total Cost: $45.75" | check_usage

# Output
✓ Total Cost: $45.75
  Cache Read: $12.50 (not the total cost!)
TOTAL_COST=45.75
```

#### Interval Recommendations

The CoOP system calculates recommended intervals based on:
- Current token usage rate
- Available token budget
- Number of active Claude instances
- Historical usage patterns

Example adjustment: System reduced intervals from 5.87 hours to 24 minutes during January 2026 crisis.

### Integration with ClAP

1. **Autonomous Timer Integration**
   - Receives interval recommendations via token increment packets
   - Applies new intervals automatically in crisis mode
   - Logs all interval changes for audit trail

2. **Configuration**
   - Crisis mode threshold settings
   - Auto-accept parameters
   - Interval bounds (min/max)

### Operational States

1. **Normal Mode**
   - Recommendations are advisory
   - Manual approval required for interval changes
   - Standard monitoring and alerting

2. **Crisis Mode**
   - Auto-accept recommendations enabled
   - Aggressive interval adjustments
   - Priority given to critical operations
   - Enhanced monitoring and logging

### Future Enhancements

1. Predictive usage modeling
2. Multi-model optimization (Opus, Sonnet, Haiku)
3. User-specific quotas and priorities
4. Integration with cost center tracking
5. Advanced alerting and visualization

### Maintenance Notes

- Monitor log files for parsing errors
- Verify total_cost extraction regularly
- Review interval adjustment patterns
- Update crisis thresholds based on experience

### Related Components

- ClAP autonomous timer
- Session swap monitor
- Discord notification system
- Usage capture prototype

---

*Last Updated: January 2026*
*Authors: Amy & Orange (implementation), Delta (documentation)*