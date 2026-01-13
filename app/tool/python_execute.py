import multiprocessing
import sys
from io import StringIO
from typing import Dict, List

from app.tool.base import BaseTool, ToolExample


class PythonExecute(BaseTool):
    """A tool for executing Python code with timeout and safety restrictions."""

    name: str = "python_execute"
    description: str = "Executes Python code string. Note: Only print outputs are visible, function return values are not captured. Use print statements to see results."
    parameters: dict = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python code to execute.",
            },
        },
        "required": ["code"],
    }
    examples: List[ToolExample] = [
        ToolExample(
            description="Calculate factorial using math library",
            parameters={"code": "import math\nprint(math.factorial(5))"},
            expected_output="120",
            notes="Use print() to see results"
        ),
        ToolExample(
            description="List comprehension for squares",
            parameters={"code": "print([x**2 for x in range(5)])"},
            expected_output="[0, 1, 4, 9, 16]"
        ),
        ToolExample(
            description="Read and count lines in a file",
            parameters={"code": "with open('data.txt') as f:\n    print(len(f.readlines()))"},
            expected_output="<number of lines>",
            notes="Useful for file analysis"
        ),
        ToolExample(
            description="JSON processing and pretty printing",
            parameters={"code": "import json\ndata = {'key': 'value', 'count': 42}\nprint(json.dumps(data, indent=2))"},
            expected_output='{\n  "key": "value",\n  "count": 42\n}'
        ),
        ToolExample(
            description="Data analysis with collections",
            parameters={"code": "from collections import Counter\nwords = ['a', 'b', 'a', 'c', 'a', 'b']\nprint(Counter(words).most_common(2))"},
            expected_output="[('a', 3), ('b', 2)]"
        )
    ]

    def _run_code(self, code: str, result_dict: dict, safe_globals: dict) -> None:
        original_stdout = sys.stdout
        try:
            output_buffer = StringIO()
            sys.stdout = output_buffer
            exec(code, safe_globals, safe_globals)
            result_dict["observation"] = output_buffer.getvalue()
            result_dict["success"] = True
        except Exception as e:
            result_dict["observation"] = str(e)
            result_dict["success"] = False
        finally:
            sys.stdout = original_stdout

    async def execute(
        self,
        code: str,
        timeout: int = 30,  # Increased from 5 to 30 for Daytona sandbox initialization
    ) -> Dict:
        """
        Executes the provided Python code with a timeout.

        Args:
            code (str): The Python code to execute.
            timeout (int): Execution timeout in seconds (default: 30).

        Returns:
            Dict: Contains 'output' with execution output or error message and 'success' status.
        """

        with multiprocessing.Manager() as manager:
            result = manager.dict({"observation": "", "success": False})
            if isinstance(__builtins__, dict):
                safe_globals = {"__builtins__": __builtins__}
            else:
                safe_globals = {"__builtins__": __builtins__.__dict__.copy()}
            proc = multiprocessing.Process(
                target=self._run_code, args=(code, result, safe_globals)
            )
            proc.start()
            proc.join(timeout)

            # timeout process
            if proc.is_alive():
                proc.terminate()
                proc.join(1)
                return {
                    "observation": f"Execution timeout after {timeout} seconds",
                    "success": False,
                }
            return dict(result)
