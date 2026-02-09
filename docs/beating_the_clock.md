!!! WARNING "Made by Bram Vrancke & chatGPT"

    This page was made by Bram Vrancke, for the ULB cluster. you'll have to modify the scripts.

Scripts needed:

- [lyra.beast.gpu.iterative.slurm](./scripts/lyra.beast.gpu.iterative.slurm){:download="lyra.beast.gpu.iterative.slurm"}
- [check_beast_ess.py](./scripts/check_beast_ess.py){:download="check_beast_ess.py"}

The script `lyra.beast.gpu.iterative.slurm` starts a BEAST run with a walltime of 5 days (the maximum walltime on the Lyra cluster).
30 minutes prior to this walltime, the workflow manager (SLURM) signals the script that it's time to evaluate the ESS values of the model parameters.
This signal makes that the ongoing BEAST run is stopped, and that the companion script `check_beast_ess.py` checks the ESS values.
When these are above a user-specified threshold (defaults to 200), the script stops running.
In the other case, the run is continued from the most recent checkpoint file (by default generated every 1.000.000 states).
The above check is again scheduled 30 minutes prior to reaching the new run's walltime. By default, a run is continued at most 4 times (so the analysis runs for a maximum of 5 times the specified walltime, e.g. 25 days).
If log-files of multiple continuations are present, `check_beast_ess.py` combines them and removes the 10% first logged states as burnin.

The slurm-script expects the beast jar-file and `check_beast_ess.py` in the folder `$HOME/biosoft/` on the HPC you're using.

My home folder on the CECI clusters is `/home/ulb/lubies/bvrancke`.
To copy files to `$HOME/biosoft/`, you need to replace `$HOME` by the path that points to your home folder.
In case of doubt, you can find this issuing the following commands:

Log in on the HPC, for example Lyra:

```bash
# on own computer
$ ssh lyra
```

Now print the value of the `$HOME` to screen:

```bash
# on HPC
$ echo $HOME
/home/ulb/lubies/bvrancke
```

Create the folder `biosoft`:

```bash
# on HPC
$ mkdir $HOME/biosoft
```

Copy the BEAST jar-file you want to use and check_beast_ess.py from your computer to `$HOME/biosoft/`.
At the time of writing, I ran BEAST version 10.5.0, and named the BEAST jar file 'beast.10.5.0.jar'.
This is also the default name expected by the slurm script.
Should you decide to use another name, do not forget to also update the variable `beast_version` in lyra.beast.gpu.iterative.slurm (around line 32).

```bash
# on own computer

# In the command below, replace <path to your home folder> by your version of /home/ulb/lubies/bvrancke
$ my_beast_jar="beast.10.5.0.jar"
$ scp "$my_beast_jar" lyra:<path to your home folder>/biosoft
$ scp check_beast_ess.py lyra:<path to your home folder>/biosoft
```

The ESS values are estimated using the ess function from the Python module (or package) [Arviz](https://www.arviz.org/en/latest/).
The slurm-script expects this to be installed in a virtual environment that is named 'venv_beast'.
To do so, first load the core Python module on the HPC. In this example, I've used the most recent version that was available on Lyra when setting this up.

When installing Python modules, they may depend on functionalities provided by other modules.
If this is the case, these other modules, which are referred to as dependencies, will also need to be installed.
It is advised to use the optimally compiled versions of modules/dependencies that are provided on the HPC.
To make sure these are available to the virtual environment, specify the flag
`--system-site-packages` when creating the virtual environment.
This flag updates the include-system-site-packages setting that can be found in the configuration file `$HOME/venv_beast/pyvenv.cfg` from 'false' to 'true.

```bash
# on HPC
$ module load Python/3.11.3-GCCcore-12.3.0
$ python -m venv --system-site-packages $HOME/venv_beast

# check whether 'include-system-site-packages' is correctly set to true:
$ vim $HOME/venv_beast/pyvenv.cfg
```

Now activate the virtual environment and install arviz.

```bash
# on HPC
$ source $HOME/venv_beast/bin/activate
(venv_beast) $ pip install arviz # let pip decide for dependencies already in system
# after installing, confirm it works:
(venv_beast) $ python -c "import arviz; print(arviz.__version__)"
```

One important note is that, for the script to find the generated log and checkpoint files, it is expected that the following naming convention is adhered to when setting up the XML for the BEAST analysis:

- XML file name:
  <XMLbaseName\>.r[0-9]+.xml
- log file name:
  <XMLbaseName\>.r[0-9]+.log

The names of the checkpoint file(s), log- and trees files and XMLs for the continued runs are automatically taken care of by the slurm-script.

**USAGE INSTRUCTIONS**

To submit a job:

```
# on HPC
$ XML=your_analysis.xml
$ sbatch --export=XML=$XML,WD=`pwd` \
--output=${XML%%.xml}.o --error=${XML%%.xml}.e \
--job-name=${XML%%.xml} lyra.beast.gpu.iterative.slurm
```

_User-configurable parameters:_

| variable                         |                                             |
| -------------------------------- | ------------------------------------------- |
| MAX_ITERATIONS=5                 | # Maximum number of iterations              |
| INSTANCE=1                       | # GPU instance to use                       |
| saveEveryState=1000000           | # BEAST saves state every N MCMC iterations |
| beast_version="beast.10.5.0.jar" | # BEAST version to use                      |
| minimum_required_ESS=200         | # Adjust as you see fit                     |

Finally, should you find this useful, you are encouraged to acknowledge Arviz by citing it using [https://doi.org/10.21105/joss.01143](https://doi.org/10.21105/joss.01143).
