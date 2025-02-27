from dataclasses import dataclass
import pandas as pd
import typing

@dataclass
class CalendarWeekView:
    week: int
    df: pd.DataFrame