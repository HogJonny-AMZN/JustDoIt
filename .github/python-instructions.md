---
applyTo: python
---

# Python Coding Standards for Job Orchestrator

## Project Overview

**Job Orchestrator** is a distributed gRPC-based job execution system managing Maya and Houdini worker processes with priority queuing, dependency resolution, and external API integration for game engines and other clients.

**Current Status**: Phase 8+ Complete - Full system operational with external client integration.

## Core Principles

- **PEP 8 Compliance**: Follow PEP 8 with line length extended to 120 characters
- **Type Safety**: Use type hints for all function arguments and return values
- **Readability First**: Prioritize clear, maintainable code over clever solutions
- **Minimal Changes**: Write the least code necessary to solve the problem
- **Async-First**: Use `async def` for gRPC services and orchestrator operations

## Project Architecture

### Core Services
1. **OrchestratorServer** - Dual gRPC services (internal DCC worker communication + external client API)
2. **JobManager** - Priority queue with dependency resolution and status callbacks
3. **DCCPoolManager** - Auto-scaling worker pool (8 instances: 3+1 per DCC type)
4. **JobResultStore** - TTL-based result caching (1-hour default)

### Execution Modes
- **HEADLESS** - `mayapy.exe`/`hython.exe` (default, fastest startup)
- **GUI** - `maya.exe`/`houdini.exe` (only for viewport operations like playblast)

### External API Services
- `SubmitJob` - Submit jobs with priority, metadata, and dependencies
- `StreamJobStatus` - Real-time status updates via server streaming
- `GetJobResult` - Retrieve completed job results with timeout
- `CancelJob` - Cancel queued or running jobs
- `ListJobs` - Query jobs by submitter with status filters
- `GetPoolStatus` - Monitor DCC worker pool health and utilization

### Module Structure Standards

**Every Python module must include this header:**

```python
"""
Package: module.path.name
Brief one-line description.

Detailed description of module purpose and functionality.
"""

# Standard library imports
import asyncio
import logging as _logging
from pathlib import Path

# External imports
from PySide6.QtCore import Signal
import grpc.aio

# Project imports (absolute paths only)
from job_orchestrator.orchestrator.job import Job
from job_orchestrator.protos import orchestrator_pb2

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "module.path.name"  # Must match Package docstring
__updated__ = "YYYY-MM-DD HH:MM:SS"
__version__ = "X.Y.Z"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)  # Use _MODULE_NAME, NOT __name__
```

### Logging

- Import logging with alias: `import logging as _logging`
- Define module logger: `_LOGGER = _logging.getLogger(_MODULE_NAME)`
- Two-part error messages: human-readable context first, then technical details
- Configure logging in entry points, not in library modules
- Use debug level for execution flow tracking
- Use handlers with loglevel to determine what emits to console/file/etc

### gRPC and Protobuf Standards

**Service Implementation:**
```python
# Server implementation must inherit from generated servicer
class OrchestratorServer(
    orchestrator_pb2_grpc.OrchestratorServicer,
    orchestrator_pb2_grpc.ExternalJobAPIServicer,
    orchestrator_pb2_grpc.HealthCheckServicer,
):
    async def GetPoolStatus(self, request: orchestrator_pb2.PoolStatusRequest,
                           context: aio.ServicerContext) -> orchestrator_pb2.PoolStatusResponse:
        """Implement gRPC methods with proper type hints."""
```

**Client Usage:**
```python
# Use async context managers for channels
async with grpc.aio.insecure_channel('localhost:50051') as channel:
    stub = orchestrator_pb2_grpc.ExternalJobAPIStub(channel)
    response = await stub.GetPoolStatus(orchestrator_pb2.PoolStatusRequest())
```

**Worker RPC Pattern (Standardized Feb 2026):**
```python
# All workers use update_status() with explicit JobStatus enum
from job_orchestrator.protos import job_pb2

async def update_status(
    job_id: str,
    status: int,  # job_pb2.JobStatus enum value
    message: str,
    progress_percent: int = 0,
    metadata: dict[str, Any] | None = None,
    output_files: list[str] | None = None
) -> None:
    """Update job status via gRPC - standardized pattern."""
    update = orchestrator_pb2.JobStatusUpdate(
        job_id=job_id,
        status=status,  # Explicit: QUEUED/RUNNING/COMPLETED/FAILED
        message=message,
        progress_percent=progress_percent,
        metadata=metadata or {},
        output_files=output_files or [],
    )
    await stub.UpdateStatus(update)

# Example usage in worker execution
await update_status(job_id, job_pb2.JobStatus.RUNNING, "Executing script", 10)
# ... execute job ...
await update_status(job_id, job_pb2.JobStatus.COMPLETED, "Complete", 100,
                   metadata=result_metadata, output_files=actual_files)
```

**Protobuf Compilation:**
- **ALWAYS use `compile_protos.bat`** for protobuf changes (compiles AND fixes imports)
- Alternative: `make proto` (now uses compile_protos.bat internally)
- Never use manual `python -m grpc_tools.protoc` commands (causes import issues)
- Never modify generated `*_pb2.py` or `*_pb2_grpc.py` files directly
- Import generated files with: `from job_orchestrator.protos import orchestrator_pb2`

### Maya Coding Standards (ENFORCED)

**CRITICAL: Workers actively validate and reject PyMEL/MEL code.**

```python
# ✅ CORRECT - Use maya.cmds and OpenMaya 2.0
import maya.cmds as cmds
from maya.api import OpenMaya as om

sphere = cmds.polySphere(radius=5)[0]
cmds.move(0, 5, 0, sphere)

# ❌ FORBIDDEN - Will fail validation
import pymel.core as pm  # RuntimeError raised by workers
pm.polySphere()
maya.mel.eval("polySphere -r 5")  # MEL eval forbidden
```

**Rationale:** PyMEL is unmaintained. Workers enforce `maya.cmds` + `OpenMaya` only.

### Error Handling

- Catch specific exceptions, not generic `except:`
- Provide context in error messages
- Use appropriate error types for different situations
- Validate inputs early in functions

### Path Handling

- Use `pathlib.Path` for path manipulation, not string operations
- Standardize path formats (forward slashes) for cross-platform compatibility
- Validate paths before operations

### UI Development

- Separate UI code from business logic (MVC pattern)
- Use Qt Designer for layouts (`.ui` files)
- Connect signals to functions directly, not via string-based connections
- Never update UI from worker threads, use a signal bridge or similar mechanism

### Docstrings and Documentation

- Use compact reStructuredText (ReST) format for all docstrings
- Include :param:, :returns:, :raises: sections
- Use single-line descriptions when possible
- Prefer concise parameter descriptions over verbose explanations


## Module Structure

**CRITICAL:** All functions, classes, and executable code must come AFTER the module metadata section. Never place function definitions between imports and module metadata.

**Function/Class Separation:** Every top-level function and class definition must be preceded by a separator line:

```python
# -------------------------------------------------------------------------
```

This ensures clear visual separation and consistent structure across all modules.

Every Python module follows this template:

```python
"""
Package: job_orchestrator/module/path
Brief module description.

This module provides [core functionality description].
"""

import __logging

from typing import Any, Dict, List, Optional

# Third-party imports
import grpc
from PySide6.QtWidgets import QWidget

# Local imports
from job_orchestrator.orchestrator.job import Job
from job_orchestrator.protos import job_pb2

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "job_orchestrator.module.path"
__updated__ = "YYYY-MM-DD HH:MM:SS"
__version__ = "X.Y.Z"
__author__ = ["jGalloway"]
_LOGGER = __logging.getLogger(_MODULE_NAME)

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3


# -------------------------------------------------------------------------
# Classes and functions

class ExampleClass:
    """Example class following project conventions."""

    def __init__(self, name: str) -> None:
        """Initialize the class.

        :param name: The name identifier for this instance
        """
        self.name = name


# -------------------------------------------------------------------------
def example_function(param: str, optional: int = 0) -> bool:
    """Example function with type hints and docstring.

    :param param: Required string parameter
    :param optional: Optional integer parameter (default: 0)
    :returns: True if operation succeeded, False otherwise
    :raises ValueError: If param is empty
    """
    if not param:
        raise ValueError("param cannot be empty")
    return True
```

## Import Organization

Follow strict import hierarchy:

```python
# 1. Standard library (alphabetical)
import asyncio
import logging as _logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# 2. Third-party packages (alphabetical)
import grpc
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMainWindow

# 3. Local imports (alphabetical, grouped by subpackage)
from job_orchestrator.orchestrator.job import Job
from job_orchestrator.orchestrator.job_manager import JobManager
from job_orchestrator.protos import job_pb2, orchestrator_pb2_grpc
from job_orchestrator.utils.log_helpers import setup_logging
```

**Import Rules:**

- Never use wildcard imports (`from x import *`)
- One import per line for readability
- Group related imports together
- Use absolute imports: `from job_orchestrator.orchestrator.job import Job`
- Absolute imports with aliases if needed: `import job_orchestrator.orchestrator.job as orchestrator_job`
- Never import `job_orchestrator.protos` as `grpc` (use `job_orchestrator.protos`)

## Testing & Development Practices

### Test Structure
- All tests in `/tests/` directory with `test_*.py` naming
- Use `pytest` with async support: `pytest.mark.asyncio`
- Group tests by functional area (job lifecycle, external API, worker functionality)
- Mock external dependencies (file system, network calls, DCC processes)
- **Concurrent testing**: `test_concurrent_workers.py` - 4 tests for concurrent execution across all worker types
- **Load testing**: `test_load_stress.py` - 6 tests for queue depth, priority ordering, throughput, scaling
- **Worker standardization**: All workers use `update_status(job_id, status, message, progress_percent, metadata, output_files)` with explicit JobStatus enum

### Development Environment
```bash
# Environment setup
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate.bat on Windows
pip install -r requirements.txt

# Essential commands
make proto      # Compile protobuf files AND fix imports (uses compile_protos.bat)
compile_protos.bat  # Direct protobuf compilation with import fixing
make run        # Start orchestrator server (port 50051)
make test       # Run pytest suite
make check      # Ruff + mypy + tests
```

### Debug Tools
- `debug_pool_status.py` - Test gRPC pool status calls
- `debug_simple_health.py` - Validate health check service
- `test_monitor_simple.py` - UI testing for pool monitor
- Pool monitor: `python -m job_orchestrator.ui.pool_monitor`
- Server logs: `logs/job_orchestrator_YYYYMMDD_HHMMSS.log`

### Current Project Status (February 2026)
- **Phase 10 Complete**: Worker RPC standardization, concurrent testing, load testing
- **38 test modules** with 100+ individual tests (100% success rate)
- **Active Development**: Multi-job workflows, dependency cascades, C# client library

## Type Hints

### Required Type Annotations

All functions must have complete type hints:

```python
# Simple types
def get_job_status(job_id: str) -> str:
    return "COMPLETED"

# Optional parameters
def submit_job(script: str, priority: int = 5) -> str:
    return "job-123"

# Complex return types
def get_metadata() -> Dict[str, Any]:
    return {"version": "1.0", "count": 42}

# No return value
def log_message(msg: str) -> None:
    logger.info(msg)

# Async functions
async def execute_job(job: Job) -> bool:
    await asyncio.sleep(1)
    return True

# Protobuf types
def create_job_request(script: str) -> job_pb2.JobRequest:
    return job_pb2.JobRequest(script=script)

# gRPC streaming
async def stream_status(
    job_id: str
) -> AsyncIterator[job_pb2.JobUpdate]:
    yield job_pb2.JobUpdate(job_id=job_id)
```

### Complex Type Examples

```python
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple, Union
from pathlib import Path

# Collections
def get_jobs() -> List[Job]:
    return []

def get_parameters() -> Dict[str, Any]:
    return {"radius": 5.0, "name": "sphere"}

# Optional values
def find_job(job_id: str) -> Optional[Job]:
    return None  # or Job instance

# Union types
def get_result() -> Union[str, Dict[str, Any]]:
    return "success"  # or {"status": "ok"}

# Tuples with named elements
def validate_script(code: str) -> Tuple[bool, Optional[str]]:
    return True, None  # (is_valid, error_message)

# Callbacks
StatusCallback = Callable[[str, str], None]

def register_callback(callback: StatusCallback) -> None:
    callback("job-123", "RUNNING")

# Path handling
def load_config(path: Path) -> Dict[str, Any]:
    return {}

# Async iterators (for gRPC streaming)
async def stream_updates() -> AsyncIterator[job_pb2.JobUpdate]:
    yield job_pb2.JobUpdate()
```

## _logging Standards

### Logger Setup

```python
import logging as _logging

_LOGGER = _logging.getLogger(__name__)

# In entry points (main.py, servers), configure _logging:
from job_orchestrator.utils._logging import setup_logging

setup_logging(level="INFO", log_file="orchestrator.log")
```

### _logging Patterns

```python
# Debug: Execution flow tracking
_LOGGER.debug(f"Processing job {job_id} with priority {priority}")

# Info: Normal operations
_LOGGER.info(f"Job {job_id} completed in {duration:.2f}s")

# Warning: Recoverable issues
_LOGGER.warning(f"Job {job_id} missing optional output file: {path}")

# Error: Two-part messages (context + technical details)
_LOGGER.error(f"Failed to submit job: {str(e)}")
_LOGGER.error(f"Job validation failed: Script contains PyMEL imports")

# Exception: Include traceback
try:
    result = await execute_script(script)
except Exception as e:
    _LOGGER.exception(f"Script execution failed for job {job_id}")
    raise
```

**Logging Rules:**

- Use `_LOGGER.exception()` in except blocks to include traceback
- Include relevant context (job_id, client_id, etc.) in messages
- Don't log sensitive information (passwords, API keys)
- Use f-strings for formatting, not old-style `%` or `.format()`

## Exception Handling

### Exception Best Practices

```python
# Catch specific exceptions
try:
    job = await job_manager.get_job(job_id)
except KeyError:
    _LOGGER.error(f"Job not found: {job_id}")
    raise ValueError(f"Invalid job_id: {job_id}")

# Validate inputs early
def enqueue_job(job: Job) -> None:
    if job.priority < 0 or job.priority > 10:
        raise ValueError(f"Priority must be 0-10, got {job.priority}")
    if not job.script:
        raise ValueError("Job script cannot be empty")
    # Continue with operation...

# Provide context in error messages
try:
    with open(config_path) as f:
        config = json.load(f)
except FileNotFoundError:
    raise FileNotFoundError(
        f"Configuration file not found: {config_path}"
    )
except json.JSONDecodeError as e:
    raise ValueError(
        f"Invalid JSON in config file {config_path}: {e}"
    )

# Re-raise with context
try:
    result = await worker.execute_job(job)
except grpc.RpcError as e:
    _LOGGER.error(f"gRPC error executing job {job.job_id}: {e.code()}")
    raise RuntimeError(f"Worker communication failed: {e.details()}")

# Clean up resources in finally
channel = None
try:
    channel = grpc.aio.insecure_channel("localhost:50051")
    stub = orchestrator_pb2_grpc.OrchestratorStub(channel)
    result = await stub.SubmitJob(request)
finally:
    if channel:
        await channel.close()
```

### Common Exception Types

- `ValueError`: Invalid input values or parameters
- `KeyError`: Missing dictionary keys or job IDs
- `FileNotFoundError`: Missing configuration or script files
- `RuntimeError`: Unexpected runtime conditions
- `grpc.RpcError`: gRPC communication failures
- `asyncio.TimeoutError`: Operation timeouts

## Async Programming

### Async/Await Patterns

```python
# Async function definition
async def fetch_job_result(job_id: str) -> job_pb2.JobResult:
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = orchestrator_pb2_grpc.ExternalJobAPIStub(channel)
        result = await stub.GetJobResult(job_pb2.JobQuery(job_id=job_id))
        return result

# Concurrent execution
async def execute_multiple_jobs(jobs: List[Job]) -> List[bool]:
    tasks = [execute_job(job) for job in jobs]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# Async iteration (gRPC streaming)
async def monitor_job_status(job_id: str) -> None:
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = orchestrator_pb2_grpc.ExternalJobAPIStub(channel)
        async for update in stub.StreamJobStatus(job_pb2.JobQuery(job_id=job_id)):
            _LOGGER.info(f"Progress: {update.progress_percent}%")
            if update.status in ["COMPLETED", "FAILED"]:
                break

# Async context managers
async def process_with_lock(job: Job) -> None:
    async with job_lock:
        await job.execute()

# Timeouts
async def execute_with_timeout(job: Job) -> bool:
    try:
        result = await asyncio.wait_for(
            execute_job(job),
            timeout=300.0
        )
        return result
    except asyncio.TimeoutError:
        _LOGGER.error(f"Job {job.job_id} timed out after 300s")
        return False
# Concurrent execution (testing pattern)
async def test_concurrent_workers():
    """Test concurrent job execution across multiple worker types."""
    tasks = [
        submit_job("maya", script1),
        submit_job("houdini", script2),
        submit_job("python", script3),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    assert all(isinstance(r, str) for r in results)  # All return job_ids```

## Filesystem Operations

### Use pathlib.Path

```python
from pathlib import Path

# Create paths
config_dir = Path("job_orchestrator/config")
config_file = config_dir / "orchestrator_config.json"

# Validate existence
if not config_file.exists():
    raise FileNotFoundError(f"Config not found: {config_file}")

# Read/write files
with config_file.open("r") as f:
    data = json.load(f)

# Expand globs
output_dir = Path("C:/renders")
rendered_frames = list(output_dir.glob("frame_*.png"))

# Get absolute paths
absolute_path = config_file.resolve()

# Cross-platform paths (always forward slashes in code)
script_path = Path("scripts/render.py")  # Works on Windows/Linux
```

## Maya-Specific Guidelines

### CRITICAL: Avoid PyMEL and MEL

```python
# CORRECT: Use maya.cmds
import maya.cmds as cmds
from maya.api import OpenMaya as om

def create_sphere(radius: float, name: str) -> str:
    """Create a sphere using maya.cmds.

    :param radius: Sphere radius
    :param name: Object name
    :returns: Transform node name
    """
    sphere = cmds.polySphere(radius=radius, name=name)[0]
    cmds.move(0, radius, 0, sphere)
    return sphere

# FORBIDDEN: Never use PyMEL
import pymel.core as pm  # This will fail validation!
pm.polySphere()  # NEVER DO THIS

# FORBIDDEN: Never use MEL
import maya.mel
maya.mel.eval("polySphere -r 5")  # NEVER DO THIS
```

### Script Validation

```python
from job_orchestrator.utils.maya_utils import validate_maya_code

def validate_job_script(script: str) -> None:
    """Validate Maya script for forbidden patterns.

    :param script: The Maya Python script to validate
    :raises ValueError: If script contains PyMEL or MEL
    """
    is_valid, error = validate_maya_code(script)
    if not is_valid:
        raise ValueError(f"Invalid Maya script: {error}")
```

## Testing Patterns

### Unit Tests with pytest

```python
# tests/test_job_manager.py
import pytest
from job_orchestrator.orchestrator.job import Job
from job_orchestrator.orchestrator.job_manager import JobManager

@pytest.fixture
def job_manager():
    """Provide a fresh JobManager instance."""
    return JobManager()

@pytest.fixture
def sample_job():
    """Provide a sample job for testing."""
    return Job(
        job_type="maya",
        payload={"task": "render"},
        priority=5
    )

@pytest.mark.asyncio
async def test_enqueue_job(job_manager, sample_job):
    """Test job enqueue adds job to queue."""
    await job_manager.enqueue_job(sample_job)
    assert len(job_manager.job_queue) == 1

@pytest.mark.asyncio
async def test_dispatch_job_priority(job_manager):
    """Test jobs dispatch in priority order."""
    low_priority_job = Job(job_type="maya", payload={}, priority=3)
    high_priority_job = Job(job_type="maya", payload={}, priority=8)

    await job_manager.enqueue_job(low_priority_job)
    await job_manager.enqueue_job(high_priority_job)

    dispatched = await job_manager.dispatch_jobs("maya")
    assert dispatched.job_id == high_priority_job.job_id

def test_validate_maya_code_rejects_pymel():
    """Test Maya code validation rejects PyMEL."""
    from job_orchestrator.utils.maya_utils import validate_maya_code

    script = "import pymel.core as pm\npm.polySphere()"
    is_valid, error = validate_maya_code(script)

    assert not is_valid
    assert "PyMEL" in error

@pytest.mark.asyncio
async def test_concurrent_workers():
    """Test concurrent job execution across all worker types."""
    tasks = [
        submit_and_wait("maya", maya_script),
        submit_and_wait("houdini", houdini_script),
        submit_and_wait("python", python_script),
        submit_and_wait("bp_mayapy", bp_script),
    ]
    results = await asyncio.gather(*tasks)
    assert all(r.status == job_pb2.JobStatus.COMPLETED for r in results)

@pytest.mark.slow
@pytest.mark.asyncio
async def test_load_stress():
    """Test queue handling under load (50 jobs across 5 workers)."""
    jobs = [create_job_request(f"job_{i}") for i in range(50)]
    job_ids = await asyncio.gather(*[submit_job(j) for j in jobs])
    results = await asyncio.gather(*[wait_for_job(jid) for jid in job_ids])
    assert sum(1 for r in results if r.status == job_pb2.JobStatus.COMPLETED) >= 45
```

### Integration Tests

```python
# tests/test_integration_external_api.py
import pytest
import grpc
from job_orchestrator.protos import job_pb2, orchestrator_pb2_grpc

@pytest.mark.integration
@pytest.mark.asyncio
async def test_submit_and_retrieve_job():
    """Test full job submission and retrieval flow."""
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = orchestrator_pb2_grpc.ExternalJobAPIStub(channel)

        # Submit job
        request = job_pb2.JobRequest(
            job_type="maya",
            execution_mode="HEADLESS",
            script="import maya.cmds as cmds\nprint('test')",
            priority=5
        )
        response = await stub.SubmitJob(request)
        job_id = response.job_id

        # Retrieve result
        result = await stub.GetJobResult(job_pb2.JobQuery(job_id=job_id))
        assert result.status in ["COMPLETED", "RUNNING", "QUEUED"]
```

## UI Development (PySide6)

### Qt Signal/Slot Patterns

```python
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QMainWindow, QPushButton

class MainWindow(QMainWindow):
    """Main application window."""

    # Define signals
    job_submitted = Signal(str)  # Emits job_id

    def __init__(self):
        super().__init__()
        self.submit_button = QPushButton("Submit Job")

        # Connect signals to slots
        self.submit_button.clicked.connect(self.on_submit_clicked)
        self.job_submitted.connect(self.on_job_submitted)

    @Slot()
    def on_submit_clicked(self) -> None:
        """Handle submit button click."""
        job_id = self.submit_job()
        self.job_submitted.emit(job_id)

    @Slot(str)
    def on_job_submitted(self, job_id: str) -> None:
        """Handle job submission completion."""
        logger.info(f"Job submitted: {job_id}")
```

### Async Qt Integration (qasync)

```python
import asyncio
from qasync import QEventLoop, asyncSlot
from PySide6.QtWidgets import QApplication, QMainWindow

class AsyncMainWindow(QMainWindow):
    """Main window with async operations."""

    @asyncSlot()
    async def on_connect_clicked(self) -> None:
        """Connect to orchestrator (async operation)."""
        try:
            await self.client.connect()
            logger.info("Connected to orchestrator")
        except Exception as e:
            logger.error(f"Connection failed: {e}")

# Application entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = AsyncMainWindow()
    window.show()

    with loop:
        loop.run_forever()
```

## Anti-Patterns to Avoid

### Common Mistakes

```python
# WRONG: Mutable default argument
def add_job(jobs: List[Job] = []):  # BUG!
    jobs.append(job)

# CORRECT: Use None and create new list
def add_job(jobs: Optional[List[Job]] = None) -> List[Job]:
    if jobs is None:
        jobs = []
    jobs.append(job)
    return jobs

# WRONG: String concatenation in loops
result = ""
for item in items:
    result += item  # Inefficient!

# CORRECT: Use join
result = "".join(items)

# WRONG: Bare except
try:
    execute_job(job)
except:  # Catches too much!
    _LOGGER.error("Failed")

# CORRECT: Catch specific exceptions
try:
    execute_job(job)
except ValueError as e:
    _LOGGER.error(f"Invalid job: {e}")
except RuntimeError as e:
    _LOGGER.error(f"Execution failed: {e}")

# WRONG: Modifying list while iterating
for job in active_jobs:
    if job.is_complete():
        active_jobs.remove(job)  # BUG!

# CORRECT: Create new list or iterate over copy
active_jobs = [j for j in active_jobs if not j.is_complete()]
# OR
for job in active_jobs.copy():
    if job.is_complete():
        active_jobs.remove(job)
```

## Protobuf Conventions

### Working with Generated Code

```python
# Import generated modules
from job_orchestrator.protos import job_pb2, orchestrator_pb2_grpc

# Create protobuf messages
request = job_pb2.JobRequest(
    job_type="maya",
    execution_mode="HEADLESS",
    script="import maya.cmds as cmds",
    priority=5,
    parameters={"radius": 5.0},
    metadata={"project": "game_assets"}
)

# Access repeated fields (lists)
request.input_files.append("C:/scenes/input.ma")
request.output_files.extend(["C:/renders/frame_*.png"])

# Access map fields (dictionaries)
request.parameters["radius"] = 10.0
request.metadata["user"] = "artist_01"

# Convert to/from protobuf
job = Job.from_request(request)  # Custom class method
result = job.to_protobuf()  # Convert back to protobuf
```

### Enum Handling

```python
from job_orchestrator.protos import job_pb2

# Access enum values
status = job_pb2.JobStatus.RUNNING

# Convert to string
status_str = job_pb2.JobStatus.Name(status)  # "RUNNING"

# Convert from string
status_enum = job_pb2.JobStatus.Value("COMPLETED")

# Mapping between Python and protobuf enums
from job_orchestrator.orchestrator.job import JobStatus

def to_protobuf_status(status: JobStatus) -> int:
    """Convert Python enum to protobuf enum."""
    mapping = {
        JobStatus.QUEUED: job_pb2.JobStatus.QUEUED,
        JobStatus.RUNNING: job_pb2.JobStatus.RUNNING,
        JobStatus.COMPLETED: job_pb2.JobStatus.COMPLETED,
        JobStatus.FAILED: job_pb2.JobStatus.FAILED,
        JobStatus.CANCELLED: job_pb2.JobStatus.CANCELLED,
    }
    return mapping[status]
```

## Code Review Checklist

Before committing code, verify:

- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] _logging uses appropriate levels (debug/info/warning/error)
- [ ] Exceptions are specific, not bare `except:`
- [ ] No PyMEL or MEL in Maya code
- [ ] Paths use `pathlib.Path`, not string operations
- [ ] Async functions use `async def` and `await`
- [ ] UI updates only happen on main thread (Qt)
- [ ] No mutable default arguments
- [ ] Imports are organized (stdlib → third-party → local)
- [ ] Tests pass (`make test`)
- [ ] Code is formatted with Ruff (`make ruff-fix`)

## Documentation Examples

### Function Documentation

```python
async def submit_job(
    script: str,
    priority: int = 5,
    parameters: Optional[Dict[str, Any]] = None
) -> str:
    """Submit a job to the orchestrator.

    :param script: Python script to execute in DCC
    :param priority: Job priority (0-10, higher = more urgent)
    :param parameters: Optional script parameters for {param} substitution
    :returns: Job ID string
    :raises ValueError: If priority is out of range or script is empty
    :raises grpc.RpcError: If connection to orchestrator fails

    Example::

        job_id = await submit_job(
            script="import maya.cmds as cmds\\ncmds.polySphere()",
            priority=7,
            parameters={"radius": 5.0}
        )
    """
    if not script:
        raise ValueError("Script cannot be empty")
    if priority < 0 or priority > 10:
        raise ValueError(f"Priority must be 0-10, got {priority}")

    # Implementation...
    return job_id
```

### Class Documentation

```python
class JobManager:
    """Manages job queue and dispatching to workers.

    The JobManager maintains a priority queue of jobs and handles:
    - Job submission and queueing
    - Priority-based dispatching
    - Dependency resolution
    - Status callbacks for real-time updates

    Attributes:
        job_queue: Priority queue (heapq) of pending jobs
        active_jobs: Dictionary of currently running jobs
        completed_jobs: Set of completed job IDs
        failed_jobs: Set of failed job IDs

    Example:
        >>> manager = JobManager()
        >>> await manager.enqueue_job(job)
        >>> job = await manager.dispatch_jobs("maya", ExecutionMode.HEADLESS)
    """

    def __init__(self) -> None:
        """Initialize the job manager with empty queues."""
        self.job_queue: List[Tuple[int, int, Job]] = []
        self.active_jobs: Dict[str, Job] = {}
        self.completed_jobs: Set[str] = set()
        self.failed_jobs: Set[str] = set()
```

## Goals Summary

When writing code for Job Orchestrator:

1. **Follow project conventions** - Match existing patterns in the codebase
2. **Write idiomatic Python** - Clean, Pythonic solutions
3. **Prioritize readability** - Code is read more than written
4. **Minimize changes** - Don't refactor unnecessarily
5. **Write tests** - Unit tests for core logic, integration tests for workflows
6. **Document thoroughly** - Type hints, docstrings, and examples
7. **Handle errors gracefully** - Specific exceptions with context
8. **Use async correctly** - Await async calls, use asyncio patterns
9. **Validate Maya code** - Reject PyMEL and MEL automatically
10. **Log appropriately** - Debug for flow, error for failures
