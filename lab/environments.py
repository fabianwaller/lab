# Lab is a Python package for evaluating algorithms.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import multiprocessing
import os
import random
import re
import subprocess
import sys
from datetime import datetime

from lab import tools
from math import ceil

def _get_job_prefix(exp_name):
    assert exp_name
    escape_char = "j" if exp_name[0].isdigit() else ""
    return "".join([escape_char, exp_name, "-"])


def is_build_step(step):
    """Return true iff the given step is the "build" step."""
    return step._funcname == "build"


def is_run_step(step):
    """Return true iff the given step is the "run" step."""
    return step._funcname == "start_runs"


class Environment:
    """Abstract base class for all environments."""

    def __init__(self, randomize_task_order=True):
        """
        If *randomize_task_order* is True (default), tasks for runs are
        started in a random order. This is useful to avoid systematic
        noise due to, e.g., one of the algorithms being run on a
        machine with heavy load. Note that due to the randomization,
        run directories may be pristine while the experiment is running
        even though the logs say the runs are finished.

        """
        self.exp = None
        self.randomize_task_order = randomize_task_order

    def _get_task_order(self):
        task_order = list(range(1, len(self.exp.runs) + 1))
        if self.randomize_task_order:
            random.shuffle(task_order)
        return task_order

    def write_main_script(self):
        raise NotImplementedError

    def start_runs(self):
        """
        Execute all runs that are part of the experiment.
        """
        raise NotImplementedError

    def run_steps(self):
        raise NotImplementedError

    def uses_scratch(self):
        return False

    def check_cluster_status(self, printout=True):
        """
        Check the status of all cluster jobs. Return True if there is a running job.
        """
        print("Checking cluster status is not implemented for this environment.")

    def submitted_job_categories(self):
        """
        Check if a run step has been submitted before.
        """
        return []

    def remove_cluster_jobs(self, confirm: bool):
        """
        Check the status of all cluster jobs. Return True if all jobs are completed.
        """
        print("Removing cluster jobs is not implemented for this environment.")


class LocalEnvironment(Environment):
    """
    Environment for running experiments locally on a single machine.
    """

    EXP_RUN_SCRIPT = "run"

    def __init__(self, processes=None, **kwargs):
        """
        If given, *processes* must be between 1 and #CPUs. If omitted,
        it will be set to #CPUs.

        See :py:class:`~lab.environments.Environment` for inherited
        parameters.

        """
        Environment.__init__(self, **kwargs)
        cores = multiprocessing.cpu_count()
        if processes is None:
            processes = cores
        if not 1 <= processes <= cores:
            raise ValueError("processes must be in the range [1, ..., #CPUs].")
        self.processes = processes

    def write_main_script(self):
        script = tools.fill_template(
            "local-job.py", task_order=self._get_task_order(), processes=self.processes
        )

        self.exp.add_new_file("", self.EXP_RUN_SCRIPT, script, permissions=0o755)

    def start_runs(self):
        tools.run_command(
            [tools.get_python_executable(), self.EXP_RUN_SCRIPT], cwd=self.exp.path
        )

    def run_steps(self, steps):
        for step in steps:
            step()


class GridEnvironment(Environment):
    """Abstract base class for grid environments."""

    # Must be overridden in derived classes.
    JOB_HEADER_TEMPLATE_FILE = None
    RUN_JOB_BODY_TEMPLATE_FILE = None
    STEP_JOB_BODY_TEMPLATE_FILE = None

    # Can be overridden in derived classes.
    MAX_TASKS = float("inf")

    def __init__(self, email=None, extra_options=None, **kwargs):
        """

        If the main experiment step is part of the selected steps, the
        selected steps are submitted to the grid engine. Otherwise, the
        selected steps are run locally.

        .. note::

            If the steps are run by the grid engine, this class writes
            job files to the directory ``<exppath>-grid-steps`` and
            makes them depend on one another. Please inspect the \\*.log
            and \\*.err files in this directory if something goes wrong.
            Since the job files call the experiment script during
            execution, it mustn't be changed during the experiment.

        If *email* is provided and the steps run on the grid, a message
        will be sent when the last experiment step finishes.

        Use *extra_options* to pass additional options. The
        *extra_options* string may contain newlines. Slurm example that
        reserves two cores per run::

            extra_options='#SBATCH --cpus-per-task=2'

        See :py:class:`~lab.environments.Environment` for inherited
        parameters.

        """
        Environment.__init__(self, **kwargs)
        self.email = email
        self.extra_options = extra_options or "## (not used)"

    def start_runs(self):
        # The queue will start the experiment by itself.
        pass

    def _get_job_name(self, step):
        return (
            f"{_get_job_prefix(self.exp.name)}"
            f"{self.exp.steps.index(step) + 1:02d}-{step.name}"
        )

    def _get_num_runs(self):
        num_runs = len(self.exp.runs)
        if num_runs > self.MAX_TASKS:
            logging.critical(
                f"You are trying to submit a job with {num_runs} tasks, "
                f"but only {self.MAX_TASKS} are allowed."
            )
        return num_runs

    def _get_num_tasks(self, step):
        if is_run_step(step):
            return self._get_num_runs()
        else:
            return 1

    def _get_job_params(self, step, is_last):
        return {
            "errfile": "driver.err",
            "extra_options": self.extra_options,
            "logfile": "driver.log",
            "name": self._get_job_name(step),
            "num_tasks": self._get_num_tasks(step),
        }

    def _get_job_header(self, step, is_last):
        job_params = self._get_job_params(step, is_last)
        return tools.fill_template(self.JOB_HEADER_TEMPLATE_FILE, **job_params)

    def _get_run_job_body(self):
        return tools.fill_template(
            self.RUN_JOB_BODY_TEMPLATE_FILE,
            task_order=" ".join(str(i) for i in self._get_task_order()),
            exp_path=self.exp.path,
            use_scratch="true" if self.USE_SCRATCH else "false",
            python=tools.get_python_executable(),
        )

    def _get_step_job_body(self, step):
        return tools.fill_template(
            self.STEP_JOB_BODY_TEMPLATE_FILE,
            cwd=os.getcwd(),
            python=tools.get_python_executable(),
            script=sys.argv[0],
            step_name=step.name,
        )

    def _get_job_body(self, step):
        if is_run_step(step):
            return self._get_run_job_body()
        return self._get_step_job_body(step)

    def _get_job(self, step, is_last):
        return f"{self._get_job_header(step, is_last)}\n\n{self._get_job_body(step)}"

    def _get_job_dir_path(self):
        return self.exp.path + "-grid-steps"

    def _get_id_file_path(self):
        return os.path.join(self._get_job_dir_path(), "cluster_ids")

    def _read_id_file(self):
        if not os.path.exists(self._get_id_file_path()):
            return None
        with open(self._get_id_file_path(), "r") as f:
            entries = list()
            for line in f:
                strings = line.split()
                entries.append({"cluster_id": strings[0], "name": strings[1], "category": strings[2],
                                "time": f"{strings[3]} {strings[4]}"})
            return entries

    def write_main_script(self):
        # The main script is written by the run_steps() method.
        pass

    def prepare_job_dir(self, steps):
        job_dir = self._get_job_dir_path()

        if os.path.exists(job_dir):
            if self.check_cluster_status(printout=False):
                tools.confirm_or_abort(
                    f'You have submitted jobs for this experiment that are currently running. '
                    f'Do you want to cancel them in order to proceed.'
                )
                self.remove_cluster_jobs(confirm=False)
            if (any(is_run_step(step) for step in steps) and
                    ("main" in self.submitted_job_categories() or "dag" in self.submitted_job_categories())):
                tools.confirm_or_abort(
                    f"You are about to submit the main experiment step and the grid-steps directory is not empty.\n"
                    f"Confirm that you want to delete the grid-steps, and submit the experiment (again)?"
                )
                tools.remove_path(job_dir)

        # Overwrite exp dir if it exists.
        if any(is_build_step(step) for step in steps):
            self.exp._remove_experiment_dir()

        # Remove eval dir if it exists.
        if os.path.exists(self.exp.eval_dir):
            if tools.answer_yes(f'The evaluation directory "{self.exp.eval_dir}" already exists. '
                                f'Do you want to remove it?'):
                tools.remove_path(self.exp.eval_dir)

        # Create job dir only when we need it.
        tools.makedirs(job_dir)
        return job_dir

    def run_steps(self, steps):
        """
        We can't submit jobs from within the grid, so we submit them
        all at once with dependencies. We also can't rewrite the job
        files after they have been submitted.
        """
        self.exp.build(write_to_disk=False)
        job_dir = self.prepare_job_dir(steps)
        prev_job_id = None
        for step in steps:
            job_name = self._get_job_name(step)
            job_file = os.path.join(job_dir, job_name)
            job_content = self._get_job(step, is_last=(step == steps[-1]))
            tools.write_file(job_file, job_content)
            prev_job_id = self._submit_job(job_name, job_file, job_dir, is_run_step(step), dependency=prev_job_id)

    def _submit_job(self, job_name, job_file, job_dir, is_main_job, dependency=None):
        raise NotImplementedError

    def submitted_job_categories(self):
        entries = self._read_id_file()
        job_categories = []
        for entry in entries:
            job_categories.append(entry["category"])
        return job_categories


class FAISlurmEnvironment(GridEnvironment):

    DEFAULT_PARTITION = "fai0x"
    DEFAULT_QOS = "normal"
    DEFAULT_MEMORY_PER_CPU = "3872M"
    DEFAULT_CPUS = 1
    DEFAULT_EXPORT = ["ALL"]
    DEFAULT_SETUP = ""
    USE_SCRATCH = True
    JOB_HEADER_TEMPLATE_FILE = "slurm-job-header"
    RUN_JOB_BODY_TEMPLATE_FILE = "slurm-run-job-body"
    STEP_JOB_BODY_TEMPLATE_FILE = "slurm-step-job-body"

    EXTRA_STEP_CPUS = 8
    EXTRA_STEP_MEMORY_PER_CPU = "1G"
    EXTRA_STEP_PARTITION = "fai-all"

    def __init__(
        self,
        partition=None,
        qos=None,
        memory_per_cpu=None,
        cpus=None,
        export=None,
        setup=None,
        use_scratch=None,
        slurm_time_limit=None,
        **kwargs,
    ):
        """

        *partition* must be a valid Slurm partition name.

        *slurm_time_limit* is the time limit for the slurm job in minutes
        (if an integer is passed), or the slurm time limit as a string in the appropriate format
        (see documentation for --time in https://slurm.schedmd.com/sbatch.html).

        *use_scratch* indicates whether to execute the run in a scratch directory
        on the remote machine.

        *memory_per_cpu* must be a string specifying the memory
        allocated for each core. The string must end with one of the
        letters K, M or G. The default is "3872M". The value for
        *memory_per_cpu* should not surpass the amount of memory that is
        available per core. Processes that surpass the *memory_per_cpu* limit are
        terminated with SIGKILL. To impose a soft limit that can be
        caught from within your programs, you can use the
        ``memory_limit`` kwarg of
        :py:func:`~lab.experiment.Run.add_command`. Fast Downward users
        should set memory limits via the ``driver_options``.

        Slurm limits the memory with cgroups. Unfortunately, this often
        fails on our nodes, so we set our own soft memory limit for all
        Slurm jobs. We derive the soft memory limit by multiplying the
        value denoted by the *memory_per_cpu* parameter with 0.98 (the
        Slurm config file contains "AllowedRAMSpace=99" and we add some
        slack). We use a soft instead of a hard limit so that child
        processes can raise the limit.

        Use *export* to specify a list of environment variables that
        should be exported from the login node to the compute nodes (default: ["PATH"]).

        You can alter the environment in which the experiment runs with
        the **setup** argument. If given, it must be a string of Bash
        commands. Example::

            # Load Singularity module.
            setup="module load Singularity/2.6.1 2> /dev/null"

        See :py:class:`~lab.environments.GridEnvironment` for inherited
        parameters.

        """
        GridEnvironment.__init__(self, **kwargs)

        if partition is None:
            partition = self.DEFAULT_PARTITION
        if qos is None:
            qos = self.DEFAULT_QOS
        if memory_per_cpu is None:
            memory_per_cpu = self.DEFAULT_MEMORY_PER_CPU
        if cpus is None:
            cpus = self.DEFAULT_CPUS
        if export is None:
            export = self.DEFAULT_EXPORT
        if setup is None:
            setup = self.DEFAULT_SETUP
        if use_scratch is not None:
            self.USE_SCRATCH = use_scratch

        self.partition = partition
        self.qos = qos
        self.memory_per_cpu = memory_per_cpu
        self.cpus = self.memory_per_cpu
        self.export = export
        self.setup = setup
        self.slurm_time_limit = slurm_time_limit
        self.cpus = cpus

    @staticmethod
    def _get_memory_in_kb(limit):
        match = re.match(r"^(\d+)(k|m|g)?$", limit, flags=re.I)
        if not match:
            logging.critical(f"malformed memory_per_cpu parameter: {limit}")
        memory = int(match.group(1))
        suffix = match.group(2)
        if suffix is not None:
            suffix = suffix.lower()
        if suffix == "k":
            pass
        elif suffix is None or suffix == "m":
            memory *= 1024
        elif suffix == "g":
            memory *= 1024 * 1024
        return memory

    def _get_job_params(self, step, is_last):
        memory_per_cpu = self.memory_per_cpu if is_run_step(step) else self.EXTRA_STEP_MEMORY_PER_CPU
        cpus = self.cpus if is_run_step(step) else self.EXTRA_STEP_CPUS
        partition = self.partition if is_run_step(step) else self.EXTRA_STEP_PARTITION

        job_params = GridEnvironment._get_job_params(self, step, is_last)

        # Let all tasks write into the same two files. We could use %a
        # (which is replaced by the array ID) to prevent mangled up logs,
        # but we don't want so many files.
        job_params["logfile"] = "slurm.log"
        job_params["errfile"] = "slurm.err"

        job_params["partition"] = partition
        job_params["qos"] = self.qos
        job_params["cpus"] = cpus
        job_params["memory_per_cpu"] = memory_per_cpu
        memory_per_cpu_kb = FAISlurmEnvironment._get_memory_in_kb(memory_per_cpu)
        job_params["soft_memory_limit"] = int(cpus * memory_per_cpu_kb * 0.98)
        # Prioritize array jobs from autonice users.
        job_params["nice"] = 0
        job_params["environment_setup"] = self.setup
        job_params["use_scratch"] = self.USE_SCRATCH
        job_params["slurm_time_limit"] = f"#SBATCH -t {self.slurm_time_limit}" if self.slurm_time_limit else "### none"

        if is_last and self.email:
            job_params["mailtype"] = "END,FAIL,REQUEUE,STAGE_OUT"
            job_params["mailuser"] = self.email
        else:
            job_params["mailtype"] = "NONE"
            job_params["mailuser"] = ""

        return job_params

    def _submit_job(self, job_name, job_file, job_dir, is_main_job, dependency=None):
        submit = ["sbatch"]
        if self.export:
            submit += ["--export", ",".join(self.export)]
        if dependency:
            submit.extend(["-d", "afterany:" + dependency, "--kill-on-invalid-dep=yes"])
        submit.append(job_file)
        logging.info(f"Executing {' '.join(submit)}")
        out = subprocess.check_output(submit, cwd=job_dir).decode()
        logging.info(f"Output: {out.strip()}")
        match = re.match(r"Submitted batch job (\d*)", out)
        assert match, f"Submitting job with sbatch failed: '{out}'"
        cluster_id = match.group(1)
        category = "main" if is_main_job else "other"
        tools.write_file(self._get_id_file_path(),
                         f"{cluster_id} {job_name} {category} {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}\n",
                         append=True)

        return cluster_id

    def uses_scratch(self):
        return self.USE_SCRATCH

    def check_cluster_status(self, printout=True):
        entries = self._read_id_file()
        if not entries:
            print("There are no tracked cluster jobs.")
            return False
        exists_running_job = False
        for entry in entries:
            cluster_id = entry["cluster_id"]
            name = entry["name"]
            time = entry["time"]
            if printout:
                print(f"\nChecking status for job {name} submitted on {time} (cluster id: {cluster_id})")
            out = subprocess.check_output(["squeue", "-j", cluster_id], stderr=subprocess.STDOUT).decode()
            lines = out.splitlines(keepends=True)
            if len(lines) == 1 and "JOBID" in lines[0]:
                if printout:
                    print(f"\nCompleted!\n")
            else:
                if printout:
                    print(f"\nYour job is not completed yet. Details:\n\n{out}")
                exists_running_job = True
        return exists_running_job

    def remove_cluster_jobs(self, confirm=True):
        entries = self._read_id_file()
        if not entries:
            print("There are no tracked cluster jobs.")
        for entry in entries:
            cluster_id = entry["cluster_id"]
            name = entry["name"]
            time = entry["time"]
            out = subprocess.check_output(["squeue", "-j", cluster_id], stderr=subprocess.STDOUT).decode()
            lines = out.splitlines(keepends=True)
            if not (len(lines) == 1 and "JOBID" in lines[0]):
                question = f"Are you sure you want to remove job {name} (cluster id: {cluster_id}, submitted: {time})?"
                if confirm and not tools.answer_yes(question):
                    continue
                print(subprocess.check_output(["scancel", cluster_id], stderr=subprocess.STDOUT).decode())


class FAICondorEnvironment(GridEnvironment):

    DEFAULT_USE_BATCH_MODE = False
    DEFAULT_USE_SCRATCH = True
    DEFAULT_DOCKERIMAGE = "janeisenhut/fai-lab:v0.2"
    DEFAULT_GETENV = ["HOME"]
    DEFAULT_GPUS = 0

    # Dependent on whether batch mode is enabled (without batch mode, with batch mode)
    DEFAULT_CPUS = (1, 16)
    DEFAULT_MEMORY = ("4G", "64G")
    DEFAULT_BATCH_CONCURRENT_PROCESSES = (None, 15)
    DEFAULT_MAX_BATCH_SIZE = (None, 150)
    DEFAULT_RUN_JOB_BODY_TEMPLATE_FILE = ("condor-run-job-body", "condor-batch-job.py")

    # For additional steps, i.e., not the main run step
    EXTRA_STEP_CPUS = 8
    EXTRA_STEP_GPUS = 0
    EXTRA_STEP_MEMORY = "8G"

    JOB_HEADER_TEMPLATE_FILE = "condor-job-header"
    STEP_JOB_BODY_TEMPLATE_FILE = "condor-step-job-body"

    def __init__(
        self,
        use_batch_mode=None,
        docker_image=None,
        getenv=None,
        cpus=None,
        gpus=None,
        memory=None,
        additional_requirements=None,
        use_scratch=None,
        batch_concurrent_processes=None,
        max_batch_size=None,
        **kwargs,
    ):
        """

        *use_batch_mode* (default: False) allows you to group runs into batches, i.e., a number of lab runs are grouped
        into a single Condor job. If you have many relatively short runs, this can increase performance as it
        reduces the overhead due to the Condor scheduler and setting up Docker containers. On the downside, it can also
        have detrimental effects due to segmentation of the available resources. It is also possible that there are not
        enough resources to run bigger batch jobs even though executing single runs would be possible.
        Furthermore, if enabled, you need to pay more attention to make sure that individual runs stick to there
        resource limits, as individual runs are not run in cgroups.

        *docker_image* (default: janeisenhut/fai-lab:v0.2) must be a valid Docker image.
        If the default image does not provide all you need, consider basing your Docker image on the default image
        to make sure that you have everything included to run lab itself. Images can be uploaded to Docker Hub
        (see: https://htcondor.readthedocs.io/en/latest/man-pages/condor_submit.html#docker_image).

        *get_env* (default: HOME) list of which environment variables to export
        (see: https://htcondor.readthedocs.io/en/latest/man-pages/condor_submit.html#getenv).

        *cpus* (default: 1 in normal mode, 16 in batch mode) is the number of CPUs per Condor job
        (see https://htcondor.readthedocs.io/en/latest/man-pages/condor_submit.html#request_cpus).
        If you use batch mode, this refers to the batch, not to single runs and you might want to include
        a CPU for the overhead caused by managing the runs.

        *gpus* (default: 0) is the number of GPUs per Condor job
        (see https://htcondor.readthedocs.io/en/latest/man-pages/condor_submit.html#request_gpus).
        If you use batch mode, this refers to the batch, not to single runs.
        You can use floats here, e.g., set gpus=0.5, to request half a GPU share per Condor job.

        *memory* (default: 4G in normal mode, 64G in batch mode) must be a string specifying the memory allocated
        for each Condor job (see https://htcondor.readthedocs.io/en/latest/man-pages/condor_submit.html#request_memory).
        If you use batch mode, this refers to the batch, not to single runs.
        Remember to leave some margin between the memory limit for the actual lab task(s) and the slurm job.

        *additional_requirements* (default: None) must be a string specifying a requirement expression
        (see https://htcondor.readthedocs.io/en/latest/man-pages/condor_submit.html#requirements).
        The expression will be conjoined with the requirements generated by lab. For instance, you could use
        additional_requirements='(machine == "wali1.hpc.uni-saarland.de" || machine == "wali2.hpc.uni-saarland.de")' to
        force that only the two specified nodes are used.

        *use_scratch* (default: True) indicates whether to execute the run in a scratch directory on the remote machine.

        *batch_concurrent_processes* (default: 15, batch mode only) the number of lab runs to execute in parallel.

        *max_batch_size* (default: 150, batch mode only) the maximum number of lab runs per batch. lab will make sure
        that the number of runs per batch is evenly distributed, i.e., if you have 101 runs and you set
        max_batch_size to 100, there will be two batches with 51 and 50 runs, respectively.

        """
        GridEnvironment.__init__(self, **kwargs)
        self.USE_SCRATCH = use_scratch if use_scratch is not None else self.DEFAULT_USE_SCRATCH
        self.batch_mode = use_batch_mode if use_batch_mode is not None else self.DEFAULT_USE_BATCH_MODE
        self.docker_image = docker_image if docker_image is not None else self.DEFAULT_DOCKERIMAGE
        self.getenv = getenv if getenv is not None else self.DEFAULT_GETENV
        self.gpus = gpus if gpus is not None else self.DEFAULT_GPUS
        self.additional_requirements = f"requirements = $(requirements) && ({additional_requirements})" \
            if additional_requirements is not None else ""

        self.cpus = cpus if cpus is not None else self.DEFAULT_CPUS[int(self.batch_mode)]
        self.memory = memory if memory is not None else self.DEFAULT_MEMORY[int(self.batch_mode)]
        self.batch_concurrent_processes = batch_concurrent_processes if batch_concurrent_processes is not None \
            else self.DEFAULT_BATCH_CONCURRENT_PROCESSES[int(self.batch_mode)]
        self.RUN_JOB_BODY_TEMPLATE_FILE = self.DEFAULT_RUN_JOB_BODY_TEMPLATE_FILE[int(self.batch_mode)]
        self.max_batch_size = max_batch_size if max_batch_size is not None \
            else self.DEFAULT_MAX_BATCH_SIZE[int(self.batch_mode)]

    def _get_job_params(self, step, is_last):
        job_params = GridEnvironment._get_job_params(self, step, is_last)
        job_name = self._get_job_name(step)
        job_params["dockerimage"] = self.docker_image
        job_params["getenv"] = self.getenv
        job_params["requirements"] = self.additional_requirements

        if is_run_step(step) and self.USE_SCRATCH:
            job_params["transfer"] = "should_transfer_files = YES\nwhen_to_transfer_output = ON_EXIT"
        else:
            job_params["transfer"] = "should_transfer_files = NO"

        if self.batch_mode and is_run_step(step):
            num_tasks = self._get_num_tasks(step)
            num_batches = ceil(num_tasks / self.max_batch_size)
            job_params["jobs"] = num_batches
            job_params["executable"] = f"{job_name}.py"
        else:
            job_params["jobs"] = job_params["num_tasks"]
            job_params["executable"] = f"{job_name}.sh"

        job_params["cpus"] = self.cpus if is_run_step(step) else self.EXTRA_STEP_CPUS
        job_params["gpus"] = self.gpus if is_run_step(step) else self.EXTRA_STEP_GPUS
        job_params["memory"] = self.memory if is_run_step(step) else self.EXTRA_STEP_MEMORY

        if is_last and self.email:
            job_params["mail"] = f"notification = Always\nnotify_user = {self.email}"
        else:
            job_params["mail"] = "notification = Never"
        return job_params

    def _submit_job(self, job_name, job_file, job_dir, is_main_job, dependency=None):
        if dependency:
            raise NotImplementedError("Dependency not implemented for this environment")
        submit = ["condor_submit", job_file]
        logging.info(f"Submitting job array: {' '.join(submit)}")
        out = subprocess.check_output(submit, cwd=job_dir).decode()
        logging.info(f"Output: {out.strip()}")
        match = re.search(r"job\(s\) submitted to cluster (\d+).", out)
        assert match, f"Submitting job cluster failed: '{out}'"
        cluster_id = match.group(1)
        category = "main" if is_main_job else "other"
        tools.write_file(self._get_id_file_path(),
                         f"{cluster_id} {job_name} {category} {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}\n",
                         append=True)

    def _submit_dag(self, job_name, dag_file, job_dir):
        submit = ["condor_submit_dag", dag_file]
        logging.info(f"Submitting jobs as DAG: {' '.join(submit)}")
        out = subprocess.check_output(submit, cwd=job_dir).decode()
        logging.info(f"Output: {out.strip()}")
        match = re.search(r"1 job\(s\) submitted to cluster (\d+).", out)
        assert match, f"Submitting DAG job failed: '{out}'"
        cluster_id = match.group(1)
        tools.write_file(self._get_id_file_path(),
                         f"{cluster_id} {job_name} dag {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}\n",
                         append=True)

    def _get_job(self, step, is_last):
        raise NotImplementedError()

    def _get_run_job_body(self):
        task_order = self._get_task_order() if self.batch_mode else " ".join(str(i) for i in self._get_task_order())
        use_scratch_options = ("true", "True") if self.USE_SCRATCH else ("false", "False")
        return tools.fill_template(
            self.RUN_JOB_BODY_TEMPLATE_FILE,
            task_order=task_order,
            exp_path=self.exp.path,
            use_scratch=use_scratch_options[int(self.batch_mode)],
            processes=self.batch_concurrent_processes,
            python=tools.get_python_executable()
        )

    def run_steps(self, steps):
        if len(steps) == 0:
            return
        self.exp.build(write_to_disk=False)
        job_dir = self.prepare_job_dir(steps)
        job_names = [self._get_job_name(step) for step in steps]
        submit_files = []
        for i, step in enumerate(steps):
            job_name = job_names[i]
            submit_file = os.path.join(job_dir, f"{job_name}.sub")
            run_file = os.path.join(job_dir, f"{job_name}.{'py' if self.batch_mode and is_run_step(step) else 'sh'}")
            submit_content = self._get_job_header(step, is_last=(step == steps[-1]))
            run_content = self._get_job_body(step)
            tools.write_file(submit_file, submit_content)
            tools.write_file(run_file, run_content)
            os.chmod(run_file, 0o755)
            submit_files.append(submit_file)
            os.makedirs(os.path.join(job_dir, f"condor-job-logs"), exist_ok=True)
        if len(steps) == 1:
            self._submit_job(job_names[0], submit_files[0], job_dir, is_run_step(steps[0]))
        else:
            assert len(steps) > 1
            exp_name = self.exp.name
            dag_file = os.path.join(job_dir, f"{exp_name}.dag")
            dag_content = ""
            for job_name, submit_file in zip(job_names, submit_files):
                dag_content += f"JOB {job_name} {submit_file}\n"
            for i, parent in enumerate(job_names[:-1]):
                child = job_names[i+1]
                dag_content += f"PARENT {parent} CHILD {child}\n"
            tools.write_file(dag_file, dag_content)
            self._submit_dag(exp_name, dag_file, job_dir)

    def uses_scratch(self):
        return self.USE_SCRATCH

    def check_cluster_status(self, printout=True):
        entries = self._read_id_file()
        if not entries:
            print("There are no tracked cluster jobs.")
            return False
        exists_running_job = False
        for entry in entries:
            cluster_id = entry["cluster_id"]
            name = entry["name"]
            time = entry["time"]
            if printout:
                print(f"\nChecking status for job {name} submitted on {time} (cluster id: {cluster_id})")
            out = subprocess.check_output(["condor_q", cluster_id], stderr=subprocess.STDOUT).decode()
            lines = out.splitlines(keepends=True)
            if len(lines) == 8 and lines[5].startswith("Total for query: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended"):
                if printout:
                    print(f"\nCompleted!\n")
            elif len(lines) == 9:
                if printout:
                    print(f"\nYour job is not completed yet. Details:\n")
                    print(lines[3] + lines[4] + lines[5] + lines[6])
                exists_running_job = True
            else:
                if printout:
                    print("\nSomething went wrong. Details:")
                    print(out)
                exists_running_job = True
        return exists_running_job

    def remove_cluster_jobs(self, confirm=True):
        entries = self._read_id_file()
        if not entries:
            print("There are no tracked cluster jobs.")
        for entry in entries:
            cluster_id = entry["cluster_id"]
            name = entry["name"]
            time = entry["time"]
            out = subprocess.check_output(["condor_q", cluster_id], stderr=subprocess.STDOUT).decode()
            lines = out.splitlines(keepends=True)
            if not (len(lines) == 8 and lines[5].startswith("Total for query: 0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held, 0 suspended")):
                question = f"Are you sure you want to remove job {name} (cluster id: {cluster_id}, submitted: {time})?"
                if confirm and not tools.answer_yes(question):
                    continue
                print(subprocess.check_output(["condor_rm", cluster_id], stderr=subprocess.STDOUT).decode())


def within_condor_job():
    batch_system = os.environ.get("BATCH_SYSTEM")
    return batch_system == "HTCondor" if batch_system else False


def within_slurm_job():
    return os.environ.get("SLURM_JOB_ID") is not None

