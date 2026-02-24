from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    """
    Base class for fact extractors.
    All extractors must implement extract().
    """

    @abstractmethod
    async def extract(
        self,
        text: str,
        agent_id: str,
    ) -> list[dict]:
        """
        Extract facts from text.

        Returns list of dicts, each with keys:
          subject:    str   (e.g. "user")
          predicate:  FactRelation
          object_:    str   (e.g. "Python")
          confidence: float (0.0–1.0)

        Never raises. Returns [] on any error.
        """
        ...
