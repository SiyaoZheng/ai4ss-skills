# Slurm Job Templates

## Basic CPU Job (Pi 2.0)

```bash
#!/bin/bash
#SBATCH --job-name=myjob
#SBATCH --partition=small        # small: 1-20 cores, shared
#SBATCH -n 20                    # Total cores
#SBATCH --ntasks-per-node=20
#SBATCH --output=%j.out
#SBATCH --error=%j.err

module load gcc
./my_program
```

## CPU Job (Siyuan-1)

```bash
#!/bin/bash
#SBATCH --job-name=myjob
#SBATCH --partition=64c512g      # Siyuan-1 CPU queue
#SBATCH -n 64                    # Total cores
#SBATCH --ntasks-per-node=64     # 64 cores per node
#SBATCH --output=%j.out
#SBATCH --error=%j.err

module load gcc
./my_program
```

## GPU Job (A100 on Siyuan-1)

```bash
#!/bin/bash
#SBATCH --job-name=gpu_job
#SBATCH --partition=a100
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16       # 16 CPU cores per GPU
#SBATCH --gres=gpu:1             # Request 1 GPU
#SBATCH --output=%j.out
#SBATCH --error=%j.err

module load cuda
python train.py
```

## GPU Job (V100 on Pi 2.0)

```bash
#!/bin/bash
#SBATCH --job-name=gpu_job
#SBATCH --partition=dgx2
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=6        # 6 CPU cores per GPU
#SBATCH --gres=gpu:1             # Request 1 GPU
#SBATCH --output=%j.out
#SBATCH --error=%j.err

module load cuda
python train.py
```

## Job Array

```bash
#!/bin/bash
#SBATCH --job-name=array_job
#SBATCH --partition=small
#SBATCH -n 1
#SBATCH --array=1-100%10         # 100 tasks, max 10 concurrent
#SBATCH --output=array_%A_%a.out
#SBATCH --error=array_%A_%a.err

# Use $SLURM_ARRAY_TASK_ID to identify task
python process.py --id $SLURM_ARRAY_TASK_ID
```

## Python Job Script

```bash
#!/bin/bash
#SBATCH --job-name=python_job
#SBATCH --partition=small
#SBATCH -n 4
#SBATCH --output=%j.out
#SBATCH --error=%j.err

module load miniconda3
source activate myenv

python my_script.py
```

## Parallel Python with multiprocessing

```bash
#!/bin/bash
#SBATCH --job-name=parallel_py
#SBATCH --partition=cpu
#SBATCH -n 40
#SBATCH --ntasks-per-node=40
#SBATCH --output=%j.out
#SBATCH --error=%j.err

module load miniconda3
source activate myenv

python -c "import multiprocessing; print(multiprocessing.cpu_count())"
python parallel_script.py
```

## R Job Script

```bash
#!/bin/bash
#SBATCH --job-name=r_job
#SBATCH --partition=small
#SBATCH -n 4
#SBATCH --output=%j.out
#SBATCH --error=%j.err

module load miniconda3
source activate r-env

Rscript my_analysis.R
```

## Parallel R with future/furrr

```bash
#!/bin/bash
#SBATCH --job-name=parallel_r
#SBATCH --partition=cpu
#SBATCH -n 40
#SBATCH --ntasks-per-node=40
#SBATCH --output=%j.out
#SBATCH --error=%j.err

module load miniconda3
source activate r-env

Rscript -e "
library(future)
library(furrr)
plan(multicore, workers = as.integer(Sys.getenv('SLURM_NTASKS')))
# Your parallel code here
"
```
