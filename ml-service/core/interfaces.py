from abc import ABC, abstractmethod
import pandas as pd

class BasePredictor(ABC):
    """
    Abstract contract for any machine learning predictor.
    """
    @abstractmethod
    def predict(self, state_vector: pd.DataFrame) -> float:
        """Takes a 1-row DataFrame representing the pitch state and returns a goal probability/value."""
        pass