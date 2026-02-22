# Morning Briefing Service Pattern

**Trigger:** When implementing a scheduled briefing or status report service with multiple data sources.

## Pattern

Compose a briefing from multiple async data sources using dependency injection for testability.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Scheduler (cron/daemon)              │
│                  triggers at T-30 wake time             │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   BriefingService                       │
│  ┌───────────┐  ┌──────────┐  ┌────────────┐           │
│  │HealthProbe│  │EventStore│  │PriorityQueue│          │
│  └─────┬─────┘  └────┬─────┘  └──────┬─────┘          │
│        │             │               │                  │
│        ▼             ▼               ▼                  │
│   AgentStatus    Events         Priorities              │
│        │             │               │                  │
│        └─────────────┴───────────────┘                  │
│                      │                                  │
│                      ▼                                  │
│              CostGovernor                               │
│                      │                                  │
│                      ▼                                  │
│            BriefingContent → render_markdown()          │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Health Probe** → Agent availability status
2. **Event Store** → Overnight events (filtered by time window)
3. **Priority Queue** → Top N tasks ranked by urgency/impact
4. **Cost Governor** → Budget projection and decision

### Contract-Aligned Models

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

class AgentStatus(Enum):
    READY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unhealthy"
    UNKNOWN = "unknown"

class CostDecision(Enum):
    ALLOW = "allow"
    WARN = "warn"
    DENY = "deny"

@dataclass(frozen=True, slots=True)
class PriorityItem:
    title: str
    source: str
    routing_id: str
    reason_codes: list[str]

@dataclass(frozen=True, slots=True)
class CostProjection:
    projected_spend: float
    currency: str
    soft_cap: float
    hard_cap: float | None
    decision: CostDecision
    rationale: str
```

### Dependency Injection Protocol

```python
class HealthProbe(Protocol):
    def check(self, agent_id: str) -> tuple[AgentStatus, str]: ...

class EventStore(Protocol):
    def query(self, since: datetime, until: datetime) -> list[OvernightEvent]: ...

class PrioritySource(Protocol):
    def top_priorities(self, limit: int) -> list[PriorityItem]: ...

class CostGovernor(Protocol):
    def project(self, date: date) -> CostProjection: ...
```

### Service Implementation

```python
@dataclass
class BriefingService:
    health_probe: HealthProbe
    event_store: EventStore
    priority_source: PrioritySource
    cost_governor: CostGovernor
    agent_ids: list[str]
    priority_limit: int = 5

    def generate(self, target_date: date, wake_time: time) -> BriefingContent:
        # 1. Probe all agents
        agents = {
            aid: self.health_probe.check(aid)
            for aid in self.agent_ids
        }

        # 2. Query overnight events
        window_start = datetime.combine(target_date - timedelta(days=1), wake_time)
        window_end = datetime.combine(target_date, wake_time)
        events = self.event_store.query(window_start, window_end)

        # 3. Get priorities
        priorities = self.priority_source.top_priorities(self.priority_limit)

        # 4. Project costs
        cost = self.cost_governor.project(target_date)

        # 5. Build alerts
        alerts = self._build_alerts(agents, cost)

        return BriefingContent(
            date=target_date,
            agents=agents,
            events=events,
            priorities=priorities,
            cost=cost,
            alerts=alerts,
        )
```

### Scheduler Modes

| Mode | Flag | Behavior |
|------|------|----------|
| One-shot | `--force` | Generate immediately, exit |
| Daemon | `--daemon` | Run continuously, generate at scheduled time |
| Status | `--check` | Report scheduler status, exit |

### Time Calculation

```python
def calculate_trigger_time(wake_time: time, prep_minutes: int = 30) -> time:
    """Generate briefing prep_minutes before wake_time."""
    wake_dt = datetime.combine(date.today(), wake_time)
    trigger_dt = wake_dt - timedelta(minutes=prep_minutes)
    return trigger_dt.time()
```

### Testing Strategy

Use mock implementations of protocols for unit tests:

```python
class MockHealthProbe:
    def __init__(self, responses: dict[str, tuple[AgentStatus, str]]):
        self.responses = responses

    def check(self, agent_id: str) -> tuple[AgentStatus, str]:
        return self.responses.get(agent_id, (AgentStatus.UNKNOWN, "No mock"))
```

### Acceptance Tests

| Test ID | Scenario | Assertion |
|---------|----------|-----------|
| AT-1 | All agents healthy | No alerts, status table shows READY |
| AT-2 | Briefing generated | File exists at expected path |
| AT-3 | Budget exceeded | Cost decision is WARN or DENY |

### Output Format

```markdown
# Morning Briefing: YYYY-MM-DD

## Agent Status

| Agent | Status | Message |
|-------|--------|---------|
| claude-code | READY | Agent ready |

## Alerts

- Cost warning: Projected spend exceeds soft cap

## Today's Priorities

1. **Task title** (from: source)
   - Routing: `route-abc123`
   - Reasons: DEADLINE_SOON, HIGH_IMPACT

## Overnight Events

- [2026-02-08T03:15] PR #32 merged

## Cost Projection

**Projected:** USD 12.50 / **Soft cap:** USD 50.00
**Decision:** ALLOW
```

## Base120 References

- **DE3 (Functional Decomposition)**: Service broken into single-responsibility components
- **CO5 (Pipeline Composition)**: Sequential data flow through transforms
- **RE2 (Feedback Loops)**: Cost governor informs next day's projections
