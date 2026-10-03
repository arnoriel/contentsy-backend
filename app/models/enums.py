from enum import StrEnum


class JobStatus(StrEnum):
    QUEUED = "queued"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    RENDERING = "rendering"
    DONE = "done"
    FAILED = "failed"


class AspectRatio(StrEnum):
    SQUARE = "1:1"
    LANDSCAPE_16_9 = "16:9"
    PORTRAIT_9_16 = "9:16"
    PORTRAIT_2_3 = "2:3"
    LANDSCAPE_3_2 = "3:2"


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]
