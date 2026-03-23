# GitHub Copilot Instructions

**Last Updated:** February 17, 2026
**Status:** Active development - Phases 1-10 complete, MODULE MODE in production, **Main thread execution support COMPLETE**, **Worker RPC standardization COMPLETE**

---

## Quick Reference

**Repository:** HogJonny-AMZN/Job_Orchestrator (Git/GitHub)
**Python Version:** 3.11.9 (Maya 2026 compatible)
**Primary Dependencies:** gRPC, protobuf, PySide6, pytest
**Dev Environment:** Windows 10/11, PowerShell, venv (.venv)

**Key Entry Points:**
- Server: `job_orchestrator/main.py`
- System Tray UI: `job_orchestrator/ui/tray_app.py`
- Mock Editor: `mock_editor/main.py`
- Workers: `job_orchestrator/dcc_workers/{maya,houdini,python}/`

---

## System Architecture

**Job Orchestrator** is a distributed gRPC job execution system with data-driven worker registry supporting Maya, Houdini, Python, and extensible worker types.

**Core Data Flow:**
```
External Client → ExternalJobAPI (50051) → JobManager (priority queue)
                                          ↓
                                 DCCPoolManager (registry-driven pools)
                                          ↓
                             Workers poll via Orchestrator RPC
                                          ↓
                        Execute scripts with {param} substitution
                                          ↓
                    Stream progress → JobResultStore (1hr TTL)
```

**Critical Architecture Points:**
- **Data-driven worker registry**: Worker types configured in JSON, not hardcoded in Python
- **Dual gRPC services** on same server: `Orchestrator` (worker↔server) + `ExternalJobAPI` (client↔server)
- **Dual execution modes**: STRING MODE (inline scripts with `{param}` substitution) + MODULE MODE (importable Python modules)
- **Dual execution contexts**: Daemon thread (default, non-blocking) + Main thread (for BP APIs, selection operations)
- **Priority queue**: Higher numbers (0-10) = higher priority, uses Python `heapq` with negative values for max-heap
- **Flexible worker pools**: Pool sizes, executables, capabilities configured per worker type in `orchestrator_config.json`
- **Execution modes**: HEADLESS (default for most workers) vs GUI (viewport operations only)
- **Multi-job workflows**: Jobs can declare dependencies; system ensures dependency completion before dispatch
- **Extensibility**: Add new worker types (Blender, Nuke, etc.) via configuration only - no code changes required

## Essential Commands

```powershell
# REQUIRED after modifying *.proto files
make proto          # Uses compile_protos.bat - compiles AND fixes imports
compile_protos.bat  # Direct batch file (recommended for protobuf changes)

# Start orchestrator (spawns 8 worker instances)
make run     # Server on port 50051
make run-ui  # run the orchestrator and system tray app

# Development
make test       # pytest with asyncio support
make ruff-fix   # Auto-fix linting
make check      # Ruff + mypy + tests

# Example usage (requires running orchestrator)
python examples/submit_simple_job.py
python examples/maya_render_job.py

# Cleanup utilities (use when stuck with zombie processes)
python scripts/kill_orchestrator.py  # Kill all orchestrator processes safely
python scripts/kill_all_dcc.py       # Kill DCC workers only
python scripts/cleanup_tmp_logs.py   # Remove old logs (5+ days)
python scripts/diagnose_zombies.py   # Analyze zombie process issues
```

## Critical Code Patterns

### Dual-Mode Job Execution

**Two execution approaches:**

**STRING MODE (backward compatible):**
```python
# Job with inline script + parameter substitution
job = Job(
    job_type="maya",
    script="""
import maya.cmds as cmds
sphere = cmds.polySphere(radius={radius}, name="{name}")[0]
""",
    parameters={"radius": 5.0, "name": "mySphere"},
    execution_mode=ExecutionMode.HEADLESS
)
# Worker performs: script.replace("{radius}", "5.0") then exec(script)
```

**MODULE MODE (recommended for production):**
```python
# Job referencing importable Python module
job = Job(
    job_type="maya",
    module_path="job_orchestrator.jobs.examples.maya.generate_hero_sword",
    entry_point="main",  # Function name to call
    parameters={"sword_length": 120, "material": "steel"},
    execution_mode=ExecutionMode.HEADLESS,
    execute_on_main_thread=False  # Default: daemon thread execution
)
# Worker performs: importlib.import_module(module_path).main(parameters)
```

**When to use MODULE MODE:**
- ✅ Production asset pipelines with IDE support (autocomplete, type checking, refactoring)
- ✅ Reusable job templates requiring debugging
- ✅ Complex logic needing unit tests
- ✅ Team collaboration on job code

**When to use STRING MODE:**
- Quick one-off prototypes
- Dynamically generated code from external clients
- Simple parameter substitution tasks

### Execution Context: Main Thread vs Daemon Thread

**Phase 10 Addition:** Jobs can now execute on Maya's main thread for operations requiring specific threading context.

**Daemon Thread Execution (Default):**
```python
execute_on_main_thread=False  # Default for backwards compatibility
```
- ✅ Non-blocking RPC server
- ✅ Workers can poll while executing
- ✅ Standard Maya/Houdini operations
- ✅ All existing jobs work unchanged

**Main Thread Execution:**
```python
execute_on_main_thread=True  # BP jobs, selection operations
```
- ✅ Solves studio-specific API threading issues (BP_mPy)
- ✅ Eliminates nested `executeInMainThreadWithResult()` deadlocks
- ✅ Uses Maya's callable variant: `executeInMainThreadWithResult(func, params)`
- ⚠️ Blocks RPC server during execution (minimal impact)
- ⚠️ Job must handle own logging via `_job_log_file` parameter

**Implementation:**
```python
# RPC Server automatically handles both contexts
if execute_on_main_thread:
    # STRING MODE: maya.utils.executeInMainThreadWithResult(script)
    # MODULE MODE: maya.utils.executeInMainThreadWithResult(entry_func, parameters)
else:
    # STRING MODE: exec(script, execution_globals)
    # MODULE MODE: entry_func(parameters)
```

**When to use main thread:**
- BP_mPy operations (material assignment, export nodes)
- Maya selection-heavy operations
- Studio-specific APIs with threading restrictions
- Operations that previously required nested `executeInMainThreadWithResult()` calls

**Example BP Job:**
```python
request = job_pb2.JobRequest(
    dcc_type="bp_mayapy",
    module_path="job_orchestrator.jobs.examples.maya.bp_export_test_model",
    entry_point="main",
    execute_on_main_thread=True,  # BP operations require main thread
    parameters={"asset_name": "BP_Test_Export", ...}
)
```

### Job Lifecycle (`orchestrator/job.py`)

**Two creation paths:**
```python
# Internal (worker-initiated)
job = Job(
    job_type="maya",
    payload={"task": "render"},
    execution_mode=ExecutionMode.HEADLESS
)

# External (client-submitted via protobuf)
job = Job.from_request(request)  # Extracts 12 fields:
# priority, submitter, input_files, output_files, script,
# parameters, metadata, dependencies
```

**Key state transitions:**
```python
job.mark_started()              # QUEUED → RUNNING, records started_at
job.mark_completed(exec_time)   # → COMPLETED, sets progress=100%
job.mark_failed(error_msg)      # → FAILED, records error
job.update_progress(50, "msg")  # Update progress_percent + log
```

**Protobuf conversions:**
```python
job.to_protobuf()   # → job_pb2.Job (for worker dispatch)
job.to_result()     # → job_pb2.JobResult (for client retrieval)
job.to_update(msg)  # → job_pb2.JobUpdate (for streaming)
```

### Priority Queue (`orchestrator/job_manager.py`)

Uses **max-heap** by storing '-priority' (higher priority = more urgent):

```python
# Enqueue with priority
await job_manager.enqueue_job(job)
# Internally: heappush(queue, (-job.priority, counter, job))

# Dispatch matching job (respects dependencies)
job = await job_manager.dispatch_jobs(
    dcc_type="maya",
    execution_mode=ExecutionMode.HEADLESS
)  # Returns highest priority job where all dependencies in completed_jobs

# Status callbacks for streaming
job_manager.register_status_callback(job_id, async_callback)
# Triggers on: enqueue, mark_started, complete_job, fail_job, cancel_job
```

**Dependency enforcement:**
```python
# Job only dispatches if ALL dependencies in completed_jobs:
if all(dep in self.completed_jobs for dep in job.dependencies):
    job.status = JobStatus.RUNNING
    return job
```

### Worker Pool Management (`orchestrator/dcc_pool_manager.py`)

**Registry-driven architecture** - pools spawn based on worker_types configuration:

```python
# Startup (called by orchestrator.start())
await pool_manager.initialize_pools()
# Iterates worker_types registry:
#   maya: mayapy.exe ×3, maya.exe ×1
#   houdini: hython.exe ×3, houdini.exe ×1
#   python: python.exe ×4
# Pool sizes, executables, RPC servers all from orchestrator_config.json

# Worker registration (called by worker on startup)
await pool_manager.register_client(client_id, worker_type)
# Associates client_id with available instance
# worker_type can be any configured type: "maya", "houdini", "python", etc.

# Job dispatch (called by RequestJob RPC)
instance = await pool_manager.get_available_instance(worker_type, exec_mode)
# Returns instance where: not is_busy, matches exec_mode, client_id registered

await pool_manager.mark_instance_busy(instance_id, job_id)
# Sets is_busy=True, current_job_id=job_id

# Job completion (called by UpdateStatus RPC)
await pool_manager.mark_instance_free(instance_id)
# Sets is_busy=False, current_job_id=None
```

**Instance health checks:**
```python
# Process health: instance.process.poll() is None
# Registration: instance.client_id is not None
# Availability: not instance.is_busy
```

**Command building (registry-driven):**
```python
# OLD: Hardcoded if/elif branches for maya/houdini
if dcc_type == "maya":
    if execution_mode == ExecutionMode.HEADLESS:
        return [self.config.mayapy_executable, ...]

# NEW: Generic registry lookup
worker_config = self.config.get_worker_config(worker_type)
executable = worker_config.get_executable(execution_mode)
rpc_server = worker_config.get_rpc_server(execution_mode)
return [executable, str(rpc_server)]
```

### Dynamic Worker Type System

**CRITICAL:** Workers are **self-aware** via environment variables - no hardcoded types!

**How It Works:**
```python
# dcc_pool_manager.py - Orchestrator passes worker type to subprocess
env["JOB_ORCHESTRATOR_WORKER_TYPE"] = dcc_type  # e.g., "bp_mayapy", "maya", "houdini"
env["JOB_ORCHESTRATOR_INSTANCE_ID"] = instance_id
env["JOB_ORCHESTRATOR_HOST"] = "localhost"
env["JOB_ORCHESTRATOR_PORT"] = str(self.config.orchestrator_port)

# maya_rpc_server.py - Worker reads type from environment
def __init__(self, instance_id: str, orchestrator_host: str, orchestrator_port: int):
    self.worker_type = os.environ.get("JOB_ORCHESTRATOR_WORKER_TYPE", "maya")
    # Use in all RPC calls (RegisterClient, RequestJob)
    request = orchestrator_pb2.DCCClientInfo(
        client_id=self.instance_id,
        dcc_type=self.worker_type  # Dynamic!
    )
```

**Critical Environment Variables:**

| Variable | Purpose | Set By | Example |
|----------|---------|--------|---------|
| `JOB_ORCHESTRATOR_WORKER_TYPE` | Pool type for registration | dcc_pool_manager | `bp_mayapy` |
| `JOB_ORCHESTRATOR_INSTANCE_ID` | Unique worker instance ID | dcc_pool_manager | `e1611895` |
| `JOB_ORCHESTRATOR_HOST` | Orchestrator address | dcc_pool_manager | `localhost` |
| `JOB_ORCHESTRATOR_PORT` | Orchestrator gRPC port | dcc_pool_manager | `50051` |
| `JOB_ORCHESTRATOR_MODE` | Execution mode hint | environment config | `HEADLESS` or `AUTO_DETECT` |

**Benefits:**
- ✅ Multiple Maya variants: `maya`, `bp_mayapy`, `maya_r&d`, `maya_preview`
- ✅ Add worker types via JSON config only (no code changes)
- ✅ Workers correctly register with matching pool
- ✅ Flexible studio-specific configurations

**See:** [docs/development/BP_MAYA_WORKER_REGISTRATION_FIX.md](docs/development/BP_MAYA_WORKER_REGISTRATION_FIX.md)

### Script Execution `(`dcc_workers/maya_rpc_server.py`)`

Workers perform **parameter substitution** using `str.format()`:

```python
# Script template with placeholders
script = """
import maya.cmds as cmds
sphere = cmds.polySphere(radius={radius}, name="{name}")[0]
"""

# Worker substitutes parameters
parameters = {"radius": 5.0, "name": "mySphere"}
for param, value in parameters.items():
    script = script.replace("{" + param + "}", str(value))

# Result:
# sphere = cmds.polySphere(radius=5.0, name="mySphere")[0]
```

**Progress reporting milestones:**
```python
await update_progress(job_id, 0, "Starting")
# Validate input files...
await update_progress(job_id, 10, "Executing script")
# Execute code...
await update_progress(job_id, 80, "Collecting outputs")
# Expand glob patterns...
await update_progress(job_id, 100, "Complete")
```

**Output tracking (glob pattern expansion):**
```python
output_files = ["C:/renders/frame_*.png"]
# Worker expands using glob.glob():
actual_output_files = glob.glob("C:/renders/frame_*.png")
# Returns: ["C:/renders/frame_0001.png", "C:/renders/frame_0002.png", ...]
```

### External API Usage (`examples/submit_simple_job.py`)

**5 RPC methods:**
```python
async with grpc.aio.insecure_channel('localhost:50051') as channel:
    stub = orchestrator_pb2_grpc.ExternalJobAPIStub(channel)

    # 1. Submit job (returns immediately)
    response = await stub.SubmitJob(job_pb2.JobRequest(...))
    # Returns: job_id, queue_position

    # 2. Stream status updates (server streaming)
    async for update in stub.StreamJobStatus(job_pb2.JobQuery(job_id=...)):
        print(f"{update.progress_percent}% - {update.message}")
        if update.status in [COMPLETED, FAILED]:
            break

    # 3. Get result (blocks until complete or timeout)
    result = await stub.GetJobResult(job_pb2.JobQuery(job_id=...))
    # Returns: JobResult with outputs, metadata, execution_time

    # 4. Cancel job
    await stub.CancelJob(job_pb2.JobQuery(job_id=...))

    # 5. List jobs by submitter
    jobs = await stub.ListJobs(job_pb2.JobListQuery(submitter="..."))
```

## Maya Code Standards (ENFORCED)

**CRITICAL: Workers actively validate and reject PyMEL/MEL code.**

```python
# ✅ CORRECT - Use maya.cmds
import maya.cmds as cmds
from maya.api import OpenMaya as om

sphere = cmds.polySphere(radius=5)[0]
cmds.move(0, 5, 0, sphere)

# ❌ FORBIDDEN - Will fail validation
import pymel.core as pm  # RuntimeError: "PyMEL detected!"
pm.polySphere()

# ❌ FORBIDDEN - Will fail validation
maya.mel.eval("polySphere -r 5")
```

**Validation in `utils/maya_utils.py`:**
```python
def validate_maya_code(code: str) -> tuple[bool, str | None]:
    if "import pymel" in code.lower():
        return False, "Code contains PyMEL imports"
    if "maya.mel.eval" in code:
        return False, "Code uses MEL eval"
    return True, None
```

**Rationale:** PyMEL is unmaintained. Workers enforce `maya.cmds` + `OpenMaya` only.

## Maya Batch Mode Best Practices (CRITICAL)

**IMPORTANT: Maya's command engine behaves differently in headless/batch mode (mayapy.exe) vs GUI mode.**

### Common Pitfall: `cmds.select()` Errors

**Symptom:**
```python
cmds.select(clear=True)  # Works in Maya GUI
# ERROR in mayapy: "Flag 'clear' must be passed a boolean argument"
```

**Root Cause:**
- Maya's command parser has quirks in standalone execution contexts
- Selection operations can fail with nonsensical type errors
- Errors appear inconsistent, especially in multi-job workflows
- See: https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=GUID-9B5AECBB-B212-4C92-959A-22599760E91A

### Solutions:

**1. Avoid Selection Entirely (Preferred)**
```python
# ❌ BAD - Uses selection (fragile in batch mode)
cmds.select(objects, replace=True)
cmds.hyperShade(assign=shadingGroup)
cmds.select(clear=True)  # May fail!

# ✅ GOOD - Direct assignment (robust)
cmds.sets(objects, edit=True, forceElement=shadingGroup)
```

**2. When Selection Required (e.g., FBX export)**
```python
# ✅ Select for export, but DON'T clear selection after
cmds.select(transforms, replace=True)
cmds.file("output.fbx", force=True, type="FBX export", es=True)
# No clear needed - lingering selection harmless in batch mode
```

**3. Alternative: Use MEL-style Integer Flags (Last Resort)**
```python
# If you MUST clear selection:
cmds.select(all=False)  # Sometimes more stable than clear=True
# Or skip entirely if possible
```

### Troubleshooting Maya Batch Errors

**If you see "Flag 'X' must be passed a boolean argument":**

1. **Check if selection is needed** - Most operations have direct alternatives
2. **Review command syntax** - Use `cmds.help("commandName")` in Maya GUI
3. **Test in mayapy directly** - Run script via `mayapy.exe script.py` to isolate issue
4. **Avoid clearing selection** - Rarely needed in headless execution
5. **Use sets/connections directly** - Bypass selection-dependent commands

**Example Refactoring:**
```python
# Before (fragile):
cmds.select(obj)
cmds.hyperShade(assign="myShader")  # Assigns to selected

# After (robust):
cmds.sets(obj, edit=True, forceElement="myShaderSG")  # Direct assignment
```

### Key Takeaway:
**Treat `cmds.select()` as unreliable in mayapy batch scripts. Always prefer direct object manipulation.**

## Execution Mode Selection

**When to use each mode:**

- **HEADLESS** (default): `mayapy.exe` / `hython.exe`
  - Fastest startup, lowest memory
  - All non-viewport operations
  - Scene manipulation, file I/O, simulations, renders (Arnold/Redshift)

- **GUI**: `maya.exe` / `houdini.exe`
  - **ONLY** for viewport operations:
    - `cmds.playblast()` - viewport preview rendering
    - Viewport screenshots
    - Interactive OpenGL rendering
  - **Do NOT use for:** batch rendering, file operations, data processing

```python
# Correct usage
job = Job(
    job_type="maya",
    execution_mode=ExecutionMode.HEADLESS,  # Default for most tasks
    script="cmds.arnoldRender(...)"
)

job = Job(
    job_type="maya",
    execution_mode=ExecutionMode.GUI,  # Only for tasks needing viewport
    script="cmds.playblast(format='avi', ...)"
)
```

## Configuration Files

### `job_orchestrator/config/orchestrator_config.json` (Worker Registry)

**Data-driven worker configuration** - add new worker types without code changes:

```json
{
  "worker_types": {
    "maya": {
      "display_name": "Autodesk Maya",
      "description": "Maya DCC for 3D modeling, animation, and rendering",
      "capabilities": {
        "supports_gui": true,
        "supports_headless": true,
        "supports_module_mode": true,
        "supports_string_mode": true
      },
      "executable_paths": {
        "headless": "${MAYA_LOCATION}/bin/mayapy.exe",
        "gui": "${MAYA_LOCATION}/bin/maya.exe"
      },
      "rpc_servers": {
        "headless": "dcc_workers/maya/maya_rpc_server.py",
        "gui": "dcc_workers/maya/maya_gui_server.py"
      },
      "environment_profile": "maya_2026",
      "pool_sizes": {
        "headless": 3,
        "gui": 1
      },
      "validation": {
        "enabled": true,
        "rules": ["no_pymel", "no_mel"]
      },
      "boot_timeout": {
        "headless": 60,
        "gui": 120
      }
    },
    "python": {
      "display_name": "Python Worker (Workspace venv)",
      "description": "Generic Python worker for mesh processing, ML inference, data transformation",
      "capabilities": {
        "supports_gui": false,
        "supports_headless": true,
        "supports_module_mode": true,
        "supports_string_mode": true
      },
      "executable_paths": {
        "headless": "${WORKSPACE_ROOT}/.venv/Scripts/python.exe"
      },
      "rpc_servers": {
        "headless": "dcc_workers/python/python_rpc_server.py"
      },
      "environment_profile": "python_workspace_venv",
      "pool_sizes": {
        "headless": 4
      },
      "boot_timeout": {
        "headless": 10
      }
    }
  },
  "scaling": {
    "max_instances_per_type": 10,
    "enable_auto_scaling": false
  },
  "orchestrator": {
    "port": 50051,
    "log_level": "INFO"
  },
  "log_retention": {
    "enabled": true,
    "max_age_days": 5,
    "max_logs_per_instance": 3,
    "max_total_size_mb": 200
  }
}
```

### `job_orchestrator/config/dcc_paths.json` (Path Resolution)

**Variable expansion source** for `${MAYA_LOCATION}`, `${HOUDINI_LOCATION}`, etc.:

```json
{
  "maya": {
    "mayapy": "C:\\Program Files\\Autodesk\\Maya2026\\bin\\mayapy.exe",
    "executable": "C:\\Program Files\\Autodesk\\Maya2026\\bin\\maya.exe",
    "version": "2026"
  },
  "houdini": {
    "hython": "C:\\Program Files\\Side Effects Software\\Houdini 20.5\\bin\\hython.exe",
    "executable": "C:\\Program Files\\Side Effects Software\\Houdini 20.5\\bin\\houdini.exe",
    "version": "20.5.512"
  }
}
```

**Path resolution** (`config.py`):
- `${MAYA_LOCATION}` → `C:\Program Files\Autodesk\Maya2026`
- `${HOUDINI_LOCATION}` → `C:\Program Files\Side Effects Software\Houdini 20.5`
- `${WORKSPACE_ROOT}` → Workspace root directory path

### Environment Configuration (`job_orchestrator/config/`)
- **`base_env.json`** - Common environment variables for all workers
- **`maya_env.json`** - Maya-specific environment (MAYA_SCRIPT_PATH, PYTHONPATH, etc.)
- **`houdini_env.json`** - Houdini-specific environment (HOUDINI_PATH, etc.)
- **`python_env.json`** - Python worker environment (PYTHONPATH, orchestrator settings)
- **`env_profiles.json`** - Named profile mappings and version detection

**Environment features:**
- Profile-based environment loading with inheritance (`base_profile` references)
- Variable expansion with `${VAR}` syntax and recursive substitution
- PATH/PYTHONPATH list handling with prepend/append operations
- Version-aware profiles (auto-detects Maya 2026, Houdini 21, etc.)
- Worker type → environment profile mapping (e.g., `maya_2026_headless` → `maya_env.json`)

**Environment profile flow:**
```
Worker Config: "environment_profile": "maya_2026"
        ↓
Environment Manager: Appends execution mode → "maya_2026_headless"
        ↓
env_profiles.json: "maya_2026_headless" → {"config_file": "maya_env.json"}
        ↓
Load and expand maya_env.json variables for subprocess
```

## Adding New Worker Types

**To add a new worker type (e.g., Blender, Nuke, custom Python env):**

1. **Add worker config** to `orchestrator_config.json`:
```json
"blender": {
  "display_name": "Blender",
  "description": "Blender for modeling and rendering",
  "capabilities": {
    "supports_gui": true,
    "supports_headless": true,
    "supports_module_mode": true,
    "supports_string_mode": true
  },
  "executable_paths": {
    "headless": "${BLENDER_LOCATION}/blender.exe",
    "gui": "${BLENDER_LOCATION}/blender.exe"
  },
  "rpc_servers": {
    "headless": "dcc_workers/blender/blender_rpc_server.py"
  },
  "environment_profile": "blender_4_0",
  "pool_sizes": {"headless": 2},
  "boot_timeout": {"headless": 30}
}
```

2. **Add path resolution** to `dcc_paths.json`:
```json
"blender": {
  "executable": "C:\\Program Files\\Blender Foundation\\Blender 4.0\\blender.exe",
  "version": "4.0"
}
```

3. **Create RPC server** (`dcc_workers/blender/blender_rpc_server.py`):
   - Copy existing worker (Maya/Houdini/Python)
   - Update imports and DCC-specific execution logic
   - Register with `dcc_type="blender"`

4. **Create environment profile** (`config/blender_env.json`):
```json
{
  "description": "Blender environment configuration",
  "variables": {
    "BLENDER_USER_SCRIPTS": {"value": "${WORKSPACE_ROOT}/blender_scripts"},
    "PYTHONPATH": {"value": ["${WORKSPACE_ROOT}"], "mode": "prepend"}
  }
}
```

5. **Add profile mapping** to `env_profiles.json`:
```json
"blender_4_0_headless": {
  "config_file": "blender_env.json",
  "description": "Blender 4.0 headless mode"
}
```

**That's it!** No Python code changes needed. The orchestrator will:
- Spawn workers from the registry
- Build commands using configured executables/RPC servers
- Load environment from profiles
- Dispatch jobs to available instances

**Code reduction achieved:**
- **Before**: ~400 lines of hardcoded DCC-specific logic
- **After**: ~15 lines of JSON configuration per worker type
- **Adding new worker**: 15 minutes (config) vs 8 hours (code changes + testing)

## Workspace Paths & Constants (`job_orchestrator/globals.py`)

**Centralized path management pattern** - all workspace paths defined in `job_orchestrator/globals.py`:

```python
from job_orchestrator.globals import (
    WORKSPACE_ROOT,  # Job_Orchestrator/ directory
    TEMP_DIR,        # .temp/ for temporary files
    LOGS_DIR,        # .temp/logs/ for all logs
    CONFIG_DIR,      # job_orchestrator/config/
    JOBS_DIR,        # job_orchestrator/jobs/ (MODULE MODE jobs)
    LOG_FORMAT,      # Standard log format
    get_temp_subdir  # Helper for creating temp subdirectories
)
```

**Key patterns:**
```python
# Use get_temp_subdir() for temp files
from job_orchestrator.globals import get_temp_subdir

meshes_dir = get_temp_subdir("meshes")  # Creates .temp/meshes/
output_path = meshes_dir / "my_sphere.obj"

# Standard log format (always use this)
import logging
handler = logging.FileHandler("mylog.log")
handler.setFormatter(logging.Formatter(LOG_FORMAT))
# Format: "timestamp :: [LEVEL][module.name] >> message :(file:line)"
```

**Why this matters:**
- Ensures consistent path resolution across all modules
- Makes refactoring paths trivial (change once in globals.py)
- Automatic directory creation with `get_temp_subdir()`
- Single source of truth for workspace layout

## Project Structure

Key directories and their purposes:
```
/job_orchestrator/
  ├── .github/
  │     ├── copilot-instructions.md      # This file - comprehensive system guide
  │     └── python-instructions.md       # Python coding standards and patterns
  ├── config/
  │     ├── orchestrator_config.json     # Main config (pools, ports, timeouts, log retention)
  │     ├── dcc_paths.json               # DCC executable paths
  │     ├── base_env.json                # Common environment variables
  │     ├── maya_env.json                # Maya-specific environment
  │     ├── houdini_env.json             # Houdini-specific environment
  │     └── env_profiles.json            # Named environment profiles
  ├── docs/                              # All documentation organized here
  │     ├── development/                 # Phase completions & dev notes
  │     │     ├── PHASE1_COMPLETE.md
  │     │     ├── PHASE2_3_COMPLETE.md
  │     │     ├── PHASE6_SUMMARY.md
  │     │     ├── IMPLEMENTATION_STATUS.md
  │     │     ├── LOG_CONSOLIDATION_MIGRATION.md
  │     │     └── WHATS_NEXT.md
  │     ├── setup/                       # Installation & config guides
  │     │     ├── SETUP.md
  │     │     ├── VENV_SETUP.md
  │     │     └── CONFIG_MIGRATION.md
  │     ├── design/                      # Architecture & design docs
  │     │     ├── PROJECT_STRUCTURE.md
  │     │     ├── LEVEL_EDITOR_INTEGRATION_DESIGN.md
  │     │     └── IMPROVEMENTS.md
  │     ├── status/                      # Project tracking
  │     │     └── PROJECT_STATUS.md
  │     └── CLEANUP_SUMMARY.md
  ├── dcc_workers/
  │     ├── maya/
  │     │     ├── maya_rpc_server.py       # ✅ v4.0.0 - Dual-mode execution
  │     │     └── maya_gui_server.py       # ✅ v4.0.0 - GUI mode support
  │     ├── houdini/
  │     │     └── houdini_rpc_server.py    # ✅ v2.0.0 - Dual-mode execution
  │     └── python/
  │           └── python_rpc_server.py     # ✅ v1.0.0 - Generic Python worker
  ├── examples/                            # ✅ Complete Python client examples
  │     ├── submit_simple_job.py           # Basic job submission
  │     ├── maya_render_job.py             # Production rendering
  │     ├── houdini_sim_job.py             # Simulation workflows
  │     ├── batch_jobs.py                  # Multi-job management
  │     ├── job_workflow_example.py        # Complex dependencies
  │     └── README.md                      # Comprehensive examples guide
  ├── jobs/                                # ✅ MODULE MODE job templates
  │     ├── examples/
  │     │     ├── maya/
  │     │     │     ├── generate_hero_sword.py      # Asset generation example
  │     │     │     ├── generate_enemy_shield.py    # Shield asset module
  │     │     │     └── generate_prop_crate.py      # Reusable prop module
  │     │     └── houdini/
  │     │           ├── generate_procedural_rock.py # Procedural geometry
  │     │           └── export_particle_cache.py    # Particle simulation
  │     └── README.md                      # MODULE MODE development guide
  ├── mock_editor/                         # ✅ Complete PySide6 demo integration
  │     ├── main.py                        # Entry point with auto-orchestrator start
  │     ├── client/orchestrator_client.py  # gRPC client wrapper
  │     ├── ui/main_window.py              # Job submission UI
  │     └── README.md                      # Setup and usage guide
  ├── protos/
  │     ├── job.proto                      # ✅ Extended with External API
  │     ├── dcc.proto
  │     └── orchestrator.proto             # ✅ Extended with External API
  ├── orchestrator/
  │     ├── config.py                      # ✅ WorkerTypeConfig + OrchestratorConfig (registry-driven)
  │     ├── job.py                         # ✅ Extended with 20+ fields (dual-mode support)
  │     ├── job_manager.py                 # ✅ Priority queue, callbacks, dependencies
  │     ├── job_result_store.py            # ✅ TTL cache for results
  │     ├── dcc_pool_manager.py            # ✅ Registry-driven pool management
  │     ├── environment_manager.py         # ✅ Environment profiles & variable expansion
  │     └── orchestrator_server.py         # ✅ Dual service (internal + external)
  ├── scripts/                             # Utility scripts
  │     ├── kill_orchestrator.py           # Safe orchestrator process cleanup
  │     ├── kill_all_dcc.py                # DCC worker cleanup
  │     ├── cleanup_tmp_logs.py            # Log retention management
  │     ├── diagnose_zombies.py            # Zombie process analysis
  │     ├── check_boot_status.py           # Worker boot status check
  │     └── vendor_dependencies.py         # Vendor gRPC dependencies
  ├── ui/
  │     ├── pool_monitor.py                # ✅ Real-time DCC pool monitoring UI
  │     └── tray_app.py                    # ✅ System tray with orchestrator integration
  ├── tests/                               # All tests organized here
  │     ├── __init__.py
  │     ├── conftest.py
  │     ├── test_job.py
  │     ├── test_job_manager.py
  │     ├── test_environment_manager.py    # ✅ Environment config tests
  │     ├── test_phase3_result_store.py
  │     ├── test_phase4_job_manager.py
  │     ├── test_phase5_external_api.py
  │     └── test_phase6_worker_enhancements.py
  ├── utils/
  │     ├── logging.py
  │     └── maya_utils.py
  ├── .temp/                               # ✅ Temporary files and logs
  │     └── logs/                          # All log files (5-day retention)
  ├── main.py
  ├── Makefile
  ├── README.md
  ├── requirements.txt
  └── pyproject.toml
```

---

## Non-ASCII Characters & Emoji Policy

To avoid platform-specific parsing and encoding issues (notably on Windows PowerShell 5.1), this repository enforces a conservative policy for executable scripts and bootstrap files.

- **Rule:** Do **not** include emoji or other non-ASCII characters in executable scripts or bootstrap files such as `*.ps1`, `*.bat`, `*.sh`, or files that are executed by DCC processes at startup (for example `userSetup.py`, `456.py`, `maya_standalone_init.py`).
- **Allowed:** Documentation, README files, and non-executable markdown or design documents may include emoji or non-ASCII characters.

Why this exists:
- PowerShell 5.1 and some Windows terminals can fail parsing scripts that contain non-ASCII characters unless the file is saved with an appropriate BOM or a compatible code page, causing errors such as "The string is missing the terminator".
- Non-ASCII characters embedded in scripts can also mask hidden encoding problems that produce runtime crashes in DCC processes (example: Qt/PySide binary conflicts from multiple Python runtimes).

Guidance:
- Prefer plain ASCII in any file that may be executed by automated tooling or by DCCs at startup.
- If you absolutely must include emoji inside a script (rare): save the file as **UTF-8 WITH BOM** and *ensure* target systems run PowerShell 7+ (or otherwise accept UTF-8 without error).
- Use `README.md` or other user-facing docs for decorative emoji, not bootstrap scripts.

Automated checks:
- A lightweight detection script is provided at `scripts/check_nonascii.py` and a GitHub Actions workflow `.github/workflows/check-nonascii.yml` is included to run on push/pull requests and fail when non-ASCII characters are present in executable scripts.
- A sample local git hook is provided at `.githooks/pre-commit` (POSIX shell) and `.githooks/pre-commit.ps1` (PowerShell). To enable local hooks, run:

```
git config core.hooksPath .githooks
```

Please update files to conform before committing; CI will block changes that introduce non-ASCII into executable scripts.

---

## Logging & Process Management

### Log Location & Retention

**All logs are centralized in `.temp/logs/` with automatic cleanup:**

```
.temp/logs/
  ├── orchestrator_{timestamp}.log          # Main orchestrator process
  ├── mock_editor_{timestamp}.log           # Mock editor application
  ├── maya_headless_{id}_pid{pid}.log       # Maya workers
  ├── maya_gui_{id}_pid{pid}.log
  ├── houdini_headless_{id}_pid{pid}.log    # Houdini workers
  └── houdini_gui_{id}_pid{pid}.log
```

**Retention Policy (orchestrator_config.json):**
- Default: 5 days (`max_age_days`)
- Max logs per instance: 3 (`max_logs_per_instance`)
- Max total size: 200 MB (`max_total_size_mb`)
- Crashed instance logs: Not preserved by default (`preserve_crashed: false`)

**Cleanup happens automatically on orchestrator startup** via `log_manager.cleanup_on_startup()`.

### Process Cleanup Utilities

**Safe termination scripts (see `/scripts/`):**

```powershell
# Kill all orchestrator processes (server, tray, pool monitor)
python scripts/kill_orchestrator.py
# Safety: Only kills processes from THIS workspace using path matching
# Protects: VS Code extensions, debuggers, other Python tools

# Kill DCC workers only (Maya, Houdini instances)
python scripts/kill_all_dcc.py

# Remove old logs (5+ days)
python scripts/cleanup_tmp_logs.py

# Diagnose zombie process issues
python scripts/diagnose_zombies.py
```

**Zombie Prevention:**
- Boot timeout enforced: 120 seconds (configurable in `orchestrator_config.json`)
- Process health tracking via `instance.process.poll()`
- Graceful shutdown with `terminate()` → `wait(3s)` → `kill()` fallback
- See `kill_orchestrator.py` for workspace-safe process matching patterns

---

## UI Development & Mock Editor Integration

### Mock Editor (`/mock_editor/`)

**Complete PySide6 integration demonstrating:**
- Auto-start orchestrator detection and launch
- gRPC client wrapper (`OrchestratorClient`) with async job submission
- Real-time job monitoring and status updates
- Multi-platform launcher scripts (`.bat` and `.ps1`)

**Architecture:**
```python
# main.py - Entry point with orchestrator auto-start
async def ensure_orchestrator_running() -> bool:
    """Check if orchestrator is available, start if needed."""

# client/orchestrator_client.py - gRPC wrapper
class OrchestratorClient:
    async def submit_job(self, job_request: dict) -> str:
        """Submit job and return job_id."""

    async def stream_job_status(self, job_id: str):
        """Stream real-time job status updates."""

# ui/main_window.py - Job submission interface
class MainWindow(QMainWindow):
    """Game editor UI with job submission panel."""
```

### Pool Monitor UI (`/job_orchestrator/ui/pool_monitor.py`)

**Real-time DCC pool monitoring:**
- Live worker instance status (BOOTING, READY, BUSY, CRASHED)
- Performance metrics (CPU, memory usage per instance)
- Health tracking and crash detection
- Refresh controls (manual + auto-refresh)

**System Tray Integration (`/job_orchestrator/ui/tray_app.py`):**
- Background orchestrator status monitoring
- Quick access to pool monitor window
- Graceful shutdown controls

### UI Development Standards

**PySide6 Requirements:**
```python
# Use modern PySide6 patterns
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PySide6.QtCore import QTimer, Signal
import qasync  # For async Qt integration

class PoolMonitorWindow(QMainWindow):
    # Use signals for thread-safe UI updates
    data_received = Signal(dict)

    def __init__(self):
        super().__init__()
        # Connect signals before starting background tasks
        self.data_received.connect(self.update_table)
```

**Async Qt Integration:**
- Use `qasync` for asyncio event loop integration
- Never update UI from worker threads - use signals
- Implement proper cleanup in `closeEvent()`
- Use `QTimer` for periodic updates with proper stop/start logic

---

## Best Practices Copilot Should Enforce

- Use `async def` for gRPC service methods and orchestrator routines.
- Wrap subprocess calls managing Maya/Houdini in async coroutines.
- **NEVER use `print()` statements - always use `_LOGGER` instead.**
  - Import logging: `import logging as _logging`
  - Define explicit module name: `_MODULE_NAME = "module.path.name"`
  - Create logger with explicit name: `_LOGGER = _logging.getLogger(_MODULE_NAME)` (NOT `__name__`)
  - Use appropriate levels: `_LOGGER.info()`, `_LOGGER.error()`, `_LOGGER.warning()`, `_LOGGER.debug()`
  - Use f-strings for readability: `_LOGGER.info(f"Processing {item}")`
- Prefer structured logs with timestamps and severity.
- Maintain strict typing: `Mypy` clean type safety.
- **Follow module structure standards** (see "Python Module Structure Standards" section above)
- **Use project cleanup scripts** instead of manual process killing (see "Logging & Process Management")
- **Worker RPC standardization**: All workers use `update_status(job_id, status, message, progress_percent, metadata, output_files)` with explicit status parameter (QUEUED/RUNNING/COMPLETED/FAILED)

---

## Implementation Status

### ✅ Completed Features (Phases 1-10)

**Phase 1-3: Core Infrastructure**
- JSON configuration system (`orchestrator_config.json`, `dcc_paths.json`)
- Job execution modes (HEADLESS/GUI) with `ExecutionMode` enum
- DCC Pool Manager with instance lifecycle management
- Protobuf schemas extended for internal and external APIs

**Phase 4-5: External Job Submission API**
- Priority queue system (0-10 scale, higher = more urgent)
- Job Result Store with TTL caching (1-hour default)
- Status callbacks for real-time streaming
- 5 External API RPC methods:
  - `SubmitJob` - Submit jobs with priority and metadata
  - `StreamJobStatus` - Real-time status updates via server streaming
  - `GetJobResult` - Retrieve completed job results
  - `CancelJob` - Cancel queued or running jobs
  - `ListJobs` - Query jobs by submitter with filters

**Phase 6: Worker Enhancements**
- Script execution with parameter substitution (`{param}` syntax)
- Input file validation (pre-execution checks)
- Output file tracking with glob pattern expansion
- Progress reporting (0%, 10%, 80%, 100% milestones)
- Metadata collection (DCC version, OS, scene info, Python version)
- Enhanced error reporting with full traceback

**Phase 7: Python Client Examples** ✅ COMPLETED
- Complete example scripts in `/examples/`:
  - `submit_simple_job.py` - Basic job submission walkthrough
  - `maya_render_job.py` - Production rendering pipeline
  - `houdini_sim_job.py` - Simulation cache export
  - `batch_jobs.py` - Multiple job management
  - `job_workflow_example.py` - Complex workflow orchestration
- Comprehensive documentation in `examples/README.md`

**Phase 8: Mock Editor Integration** ✅ COMPLETED
- `/mock_editor/` - Complete PySide6 game editor demonstrating integration
- Auto-start orchestrator capability
- Real-time job submission and monitoring UI
- Multi-platform launcher scripts

**Phase 9: Pool Monitoring UI** ✅ COMPLETED
- `/job_orchestrator/ui/pool_monitor.py` - Real-time DCC pool status monitoring
- System tray integration with `/job_orchestrator/ui/tray_app.py`
- Worker instance health tracking and crash detection
- Performance metrics (CPU, memory usage) display

**Phase 10: Worker RPC Standardization** ✅ COMPLETED (February 17, 2026)
- Standardized all workers to `update_status()` pattern with explicit status parameter
- 38 test modules with 100+ individual tests (all passing)
- Comprehensive concurrent worker testing (`test_concurrent_workers.py` - 4 tests)
- Comprehensive load/stress testing (`test_load_stress.py` - 6 tests)
- Mock Editor BP export job path fixes after reorganization

### 🚧 Current Development Focus

**Recent Enhancements (February 2026):**
- ✅ **Worker RPC Standardization** (Feb 17) - All workers use `update_status()` with explicit status parameter
- ✅ **Concurrent Testing** (Feb 17) - 4 tests validating concurrent execution across all 5 worker types
- ✅ **Load/Stress Testing** (Feb 17) - 6 tests for queue depth, priority ordering, throughput validation
- ✅ **Mock Editor Fixes** (Feb 17) - Fixed BP export job references after module reorganization
- ✅ **BP Maya Worker Registration** - Fixed 4-layer import deadlock chain enabling BP Maya integration
  - Fixed logger handler clearing at import (v4.1.0)
  - Fixed OrchestratorConfig import cascade (v4.2.0)
  - Fixed Python import lock deadlock via main thread import pattern (v3.4.0)
  - Fixed psutil type hints with ProcessType alias pattern
- ✅ **Dynamic Worker Types** - Workers self-aware via `JOB_ORCHESTRATOR_WORKER_TYPE` environment variable (v4.3.0)
- ✅ **Worker Type Flexibility** - Support for unlimited Maya variants (`maya`, `bp_mayapy`, `maya_r&d`, etc.)

**Recent Enhancements (January 2026):**
- ✅ **MODULE MODE** - Dual-mode execution: STRING (inline scripts) + MODULE (importable Python modules)
- ✅ **Environment Management** - New `environment_manager.py` with DCC version-aware profiles
- ✅ **Log Consolidation** - All logs migrated to `.temp/logs/` with 5-day retention
- ✅ **Zombie Prevention** - Boot timeout configuration and process tracking
- ✅ **Process Lifecycle** - Enhanced subprocess management and cleanup utilities

**Active Development (February 2026):**
- ✅ **BP Maya Integration** - Workers successfully register and poll for jobs
- ✅ **Job Execution Testing** - End-to-end BP Maya job execution validated
- 🚧 **Multi-Job Workflows** - Cross-DCC dependency validation and edge case handling
- 🚧 **Failed Dependency Cascade** - Auto-fail dependent jobs when dependencies fail
- 🚧 **Output Path Communication** - Automated output discovery for chained workflows

**Next Priorities:**
- Complete C# client library for Unity/Unreal integration
- Integration tests for multi-job workflows
- Performance optimization and scaling improvements
- Enhanced worker health monitoring and auto-recovery

---

## External Job Submission API

### Key Concepts

**Job Request Format:**
```python
{
    "job_type": "maya",            # or "houdini"
    "execution_mode": "HEADLESS",  # or "GUI" (for viewport operations)
    "priority": 5,                 # 0-10, higher = more urgent
    "submitter": "level_editor",   # Client identifier
    "script": """
        import maya.cmds as cmds
        cmds.polySphere(radius={radius})
    """,
    "parameters": {                # Substituted into script
        "radius": 5.0
    },
    "input_files": [               # Validated before execution
        "C:/scenes/input.ma"
    ],
    "output_files": [              # Glob patterns tracked
        "C:/renders/frame_*.png"
    ],
    "metadata": {                  # Custom key-value data
        "project": "game_assets",
        "user": "artist_01"
    }
}
```

**Job Lifecycle:**
1. **Submit** → Job queued with priority
2. **Queue** → Wait for available DCC instance
3. **Running** → Execute script with progress reporting
4. **Completed/Failed** → Result cached for retrieval

**Progress Reporting:**
- Workers report progress at milestones (0%, 10%, 80%, 100%)
- External clients receive real-time updates via `StreamJobStatus`
- Custom progress can be added via callback injection (future)

**Output Tracking:**
- Glob patterns expanded after execution
- Actual output files returned in `JobResult`
- Missing expected outputs logged but don't fail job

---

## MODULE MODE Job Development

### Creating Reusable Job Modules

Job modules live in `job_orchestrator/jobs/` and follow a **3-layer architecture pattern**:

**Layer 1: Reusable Core Function**
- Single-concern function with explicit parameters (not orchestrator dict)
- Can be imported and called from other scripts, shelf tools, or batch processes
- No dependencies on orchestrator infrastructure
- Pure business logic

**Layer 2: Orchestrator Integration Wrapper (`main()`)**
- Bridges orchestrator's dict-based parameters to core function's explicit args
- Handles parameter unpacking, defaults, type conversion, validation
- Thin translation layer - no business logic

**Layer 3: Development Testing Entry (`if __name__ == "__main__"`)**
- Allows technical artists to test in DCC Python Shell WITHOUT orchestrator
- Fast iteration - change parameters, run, see results
- Supports debugging with breakpoints in DCC environment
- Documents example usage

**Standard Job Module Structure:**

```python
"""
Package: job_orchestrator.jobs.examples.maya.generate_hero_sword
Generate a hero sword asset for game environments.

This module creates a parametric sword mesh with customizable dimensions,
materials, and LOD levels for use in game engines.
"""

import logging as _logging
from pathlib import Path
from typing import Any

# DCC imports (only available in worker runtime)
import maya.cmds as cmds

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "job_orchestrator.jobs.examples.maya.generate_hero_sword"
__updated__ = "2026-01-08 09:45:00"
__version__ = "1.0.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
def create_hero_sword(
    asset_name: str,
    output_dir: str,
    sword_length: float = 120.0,
    blade_width: float = 5.0,
    material: str = "steel"
) -> dict[str, Any]:
    """Create hero sword asset (REUSABLE CORE FUNCTION).

    :param asset_name: Name for the sword asset
    :param output_dir: Output directory for files
    :param sword_length: Total sword length in cm (default: 120)
    :param blade_width: Blade width in cm (default: 5)
    :param material: Material type ("steel", "iron", "gold")
    :return: Dict with output paths and metadata
    :raises RuntimeError: If asset generation fails
    """
    _LOGGER.info(f"Creating hero sword: {asset_name}")

    # Create geometry
    blade = cmds.polyCube(width=blade_width, height=sword_length, depth=1.0, name="sword_blade")[0]
    handle = cmds.polyCylinder(radius=2.0, height=20.0, name="sword_handle")[0]
    cmds.move(0, -sword_length/2 - 10, 0, handle)

    # Combine and clean up
    sword = cmds.polyUnite(blade, handle, name="hero_sword")[0]
    cmds.delete(sword, constructionHistory=True)

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save Maya scene
    mb_file = output_path / f"{asset_name}.mb"
    cmds.file(rename=str(mb_file))
    cmds.file(save=True, type="mayaBinary", force=True)

    # Export FBX
    fbx_file = output_path / f"{asset_name}.fbx"
    cmds.select(sword)
    cmds.file(str(fbx_file), force=True, options="v=0", type="FBX export", exportSelected=True)

    # Return metadata
    poly_count = cmds.polyEvaluate(sword, triangle=True)
    _LOGGER.info(f"Sword exported: {poly_count} triangles")

    return {
        "maya_scene": str(mb_file),
        "fbx_file": str(fbx_file),
        "polygon_count": poly_count,
        "material": material
    }


# -------------------------------------------------------------------------
def main(parameters: dict[str, Any]) -> dict[str, Any]:
    """Orchestrator integration wrapper (PARAMETER UNPACKING ONLY).

    :param parameters: Job parameters from orchestrator
        - asset_name: str - Asset identifier (required)
        - output_dir: str - Output directory (required)
        - sword_length: float - Sword length in cm (default: 120)
        - blade_width: float - Blade width in cm (default: 5)
        - material: str - Material type (default: "steel")
    :return: Execution metadata from create_hero_sword()
    """
    # Extract and convert parameters (thin wrapper - no business logic)
    asset_name = parameters["asset_name"]
    output_dir = parameters["output_dir"]
    sword_length = float(parameters.get("sword_length", 120.0))
    blade_width = float(parameters.get("blade_width", 5.0))
    material = parameters.get("material", "steel")

    # Call reusable core function
    return create_hero_sword(
        asset_name=asset_name,
        output_dir=output_dir,
        sword_length=sword_length,
        blade_width=blade_width,
        material=material
    )


# -------------------------------------------------------------------------
if __name__ == "__main__":
    """Test entry point - run directly in Maya Python Shell."""
    result = main({
        "asset_name": "Test_Sword",
        "output_dir": "C:/Temp/TestAssets",
        "sword_length": "150.0",
        "blade_width": "8.0",
        "material": "gold"
    })

    print("Sword created successfully:")
    for key, value in result.items():
        print(f"  {key}: {value}")
```

**Why This Pattern:**
- **Reusability**: Core function importable from other scripts/tools
- **Testability**: Run standalone in DCC without orchestrator overhead
- **Maintainability**: Clear separation between business logic and orchestrator integration
- **Discoverability**: Technical artists can find and use core functions in their own workflows
- **Consistency**: Every job follows same pattern - learn once, apply everywhere


### Submitting MODULE MODE Jobs

```python
# External client submits job referencing module
job_request = job_pb2.JobRequest(
    dcc_type="maya",
    execution_mode=job_pb2.ExecutionMode.HEADLESS,
    module_path="job_orchestrator.jobs.examples.maya.generate_hero_sword",
    entry_point="main",  # Function to call (default: "main")
    parameters={
        "sword_length": 120,
        "blade_width": 5.0,
        "material": "steel",
        "output_path": "C:/assets/hero_sword.fbx"
    },
    output_files=["C:/assets/hero_sword.fbx"],
    priority=5
)

response = await stub.SubmitJob(job_request)
```

### MODULE MODE Advantages

- **IDE Support**: Full autocomplete, type checking, refactoring in VS Code
- **Debugging**: Set breakpoints, step through code in Maya/Houdini GUI
- **Testing**: Unit testable functions, run standalone without orchestrator
- **Reusability**: Import shared utilities, build asset libraries
- **Maintainability**: Proper module structure, version control friendly

**See [job_orchestrator/jobs/README.md](job_orchestrator/jobs/README.md) for comprehensive MODULE MODE development guide.**

---

## Testing Standards

### Test Organization

Tests live in `tests/` and are organized by component with pytest markers:

**Markers:**
- `@pytest.mark.unit` - Fast, isolated tests (<1s each)
- `@pytest.mark.integration` - Multi-component tests (5-30s, may spawn processes)
- `@pytest.mark.slow` - Tests >5 seconds

**Test Structure:**
```python
"""
Package: tests.test_my_feature
Brief description of what this validates.
"""

import logging as _logging
import pytest

_MODULE_NAME = "tests.test_my_feature"
__updated__ = "YYYY-MM-DD HH:MM:SS"
__version__ = "1.0.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


@pytest.mark.unit
def test_basic_functionality():
    """Test basic feature behavior."""
    assert expected_result == actual_result


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_workflow():
    """Test end-to-end integration."""
    result = await complex_async_operation()
    assert result.success is True
```

### Available Fixtures (conftest.py)

- `event_loop` - Async event loop for pytest-asyncio
- `mock_admin_api_stub` - Mocked gRPC AdminAPI stub
- `mock_pool_manager` - Mocked DCCPoolManager
- `ghost_instance_data` - Sample ghost instance (with time_removed)
- `live_instance_data` - Sample live instance
- `temp_orchestrator_config` - Temporary isolated config file

### Running Tests

```powershell
# All tests
pytest tests/ -v

# By marker
pytest tests/ -v -m unit           # Fast unit tests only
pytest tests/ -v -m integration    # Integration tests only
pytest tests/ -v -m "not slow"     # Exclude slow tests

# Specific components
pytest tests/test_ghost_instance_restart.py -v
pytest tests/test_monitoring_config.py -v
pytest tests/test_job*.py -v

# With coverage
pytest tests/ --cov=job_orchestrator --cov-report=html
```

**See [tests/README.md](tests/README.md) for comprehensive testing guide.**

---

## Code Generation Guidance

When Copilot writes code in this repository:

### UI Layer (PySide6)
- Use `QSystemTrayIcon`, `QMenu`, and `QAction` for tray controls.
- Add a table-based UI (`QTableWidget`) to show job queue and status.
- Use signals or `asyncio` tasks to refresh UI automatically when jobs update.

### Orchestrator Engine
- Implement `Job` and `JobManager` classes with lifecycle states:
  - `queued → running → completed/failed`
- Use `asyncio.Queue` for job management.
- Allow job chaining by waiting for dependencies to complete.

### gRPC Integration
- Generate `.proto` stubs in `/grpc` using `grpc_tools.protoc`.
- The orchestrator runs as a gRPC server with methods:
  - `SubmitJob`, `GetStatus`, `CancelJob`, `RegisterClient`, `RequestJob`, `UpdateStatus`.
- The DCC clients (Maya, Houdini) act as gRPC clients registered dynamically.
- Use async bi-directional streaming for job updates if available.

### DCC Instance Management
- Enforce a single active Maya and Houdini process.
- Use `subprocess.Popen` to start headless/rpc-enabled sessions.
- Implement automatic cleanup on exit or failure.

### Testing
- Add `pytest` test cases for:
  - job queuing
  - completion dependencies
  - gRPC SubmitJob round-trip
  - DCC registration and simulated job execution

---

## Configuration and Developer Workflow

### Environment Setup
Copilot should automatically suggest:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
make proto
make run

### Makefile Targets
proto: # Compile protobufs (in job_orchestrator/protos/)
run: # Launch orchestrator server + tray UI
ui: # Only start PySide6 tray app
test: # Run unit tests
clean: # Remove caches and auto-generated protobufs


---

## Python Module Structure Standards

**All Python modules must follow this exact structure:**

```python
"""
Package: module.path.name
Brief one-line description.

Detailed multi-line description of module purpose,
responsibilities, and key functionality.
"""

import asyncio
import logging as _logging
from typing import Any

# External imports
from PySide6.QtCore import Signal

# Project imports (absolute paths only)
from job_orchestrator.orchestrator.job import Job
from mock_editor.client.orchestrator_client import OrchestratorClient

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "module.path.name"  # Must match Package docstring
__updated__ = "YYYY-MM-DD HH:MM:SS"
__version__ = "X.Y.Z"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)  # Use explicit module name, NOT __name__
```

**Critical Rules:**
- **Package docstring**: First line is `Package: module.path.name` (hierarchical dot notation)
- **Module metadata**: Define `_MODULE_NAME`, `__updated__`, `__version__`, `__author__` after imports
- **Explicit logger naming**: Use `_LOGGER = _logging.getLogger(_MODULE_NAME)` NOT `getLogger(__name__)`
  - This ensures consistent, explicit hierarchical naming in logs
  - Makes log filtering and debugging more transparent
  - Matches the established coding style hallmark
- **Import aliasing**: `import logging as _logging` to avoid namespace collisions
- **Absolute imports only**: Use `from job_orchestrator.module` NOT `from ..module`
- **Compact ReST docstrings**: Use `:param:`, `:return:`, `:raises:`, `.. note::` format
- **Line length**: 120 characters maximum
- **Type hints**: Use modern syntax like `dict[str, Any]`, `list[str]`

**Example Module:**
```python
"""
Package: tests.test_mock_editor
Quick test launcher for Mock Editor.

This module provides an intelligent launcher that auto-starts the orchestrator
if not available, then launches the Mock Editor UI.
"""

import asyncio
import logging as _logging
import sys

from mock_editor.client.orchestrator_client import OrchestratorClient

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_mock_editor"
__updated__ = "2025-11-02 01:15:00"
__version__ = "1.0.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
async def main_async() -> int:
    """Main entry point with orchestrator auto-start.

    :return: Exit code (0 for success, 1 for failure)
    """
    _LOGGER.info("Starting Mock Editor launcher")
    # ... implementation
```

---

## Resolved Technical Issues

### ✅ Pool Status gRPC Method Issue - RESOLVED (November 2025)

**Issue:** GetPoolStatus gRPC calls caused server crashes and protobuf import errors.

**Root Cause:** Manual protobuf compilation using `python -m grpc_tools.protoc` did not properly fix Python import paths, causing gRPC service registration failures and client-server communication issues.

**Solution:** Use `compile_protos.bat` script which:
1. Compiles protobuf files with correct paths
2. Runs `scripts/fix_protobuf_imports.py` to resolve Python import conflicts
3. Ensures proper gRPC stub generation and class accessibility

**Resolution Steps:**
```bash
# CRITICAL: Always use this for protobuf changes
compile_protos.bat
# OR
make proto  # Now correctly uses compile_protos.bat
```

**Verification:**
- ✅ GetPoolStatus gRPC calls work without server crashes
- ✅ Pool monitor UI launches successfully
- ✅ All protobuf classes properly accessible
- ✅ gRPC communication functional between clients and server

**Key Lesson:** Always use the project's established build tools (`compile_protos.bat`) rather than manual protoc commands to ensure proper import fixing and class generation.

---

## Logging & Process Management

### Log Location & Retention

**All logs are centralized in `.temp/logs/` with automatic cleanup:**

```
.temp/logs/
  ├── orchestrator_{timestamp}.log          # Main orchestrator process
  ├── mock_editor_{timestamp}.log           # Mock editor application
  ├── maya_headless_{id}_pid{pid}.log       # Maya workers
  ├── maya_gui_{id}_pid{pid}.log
  ├── houdini_headless_{id}_pid{pid}.log    # Houdini workers
  └── houdini_gui_{id}_pid{pid}.log
```

**Retention Policy (orchestrator_config.json):**
- Default: 5 days (`max_age_days`)
- Max logs per instance: 3 (`max_logs_per_instance`)
- Max total size: 200 MB (`max_total_size_mb`)
- Crashed instance logs: Not preserved by default (`preserve_crashed: false`)

**Cleanup happens automatically on orchestrator startup** via `log_manager.cleanup_on_startup()`.

### Process Cleanup Utilities

**Safe termination scripts (see `/scripts/`):**

```powershell
# Kill all orchestrator processes (server, tray, pool monitor)
python scripts/kill_orchestrator.py
# Safety: Only kills processes from THIS workspace using path matching
# Protects: VS Code extensions, debuggers, other Python tools

# Kill DCC workers only (Maya, Houdini instances)
python scripts/kill_all_dcc.py

# Remove old logs (5+ days)
python scripts/cleanup_tmp_logs.py

# Diagnose zombie process issues
python scripts/diagnose_zombies.py
```

**Zombie Prevention:**
- Boot timeout enforced: 120 seconds (configurable in `orchestrator_config.json`)
- Process health tracking via `instance.process.poll()`
- Graceful shutdown with `terminate()` → `wait(3s)` → `kill()` fallback
- See `kill_orchestrator.py` for workspace-safe process matching patterns

---

## UI Development & Mock Editor Integration

### Mock Editor (`/mock_editor/`)

**Complete PySide6 integration demonstrating:**
- Auto-start orchestrator detection and launch
- gRPC client wrapper (`OrchestratorClient`) with async job submission
- Real-time job monitoring and status updates
- Multi-platform launcher scripts (`.bat` and `.ps1`)

**Architecture:**
```python
# main.py - Entry point with orchestrator auto-start
async def ensure_orchestrator_running() -> bool:
    """Check if orchestrator is available, start if needed."""

# client/orchestrator_client.py - gRPC wrapper
class OrchestratorClient:
    async def submit_job(self, job_request: dict) -> str:
        """Submit job and return job_id."""

    async def stream_job_status(self, job_id: str):
        """Stream real-time job status updates."""

# ui/main_window.py - Job submission interface
class MainWindow(QMainWindow):
    """Game editor UI with job submission panel."""
```

### Pool Monitor UI (`/job_orchestrator/ui/pool_monitor.py`)

**Real-time DCC pool monitoring:**
- Live worker instance status (BOOTING, READY, BUSY, CRASHED)
- Performance metrics (CPU, memory usage per instance)
- Health tracking and crash detection
- Refresh controls (manual + auto-refresh)

**System Tray Integration (`/job_orchestrator/ui/tray_app.py`):**
- Background orchestrator status monitoring
- Quick access to pool monitor window
---

## Maya Coding Standards & Validation

**CRITICAL: Avoid PyMEL and MEL**

When generating Maya code, Copilot must:
- ✅ **USE:** `maya.cmds` for scene operations
- ✅ **USE:** `maya.api.OpenMaya` (OpenMaya 2.0) for API access
- ❌ **NEVER USE:** `pymel.core` or any PyMEL imports
- ❌ **NEVER USE:** `maya.mel.eval()` or MEL commands
- ❌ **NEVER USE:** `pm.*` (PyMEL abbreviation)

**Rationale:**
- PyMEL is deprecated and not actively maintained
- MEL is legacy scripting language, error-prone
- `maya.cmds` is stable, well-documented, and future-proof
- OpenMaya 2.0 provides full API access for performance-critical operations

**Example - Correct:**
```python
import maya.cmds as cmds
from maya.api import OpenMaya as om

# Create a sphere
sphere = cmds.polySphere(radius=5)[0]
cmds.move(0, 5, 0, sphere)

# API usage for performance
sel = om.MSelectionList()
sel.add(sphere)
dag_path = sel.getDagPath(0)
```

**Example - WRONG:**
```python
import pymel.core as pm  # ❌ NO! Forbidden!
sphere = pm.polySphere(radius=5)[0]
pm.move(0, 5, 0, sphere)
```

### Code Validation System (3-Tier)

Maya workers **automatically enforce** PyMEL/MEL detection for STRING MODE jobs.

**Tier 1: Global Configuration (`orchestrator_config.json`)**

```json
{
  "maya": {
    "code_validation": {
      "enabled": true,        // Enable/disable validation system-wide
      "allow_pymel": false,   // Global PyMEL policy
      "allow_mel": false      // Global MEL policy
    }
  }
}
```

**Tier 2: Job-Level Overrides (Job `metadata`)**

For rare cases requiring MEL/PyMEL (legacy tools, workarounds):

```python
# External client submits job with validation override
job_request = job_pb2.JobRequest(
    dcc_type="maya",
    script="""
import maya.cmds as cmds
cmds.mel.eval('FBXExport -f "output.fbx"')  # Legacy MEL command
""",
    metadata={
        "allow_mel": "true",  # Override global policy for THIS job only
        "mel_reason": "FBX export requires legacy MEL command for texture embedding"
    },
    priority=5
)
```

**Tier 3: Runtime Validation (`maya_utils.validate_maya_code()`)**

```python
from job_orchestrator.utils import maya_utils

# Validate code with overrides
is_valid, error_msg = maya_utils.validate_maya_code(
    code=script,
    allow_pymel=False,  # From config or job metadata
    allow_mel=True      # From job metadata override
)

if not is_valid:
    raise RuntimeError(f"Validation failed: {error_msg}")
```

**Precedence:** Job Metadata > Global Config > Hardcoded Default (strict)

**Validation Applies To:**
- ✅ STRING MODE jobs (inline scripts with parameter substitution)
- ❌ MODULE MODE jobs (importable Python modules - validated by IDE/tests)

**Validation Enforcement:**
- Runs after input file validation (Step 2 in job execution)
- Blocks job execution if invalid (FAILED status, clear error message)
- Logs decision: ENFORCED (strict), RELAXED (override), or DISABLED (global)

**When to Use Overrides:**
- **Last resort only** - Prefer `maya.cmds` refactoring
- Legacy FBX export commands requiring MEL
- Third-party tools with embedded PyMEL
- Document reason in `metadata` (e.g., `pymel_reason`, `mel_reason`)

**Configuration Examples:**

**Disable validation globally (development/testing):**
```json
{
  "maya": {
    "code_validation": {
      "enabled": false
    }
  }
}
```

**Allow MEL globally (legacy pipeline migration):**
```json
{
  "maya": {
    "code_validation": {
      "enabled": true,
      "allow_pymel": false,
      "allow_mel": true
    }
  }
}
```

**Strict enforcement (production default):**
```json
{
  "maya": {
    "code_validation": {
      "enabled": true,
      "allow_pymel": false,
      "allow_mel": false
    }
  }
}
```

**Job Logs Show Validation Decisions:**
```
--- CODE VALIDATION ---
Code validation: ENFORCED (strict mode)
  PyMEL: DENIED
  MEL: DENIED
[OK] Code validation passed
```

Or with override:
```
--- CODE VALIDATION ---
Code validation relaxed (override active):
  MEL allowed (allow_mel=true)
  Reason: FBX export requires legacy MEL command
[OK] Code validation passed
```

## DCC Execution Modes

Jobs must specify execution mode in the `Job` object:
- **HEADLESS** (default): Use mayapy.exe/hython.exe - fastest, lowest memory, no GUI
- **GUI**: Use maya.exe/houdini.exe - only when viewport operations required

**Example viewport operations requiring GUI mode:**
- Playblast generation (`cmds.playblast()`)
- Viewport screenshots
- Interactive viewport rendering
- UI-based operations

**Default to HEADLESS unless viewport explicitly needed.**

---

## Python Module Structure Standards

**All Python modules must follow this exact structure:**

```python
"""
Package: module.path.name
Brief one-line description.

Detailed multi-line description of module purpose,
responsibilities, and key functionality.
"""

import asyncio
import logging as _logging
from typing import Any

# External imports
from PySide6.QtCore import Signal

# Project imports (absolute paths only)
from job_orchestrator.orchestrator.job import Job
from mock_editor.client.orchestrator_client import OrchestratorClient

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "module.path.name"  # Must match Package docstring
__updated__ = "YYYY-MM-DD HH:MM:SS"
__version__ = "X.Y.Z"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)  # Use explicit module name, NOT __name__
```

**Critical Rules:**
- **Package docstring**: First line is `Package: module.path.name` (hierarchical dot notation)
- **Module metadata**: Define `_MODULE_NAME`, `__updated__`, `__version__`, `__author__` after imports
- **Explicit logger naming**: Use `_LOGGER = _logging.getLogger(_MODULE_NAME)` NOT `getLogger(__name__)`
  - This ensures consistent, explicit hierarchical naming in logs
  - Makes log filtering and debugging more transparent
  - Matches the established coding style hallmark
- **Import aliasing**: `import logging as _logging` to avoid namespace collisions
- **Absolute imports only**: Use `from job_orchestrator.module` NOT `from ..module`
- **Compact ReST docstrings**: Use `:param:`, `:return:`, `:raises:`, `.. note::` format
- **Line length**: 120 characters maximum
- **Type hints**: Use modern syntax like `dict[str, Any]`, `list[str]`

**Example Module:**
```python
"""
Package: tests.test_mock_editor
Quick test launcher for Mock Editor.

This module provides an intelligent launcher that auto-starts the orchestrator
if not available, then launches the Mock Editor UI.
"""

import asyncio
import logging as _logging
import sys

from mock_editor.client.orchestrator_client import OrchestratorClient

# -------------------------------------------------------------------------
# module global scope
_MODULE_NAME = "tests.test_mock_editor"
__updated__ = "2025-11-02 01:15:00"
__version__ = "1.0.0"
__author__ = ["jGalloway"]

_LOGGER = _logging.getLogger(_MODULE_NAME)


# -------------------------------------------------------------------------
async def main_async() -> int:
    """Main entry point with orchestrator auto-start.

    :return: Exit code (0 for success, 1 for failure)
    """
    _LOGGER.info("Starting Mock Editor launcher")
    # ... implementation
```

---

## Commands Copilot Can Auto-Generate

1. **Protobuf compilation command (CRITICAL - use proper script):**
compile_protos.bat  # Compiles AND fixes imports
make proto          # Alternative using Makefile
2. **Dependency installation:**
pip install pyside6 grpcio grpcio-tools protobuf pytest qasync
3. **Launch main orchestrator:**
python job_orchestrator/main.py


---

## Copilot Tone and Style

When writing code:
- Follow PEP8 formatting.
- Add detailed function docstrings with argument and return types.
- Include `# TODO` comments to mark unimplemented DCC integration points.
- Use neutral, production-ready naming conventions (`OrchestratorServer`, `JobManager`, `TrayApp`).
- When writing examples or templates, prefer clarity and maintainability over brevity.

---

## Example Commit Messages

To maintain clear project history, prefer these commit prefixes:
- `feat:` for new module or gRPC interface
- `fix:` for resolved errors or UI issues
- `refactor:` for architectural or structural improvement
- `test:` for test-related commits
- `docs:` for documentation updates

---

## Copilot Behavior Summary

Copilot serves as:
- **Architect & Implementer:** Generate production-quality modules that match the Job Orchestrator system design.
- **DevOps Assistant:** Provide Makefile tasks, CI hints, and prototyping boilerplate.
- **Documentation Partner:** Generate docstrings, READMEs, and `.proto` schema explanations automatically.

Do not generate placeholder “Hello World” or unrelated demo code. Every file should directly support the orchestration and UI pipeline.

---

## Goal State

By the end of setup, the repository should:
1. Launch a running gRPC orchestrator server with `make run`.
- Or `make run-ui` to start the orchestrator and the system tray app (with dcc pool monitor)
2. Show a functioning system tray UI.
3. Support job submission and dependency-chained execution.
4. Provide modular, testable code units in `orchestrator/`, `ui/`, and `dcc_clients/`.
