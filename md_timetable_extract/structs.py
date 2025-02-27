from dataclasses import dataclass
import pandas as pd

@dataclass
class CalendarWeekView:
    week: int
    df: pd.DataFrame