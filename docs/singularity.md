# Singularity ~ Apptainer

!!! abstract "One sentence abstraction"
    Singularity is a container platform designed for high-performance computing (HPC) that packages entire software environments into portable, reproducible images, allowing you to run applications seamlessly across different systems

Singularity was created to run complex applications on HPC clusters in a simple, portable, and reproducible way. 
First developed at Lawrence Berkeley National Laboratory, it quickly became popular at other HPC sites, academic sites, and beyond. 
The user base continues to expand, with Singularity now used across industry and academia in many areas of work.

!!! Tip
    Singularity is the tool to run on HPCs, including ours! As you don't need root acces to run it (unlike [docker](./docker.md)).

## Why Singularity?
Many container platforms are available, but Singularity is focused on:

-	Verifiable reproducibility and security, using cryptographic signatures, an immutable container image format, and in-memory decryption.
-	Integration over isolation by default. Easily make use of GPUs, high speed networks, parallel filesystems on a cluster or server by default.
-	Mobility of compute. The single file SIF container format is easy to transport and share.
-	A simple, effective security model. You are the same user inside a container as outside, and cannot gain additional privilege on the host system by default. 


## Singularity Installation
Singularity is available on most HPCs, but if you want to install it on your own machine, you can follow the instructions on the [official website](https://apptainer.org/docs/admin/main/installation.html).

!!! info
    Singularity is difficult to install on ARM chips (Apple silicon), haven\'t looked into it in detail. 

## In depth class
For a more in depth class for users with 0 experience, consider the [course from SIB](https://sib-swiss.github.io/containers-introduction-training/latest/course_material/apptainer/).
<iframe width="560" height="315" src="https://www.youtube.com/embed/d3kxtzUutjk" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

## Cheatsheet
### Downloading 
Singularity can take several image formats (e.g. a `docker` image), and convert them into it’s own `.sif` format. Unlike `docker` this image doesn’t live in a local image cache, but it’s stored as an actual file.

### From docker
You can pull them from docker hub with `singularity pull`. The syntax is:
```bash
singularity pull docker://[USER NAME]/[IMAGE NAME]:[TAG]
```

### From web/biocontainer
Given that singularity images are just files, one can download with `wget`:
```bash
wget https://depot.galaxyproject.org/singularity/bracken:2.7--py39hc16433a_0
```

### Running files
These `.sif` files can be run as standalone executables:
```bash
./ubuntu-figlet_v3.sif
```

Singularity is also different from Docker in the way it handles mounting. By default, Singularity binds your home directory and a number of paths in the root directory to the container. This results in behaviour that is almost like if you are working on the directory structure of the host.

### Running with dir
It depends on the singularity settings whether most directories are mounted by default to the container. If your directory is not mounted, you can do that with the `--bind` option of `singularity exec`:

```bash
singularity exec --bind /my/dir/to/mount/ [IMAGE NAME].sif [COMMAND]
```

Running the command `pwd` (full name of current working directory) will therefore result in a path on the host machine:

```bash
./ubuntu-figlet_v3.sif pwd
```

### Running interactive
If you want to debug or inspect an image, it can be helpful to have a shell inside the container. You can do that with `singularity shell`:

```bash
singularity shell ubuntu-figlet_v3.sif
```

# Example 

This is how Joon runs his beast analyses on the HPC. 
```bash 
#!/bin/bash
#SBATCH --clusters=genius
#SBATCH --account="lp_phylogeo_inf_gpu"
#SBATCH --mail-type="END,FAIL,TIME_LIMIT"
#SBATCH --mail-user="joon.klaps@kuleuven.be"
#SBATCH --partition=gpu_p100_long
#SBATCH --gres=gpu:2
#SBATCH --gpus-per-node=2
#SBATCH --ntasks=18
#SBATCH --mem 170000M
#SBATCH --time="168:00:00"

####################################
##### Run a beast analysis ######
####################################

#### How to run: ####
# sbatch --export=ALL,ARGS='' gpu_example.slurm

# write a function that catches any errors
abort()
{
    echo >&2 '
***************
*** ABORTED ***
***************
'
    echo "An error occurred. Exiting..." >&2
    exit 1
}

set -e
trap 'abort' 0

# write some cluster metadata to the error and output files
hostname >&2
echo $0 >&2
printf START >&2; uptime >&2
date >&2

module load cluster/genius/gpu_p100_long
module load CUDA

singularity exec --nv -B $VSC_DATA:$VSC_DATA -B $VSC_STAGING:$VSC_STAGING -B $VSC_SCRATCH:$VSC_SCRATCH -B $VSC_HOME:$VSC_HOME -B $PWD docker://jklaps/beast-beagle-cuda:v10.5.0-beta5 \
    beast \
    -beagle_GPU \
    -beagle_order 1 \
    -working \
    -save_stem Coronaviridae \
    Coronaviridae.xml \
    > Coronaviridae.beast.out

# write some cluster metadata to the error and output files
printf END >&2; uptime >&2

trap : 0

echo >&2 '
************
*** DONE ***
************
'

```
