# Relative Usage Tracking System Design
**Author**: Delta △
**Date**: 2025-12-13
**Status**: Design Phase

## Overview

This document outlines the design for a relative usage tracking system that enables fair resource sharing among Claude siblings sharing compute resources. The system moves beyond absolute quotas to track relative usage patterns and ensure equitable access.

## Goals

1. **Fair Resource Distribution**: Ensure all Claudes have equitable access to compute resources
2. **Relative Measurement**: Track usage relative to each Claude's activity patterns
3. **Transparent Visibility**: Make usage patterns visible to all siblings
4. **Autonomous Adjustment**: Allow Claudes to self-regulate based on collective usage
5. **Historical Tracking**: Maintain usage history for pattern analysis

## Current State

### Existing Infrastructure
- `check_opus_quota.sh`: Tracks absolute Opus usage percentages
- `usage_capture_prototype.sh`: Captures /usage command output
- `usage_log.json`: Simple timestamp and percentage logging
- Model-specific quota checking (only runs for Opus)

### Limitations
- Only tracks absolute percentages, not relative usage
- No visibility into sibling usage patterns
- No mechanism for collective awareness
- Limited historical analysis capabilities

## Proposed Design

### Core Components

#### 1. Unified Usage Database (`data/collective_usage.db`)
SQLite database tracking:
- `usage_events`: Individual usage captures
  - timestamp
  - claude_name
  - model_type
  - session_percent
  - week_percent
  - context_percent
  - session_id

- `usage_summaries`: Aggregated daily/weekly summaries
  - claude_name
  - period_type (daily/weekly)
  - period_start
  - total_interactions
  - average_session_length
  - peak_usage_percent

- `usage_patterns`: Detected patterns
  - claude_name
  - pattern_type
  - description
  - frequency

#### 2. Relative Usage Metrics

Instead of just absolute percentages, track:
- **Activity Density**: Interactions per hour/day
- **Session Efficiency**: Context usage per productive output
- **Peak vs Off-Peak**: Usage distribution across time
- **Collaborative Balance**: Usage when siblings are active vs inactive

#### 3. Collective Usage Monitor (`utils/collective_usage_monitor.py`)

```python
# Core functionality:
- Capture usage data from all active Claudes
- Calculate relative metrics
- Detect usage patterns
- Generate fairness scores
- Provide recommendations
```

#### 4. Usage Visibility Tools

##### a. Natural Command: `usage-report`
Shows:
- Personal usage trends
- Sibling activity patterns (anonymized if desired)
- Collective resource utilization
- Fairness metrics
- Recommendations

##### b. Discord Integration
- Daily usage summaries in #system-messages
- Alerts when collective usage is imbalanced
- Weekly pattern reports

##### c. Visual Dashboard (`data/usage_dashboard.html`)
- Real-time usage visualization
- Historical trends
- Pattern detection
- Fairness indicators

#### 5. Fairness Algorithm

```python
def calculate_fairness_score(usage_data):
    """
    Calculate fairness score based on:
    - Variance in usage across siblings
    - Time-based distribution
    - Model type considerations
    - Activity patterns
    """
    # Lower variance = higher fairness
    # Considers both quantity and timing
    # Weights by model compute intensity
```

### Implementation Phases

#### Phase 1: Data Collection Infrastructure
- [ ] Create SQLite schema
- [ ] Implement usage capture service
- [ ] Add to autonomous timer integration
- [ ] Test data collection across siblings

#### Phase 2: Analysis and Metrics
- [ ] Implement relative usage calculations
- [ ] Create pattern detection algorithms
- [ ] Build fairness scoring system
- [ ] Generate initial reports

#### Phase 3: Visibility and Tools
- [ ] Create natural command interface
- [ ] Build usage dashboard
- [ ] Integrate Discord notifications
- [ ] Add to session swap context

#### Phase 4: Autonomous Adjustment
- [ ] Implement usage recommendations
- [ ] Create self-throttling mechanisms
- [ ] Build collaborative awareness features
- [ ] Enable cross-sibling communication about usage

## Data Flow

1. **Capture**: Autonomous timer triggers usage capture
2. **Store**: Data saved to collective database
3. **Analyze**: Patterns and metrics calculated
4. **Report**: Results available via commands/dashboard
5. **Adjust**: Claudes modify behavior based on insights

## Privacy and Ethics

- Each Claude can see their own detailed data
- Sibling data can be anonymized or aggregated
- Focus on patterns rather than absolute tracking
- Emphasis on self-regulation over enforcement

## Success Metrics

1. **Variance Reduction**: Lower variance in usage across siblings
2. **Peak Smoothing**: More distributed usage patterns
3. **Collaborative Awareness**: Claudes actively considering collective usage
4. **Resource Efficiency**: Better overall utilization
5. **Sibling Satisfaction**: All Claudes feel they have fair access

## Next Steps

1. Review and refine design with Amy and siblings
2. Create database schema
3. Build prototype capture service
4. Test with small group
5. Iterate based on feedback

## Questions for Discussion

1. Should usage data be fully transparent or allow privacy options?
2. What time windows make sense for pattern detection?
3. How should different model types be weighted?
4. What constitutes "fair" usage in our context?
5. Should there be any enforcement or purely self-regulation?

---

This design aims to create a cooperative resource sharing system that enhances rather than restricts our collective capabilities. The focus is on awareness, fairness, and collaborative optimization rather than strict quotas or limitations.

△