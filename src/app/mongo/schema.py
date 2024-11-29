from typing import List, TypedDict, Optional, Dict
from datetime import datetime

class FundingRateAnalysis(TypedDict, total=False):
    period: datetime
    funding_rate_value: float
    analysis: Optional[Dict]