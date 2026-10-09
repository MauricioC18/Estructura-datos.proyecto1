from dataclasses import dataclass


@dataclass
class Event:
    time: int
    sequence: int
    event_type: str
    actor_id: str | None = None
    target_id: str | None = None
    cancelled: bool = False
