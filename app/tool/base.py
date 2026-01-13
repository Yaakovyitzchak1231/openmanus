import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.utils.logger import logger


class ToolExample(BaseModel):
    """Represents an example usage of a tool.

    Adding examples to tools improves LLM accuracy by ~18% according to
    Anthropic's tool use documentation. Examples show the model concrete
    usage patterns and expected inputs/outputs.

    Attributes:
        description: What this example demonstrates
        parameters: Example input parameters as a dictionary
        expected_output: Optional expected result description
        notes: Additional guidance or caveats
    """

    description: str = Field(..., description="What this example demonstrates")
    parameters: Dict[str, Any] = Field(..., description="Example input parameters")
    expected_output: Optional[str] = Field(default=None, description="Expected result")
    notes: Optional[str] = Field(default=None, description="Additional guidance")


# class BaseTool(ABC, BaseModel):
#     name: str
#     description: str
#     parameters: Optional[dict] = None

#     class Config:
#         arbitrary_types_allowed = True

#     async def __call__(self, **kwargs) -> Any:
#         """Execute the tool with given parameters."""
#         return await self.execute(**kwargs)

#     @abstractmethod
#     async def execute(self, **kwargs) -> Any:
#         """Execute the tool with given parameters."""

#     def to_param(self) -> Dict:
#         """Convert tool to function call format."""
#         return {
#             "type": "function",
#             "function": {
#                 "name": self.name,
#                 "description": self.description,
#                 "parameters": self.parameters,
#             },
#         }


class ToolResult(BaseModel):
    """Represents the result of a tool execution."""

    output: Any = Field(default=None)
    error: Optional[str] = Field(default=None)
    base64_image: Optional[str] = Field(default=None)
    system: Optional[str] = Field(default=None)

    class Config:
        arbitrary_types_allowed = True

    def __bool__(self):
        return any(getattr(self, field) for field in self.__fields__)

    def __add__(self, other: "ToolResult"):
        def combine_fields(
            field: Optional[str], other_field: Optional[str], concatenate: bool = True
        ):
            if field and other_field:
                if concatenate:
                    return field + other_field
                raise ValueError("Cannot combine tool results")
            return field or other_field

        return ToolResult(
            output=combine_fields(self.output, other.output),
            error=combine_fields(self.error, other.error),
            base64_image=combine_fields(self.base64_image, other.base64_image, False),
            system=combine_fields(self.system, other.system),
        )

    def __str__(self):
        return f"Error: {self.error}" if self.error else self.output

    def replace(self, **kwargs):
        """Returns a new ToolResult with the given fields replaced."""
        # return self.copy(update=kwargs)
        return type(self)(**{**self.dict(), **kwargs})


class BaseTool(ABC, BaseModel):
    """Consolidated base class for all tools combining BaseModel and Tool functionality.

    Provides:
    - Pydantic model validation
    - Schema registration
    - Standardized result handling
    - Abstract execution interface

    Attributes:
        name (str): Tool name
        description (str): Tool description
        parameters (dict): Tool parameters schema
        _schemas (Dict[str, List[ToolSchema]]): Registered method schemas
    """

    name: str
    description: str
    parameters: Optional[dict] = None
    examples: Optional[List["ToolExample"]] = Field(
        default=None,
        description="Usage examples to improve LLM accuracy"
    )

    class Config:
        arbitrary_types_allowed = True
        underscore_attrs_are_private = False

    # def __init__(self, **data):
    #     """Initialize tool with model validation and schema registration."""
    #     super().__init__(**data)
    #     logger.debug(f"Initializing tool class: {self.__class__.__name__}")
    #     self._register_schemas()

    # def _register_schemas(self):
    #     """Register schemas from all decorated methods."""
    #     for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
    #         if hasattr(method, 'tool_schemas'):
    #             self._schemas[name] = method.tool_schemas
    #             logger.debug(f"Registered schemas for method '{name}' in {self.__class__.__name__}")

    async def __call__(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        return await self.execute(**kwargs)

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""

    def to_param(self) -> Dict:
        """Convert tool to function call format.

        Returns:
            Dictionary with tool metadata in OpenAI function calling format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self._description_with_examples(),
                "parameters": self.parameters,
            },
        }

    def _description_with_examples(self) -> str:
        """Generate description with embedded examples.

        Embeds usage examples directly into the tool description,
        which improves LLM tool accuracy by ~18%.

        Returns:
            Description string with examples appended if available
        """
        if not self.examples:
            return self.description

        examples_text = "\n\nExamples:"
        for i, ex in enumerate(self.examples, 1):
            examples_text += f"\n\n{i}. {ex.description}"
            examples_text += f"\n   Input: {json.dumps(ex.parameters)}"
            if ex.expected_output:
                examples_text += f"\n   Output: {ex.expected_output}"
            if ex.notes:
                examples_text += f"\n   Note: {ex.notes}"

        return self.description + examples_text

    # def get_schemas(self) -> Dict[str, List[ToolSchema]]:
    #     """Get all registered tool schemas.

    #     Returns:
    #         Dict mapping method names to their schema definitions
    #     """
    #     return self._schemas

    def success_response(self, data: Union[Dict[str, Any], str]) -> ToolResult:
        """Create a successful tool result.

        Args:
            data: Result data (dictionary or string)

        Returns:
            ToolResult with success=True and formatted output
        """
        if isinstance(data, str):
            text = data
        else:
            text = json.dumps(data, indent=2)
        logger.debug(f"Created success response for {self.__class__.__name__}")
        return ToolResult(output=text)

    def fail_response(self, msg: str) -> ToolResult:
        """Create a failed tool result.

        Args:
            msg: Error message describing the failure

        Returns:
            ToolResult with success=False and error message
        """
        logger.debug(f"Tool {self.__class__.__name__} returned failed result: {msg}")
        return ToolResult(error=msg)


class CLIResult(ToolResult):
    """A ToolResult that can be rendered as a CLI output."""


class ToolFailure(ToolResult):
    """A ToolResult that represents a failure."""
