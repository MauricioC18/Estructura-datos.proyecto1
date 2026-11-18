from dataclasses import dataclass


@dataclass(frozen=True)
class KeyLocation:
    key_id: str
    room_id: int
    enemy_id: str | None = None

    @property
    def is_dropped_by_enemy(self):
        return self.enemy_id is not None
