# Python 与 R 环境配置指南 | Python & R Environment Setup Guide

> SJTU HPC 计算社会科学工作流完整参考 | Complete Reference for Computational Social Science Workflows

---

## 目录 | Table of Contents

1. [Conda 环境管理 | Conda Environment Management](#conda-环境管理--conda-environment-management)
2. [Python 环境配置 | Python Environment Setup](#python-环境配置--python-environment-setup)
3. [R 环境配置 | R Environment Setup](#r-环境配置--r-environment-setup)
4. [Jupyter 使用 | Jupyter Usage](#jupyter-使用--jupyter-usage)
5. [环境迁移 | Environment Migration](#环境迁移--environment-migration)
6. [常见问题 | Troubleshooting](#常见问题--troubleshooting)
7. [计算社会科学工作流 | Computational Social Science Workflows](#计算社会科学工作流--computational-social-science-workflows)

---

## Conda 环境管理 | Conda Environment Management

### 加载 Conda 模块 | Loading Conda Module

不同集群使用不同的 Conda 模块。
Different clusters use different Conda modules.

```bash
# 思源一号 | Siyuan-1 (x86_64)
module load miniconda3/4.10.3

# Pi 2.0 (x86_64)
module load miniconda3/4.8.2

# ARM 集群 | ARM Cluster (aarch64)
module load conda4aarch64/1.0.0-gcc-4.8.5
```

### 常用命令 | Common Commands

```bash
# 查看已安装包 | List installed packages
conda list

# 查看所有环境 | List all environments
conda env list

# 创建新环境 | Create new environment
conda create -n env_name python=3.10

# 激活环境 | Activate environment
source activate env_name
# 或 | or
conda activate env_name

# 退出环境 | Deactivate environment
conda deactivate

# 搜索包 | Search for package
conda search package_name -c conda-forge

# 安装包 | Install package
conda install package_name -c conda-forge -n env_name

# 删除包 | Remove package
conda remove -n env_name package_name

# 删除整个环境 | Remove entire environment
conda remove -n env_name --all
```

### 初始化配置 | Initial Configuration

```bash
# 禁用自动激活 base 环境（强烈推荐）
# Disable auto-activation of base environment (strongly recommended)
conda config --set auto_activate_base false

# 添加常用 channel | Add common channels
conda config --add channels conda-forge
conda config --set channel_priority strict

# 查看配置 | View configuration
conda config --show
```

---

## Python 环境配置 | Python Environment Setup

### 1. 创建虚拟环境 | Creating Virtual Environment

```bash
# 方法一：使用 Conda | Method 1: Using Conda
module load miniconda3/4.10.3
conda create -n myenv python=3.10 -y
source activate myenv

# 方法二：使用 venv（系统 Python）| Method 2: Using venv (system Python)
module load python/3.10.4
python -m venv ~/envs/myenv
source ~/envs/myenv/bin/activate
```

### 2. 安装包：Conda vs Pip | Installing Packages: Conda vs Pip

**推荐策略 | Recommended Strategy:**
- 优先使用 Conda 安装（更好的依赖解析）
- Use Conda first (better dependency resolution)
- Pip 用于 Conda 没有的包
- Use Pip for packages not in Conda

```bash
# Conda 安装 | Conda install
conda install numpy pandas scikit-learn -c conda-forge

# Pip 安装（在 Conda 环境中）| Pip install (within Conda env)
pip install transformers datasets

# 从 requirements.txt 安装 | Install from requirements.txt
pip install -r requirements.txt

# 导出依赖 | Export dependencies
pip freeze > requirements.txt
conda env export > environment.yaml
```

### 3. 注册为 Jupyter Kernel | Register as Jupyter Kernel

```bash
# 安装 ipykernel | Install ipykernel
conda install ipykernel -y

# 注册 kernel | Register kernel
python -m ipykernel install --user --name myenv --display-name "Python (myenv)"

# 查看已注册 kernel | List registered kernels
jupyter kernelspec list

# 删除 kernel | Remove kernel
jupyter kernelspec remove myenv
```

### 4. GPU 环境配置 | GPU Environment Setup

```bash
# 思源一号 GPU 节点 | Siyuan-1 GPU nodes (A100)
module load miniconda3/4.10.3
module load cuda/11.8.0

# 创建 GPU 环境 | Create GPU environment
conda create -n gpu_env python=3.10 -y
source activate gpu_env

# 安装 CUDA 工具包 | Install CUDA toolkit
conda install cudatoolkit=11.8 cudnn=8.6 -c conda-forge

# 安装 PyTorch (GPU) | Install PyTorch (GPU)
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia

# 安装 TensorFlow (GPU) | Install TensorFlow (GPU)
pip install tensorflow[and-cuda]

# 安装 JAX (GPU) | Install JAX (GPU)
pip install "jax[cuda12]"

# 验证 GPU | Verify GPU
python -c "import torch; print(torch.cuda.is_available())"
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

### 5. 并行计算 | Parallel Computing

```python
# multiprocessing - CPU 并行 | CPU parallelism
from multiprocessing import Pool
import os

def process_item(x):
    return x ** 2

if __name__ == '__main__':
    # 使用环境变量控制进程数 | Control process count via env var
    n_workers = int(os.environ.get('SLURM_CPUS_PER_TASK', 4))
    with Pool(n_workers) as p:
        results = p.map(process_item, range(1000))
```

```python
# mpi4py - MPI 并行（跨节点）| MPI parallelism (cross-node)
# 安装 | Install: conda install mpi4py openmpi -c conda-forge

from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if rank == 0:
    data = list(range(100))
    chunks = [data[i::size] for i in range(size)]
else:
    chunks = None

local_data = comm.scatter(chunks, root=0)
local_result = [x ** 2 for x in local_data]
results = comm.gather(local_result, root=0)

if rank == 0:
    flat_results = [item for chunk in results for item in chunk]
    print(f"Total results: {len(flat_results)}")
```

```python
# numba - JIT 编译加速 | JIT compilation acceleration
# 安装 | Install: conda install numba -c conda-forge

from numba import jit, prange
import numpy as np

@jit(nopython=True, parallel=True)
def parallel_sum(arr):
    total = 0.0
    for i in prange(arr.shape[0]):
        total += arr[i]
    return total

arr = np.random.rand(10_000_000)
result = parallel_sum(arr)
```

```python
# cupy - GPU 数组运算 | GPU array operations
# 安装 | Install: pip install cupy-cuda11x

import cupy as cp
import numpy as np

# CPU -> GPU
x_cpu = np.random.rand(10000, 10000).astype(np.float32)
x_gpu = cp.asarray(x_cpu)

# GPU 计算 | GPU computation
y_gpu = cp.dot(x_gpu, x_gpu.T)

# GPU -> CPU
y_cpu = cp.asnumpy(y_gpu)
```

---

## R 环境配置 | R Environment Setup

### 1. 使用 Conda 安装 R | Install R with Conda

```bash
# 创建 R 环境 | Create R environment
module load miniconda3/4.10.3
conda create -n r_env r-essentials r-base=4.3 -c conda-forge -y
source activate r_env

# 安装常用包 | Install common packages
conda install -c conda-forge \
    r-tidyverse \
    r-data.table \
    r-devtools \
    r-rmarkdown \
    r-shiny
```

### 2. 注册为 Jupyter Kernel | Register as Jupyter Kernel

```bash
# 在 R 环境中 | In R environment
source activate r_env

# 启动 R | Start R
R
```

```r
# 在 R 中执行 | Execute in R
install.packages('IRkernel')
IRkernel::installspec(name = 'r_env', displayname = 'R (r_env)')

# 验证 | Verify
IRkernel::installspec()
```

### 3. R 并行计算 | R Parallel Computing

```r
# future + furrr - 现代并行框架 | Modern parallel framework
# 安装 | Install: conda install -c conda-forge r-future r-furrr

library(future)
library(furrr)

# 设置并行 workers | Set parallel workers
n_cores <- as.integer(Sys.getenv("SLURM_CPUS_PER_TASK", unset = "4"))
plan(multisession, workers = n_cores)

# 并行 map | Parallel map
results <- future_map(1:1000, ~ .x^2)

# 并行带进度条 | Parallel with progress bar
library(progressr)
handlers(global = TRUE)
with_progress({
  p <- progressor(steps = 100)
  results <- future_map(1:100, ~{
    p()
    Sys.sleep(0.1)
    .x^2
  })
})

# 重置为顺序执行 | Reset to sequential
plan(sequential)
```

```r
# parallel - 基础并行包 | Base parallel package
library(parallel)

n_cores <- detectCores() - 1
cl <- makeCluster(n_cores)

# 并行 apply | Parallel apply
results <- parLapply(cl, 1:1000, function(x) x^2)

stopCluster(cl)
```

```r
# foreach + doParallel - 循环并行 | Loop parallelism
library(foreach)
library(doParallel)

cl <- makeCluster(4)
registerDoParallel(cl)

results <- foreach(i = 1:100, .combine = 'c') %dopar% {
  i^2
}

stopCluster(cl)
```

### 4. HPC Studio RStudio Server | HPC Studio RStudio Server

1. 登录 HPC Studio: https://studio.hpc.sjtu.edu.cn
2. 选择 "Interactive Apps" > "RStudio Server"
3. 配置资源：
   - Partition: 选择合适的分区 | Select appropriate partition
   - Cores: CPU 核心数 | Number of CPU cores
   - Memory: 内存大小 | Memory size
   - Time: 运行时长 | Runtime duration
4. 点击 "Launch" 启动 | Click "Launch" to start

**在 RStudio 中使用 Conda 环境 | Using Conda env in RStudio:**

```r
# 在 .Rprofile 中设置 | Set in .Rprofile
Sys.setenv(RETICULATE_PYTHON = "~/miniconda3/envs/r_env/bin/python")

# 或在脚本中 | Or in script
library(reticulate)
use_condaenv("r_env", required = TRUE)
```

---

## Jupyter 使用 | Jupyter Usage

### 1. 预置环境 | Pre-installed Environments

HPC Studio 提供预置环境 | HPC Studio provides pre-installed environments:

```bash
# 查看可用 kernel | List available kernels
jupyter kernelspec list

# 预置环境包括 | Pre-installed environments include:
# - Python 3 (ipykernel)
# - PyTorch (各版本 | various versions)
# - TensorFlow (各版本 | various versions)
# - R (IRkernel)
```

### 2. 自定义 Kernel 注册 | Custom Kernel Registration

**Python Kernel:**

```bash
source activate myenv
pip install ipykernel
python -m ipykernel install --user --name myenv --display-name "My Python Env"
```

**R Kernel:**

```r
# 在 R 中 | In R
install.packages('IRkernel')
IRkernel::installspec(name = 'my_r', displayname = 'My R Env')
```

**Julia Kernel:**

```julia
# 在 Julia 中 | In Julia
using Pkg
Pkg.add("IJulia")
using IJulia
installkernel("Julia", "--project=@.")
```

### 3. HPC Studio Jupyter 启动 | HPC Studio Jupyter Launch

1. 登录 https://studio.hpc.sjtu.edu.cn
2. 选择 "Interactive Apps" > "Jupyter"
3. 配置：
   - Partition: `cpu` / `dgx2` / `a100` 等
   - Cores: 建议 4-8 | Recommended 4-8
   - Memory: 建议 16-32GB | Recommended 16-32GB
   - GPU: 如需要 | If needed
4. 启动后选择你的 kernel | Select your kernel after launch

### 4. 命令行启动 Jupyter | Command Line Jupyter Launch

```bash
# 申请计算节点 | Request compute node
srun -p cpu -n 1 -c 4 --mem=16G --pty bash

# 启动 Jupyter | Start Jupyter
module load miniconda3/4.10.3
source activate myenv
jupyter lab --no-browser --port=8888 --ip=0.0.0.0

# 在本地建立 SSH 隧道 | Create SSH tunnel locally
# ssh -L 8888:compute_node:8888 username@login.hpc.sjtu.edu.cn
```

---

## 环境迁移 | Environment Migration

### Pi 2.0 到思源一号 | Pi 2.0 to Siyuan-1

```bash
# === 在 Pi 2.0 上 | On Pi 2.0 ===
module load miniconda3/4.8.2
source activate old_env

# 方法一：导出完整环境 | Method 1: Export full environment
conda env export > env_full.yaml

# 方法二：仅导出手动安装的包（推荐）| Method 2: Export only manually installed (recommended)
conda env export --from-history > env_minimal.yaml

# 复制到思源一号 | Copy to Siyuan-1
scp env_minimal.yaml username@sylogin.hpc.sjtu.edu.cn:~/

# === 在思源一号上 | On Siyuan-1 ===
module load miniconda3/4.10.3

# 创建环境 | Create environment
conda env create -f env_minimal.yaml

# 如果有冲突，手动创建 | If conflicts, create manually
conda create -n new_env python=3.10 -y
source activate new_env
conda install --file packages.txt -c conda-forge
```

### 跨架构迁移（x86 到 ARM）| Cross-Architecture Migration (x86 to ARM)

```bash
# ARM 架构不能直接使用 x86 的环境文件
# ARM architecture cannot directly use x86 environment files

# === 在 x86 集群上 | On x86 cluster ===
conda list --export > packages.txt
# 手动编辑，移除版本号 | Manually edit to remove version numbers

# === 在 ARM 集群上 | On ARM cluster ===
module load conda4aarch64/1.0.0-gcc-4.8.5
conda create -n arm_env python=3.10 -y
source activate arm_env

# 逐个安装，处理兼容性 | Install one by one, handle compatibility
while read package; do
    conda install -c conda-forge $package || pip install $package || echo "Failed: $package"
done < packages.txt
```

---

## 常见问题 | Troubleshooting

### 1. auto_activate_base 导致问题 | auto_activate_base Issues

**症状 | Symptoms:**
- 登录时自动进入 base 环境
- 与其他模块冲突
- 作业脚本中环境混乱

**解决方案 | Solution:**

```bash
# 禁用自动激活 | Disable auto-activation
conda config --set auto_activate_base false

# 清理 .bashrc 中的 conda init 代码 | Clean conda init from .bashrc
# 删除 # >>> conda initialize >>> 到 # <<< conda initialize <<< 之间的内容
# Remove content between # >>> conda initialize >>> and # <<< conda initialize <<<

# 重新登录 | Re-login
exit
# 重新 SSH 连接 | SSH reconnect
```

### 2. 包冲突解决 | Package Conflict Resolution

```bash
# 查看冲突详情 | View conflict details
conda install package_name --dry-run

# 使用 mamba 加速依赖解析 | Use mamba for faster resolution
conda install mamba -c conda-forge
mamba install conflicting_package

# 创建新环境避免冲突 | Create new environment to avoid conflicts
conda create -n fresh_env python=3.10 package1 package2 -c conda-forge

# 使用 pip 作为备选 | Use pip as alternative
pip install package_name --no-deps  # 不安装依赖 | Without dependencies
```

### 3. GPU 版本兼容性 | GPU Version Compatibility

```bash
# 检查 CUDA 版本 | Check CUDA version
nvidia-smi  # 驱动支持的最高 CUDA 版本 | Max CUDA version supported by driver
nvcc --version  # 当前 CUDA 工具包版本 | Current CUDA toolkit version

# 常见组合 | Common combinations (思源一号 Siyuan-1):
# CUDA 11.8 + PyTorch 2.0+ + cuDNN 8.6
# CUDA 12.1 + PyTorch 2.1+ + cuDNN 8.9

# 验证 PyTorch CUDA | Verify PyTorch CUDA
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda}')
print(f'cuDNN version: {torch.backends.cudnn.version()}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
"

# 验证 TensorFlow CUDA | Verify TensorFlow CUDA
python -c "
import tensorflow as tf
print(f'TensorFlow: {tf.__version__}')
print(f'GPU devices: {tf.config.list_physical_devices(\"GPU\")}')
"
```

### 4. Jupyter Kernel 找不到 | Jupyter Kernel Not Found

```bash
# 检查 kernel 位置 | Check kernel location
jupyter kernelspec list

# 手动安装到正确位置 | Manually install to correct location
python -m ipykernel install --user --name myenv

# 检查 kernel.json | Check kernel.json
cat ~/.local/share/jupyter/kernels/myenv/kernel.json

# 修复 Python 路径 | Fix Python path
{
  "argv": [
    "/home/username/miniconda3/envs/myenv/bin/python",
    "-m",
    "ipykernel_launcher",
    "-f",
    "{connection_file}"
  ],
  "display_name": "Python (myenv)",
  "language": "python"
}
```

### 5. 内存不足 | Out of Memory

```bash
# 增加 SLURM 内存申请 | Increase SLURM memory request
#SBATCH --mem=64G

# Python 中监控内存 | Monitor memory in Python
import psutil
print(f"Memory: {psutil.virtual_memory().percent}%")

# 使用 memory_profiler | Use memory_profiler
pip install memory_profiler
python -m memory_profiler script.py

# R 中监控内存 | Monitor memory in R
pryr::mem_used()
```

---

## 计算社会科学工作流 | Computational Social Science Workflows

### 1. 文本分析环境 | Text Analysis Environment

```bash
# 创建 NLP 环境 | Create NLP environment
conda create -n nlp python=3.10 -y
source activate nlp

# 安装 NLP 包 | Install NLP packages
pip install transformers datasets tokenizers
pip install sentencepiece protobuf
pip install jieba snownlp  # 中文 NLP | Chinese NLP
pip install spacy
python -m spacy download en_core_web_sm
python -m spacy download zh_core_web_sm

# 安装 LLM 相关 | Install LLM related
pip install openai anthropic langchain
pip install sentence-transformers faiss-cpu
```

**文本分析示例 | Text Analysis Example:**

```python
# text_analysis.py
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import os

# 情感分析 | Sentiment analysis
classifier = pipeline("sentiment-analysis", model="bert-base-chinese")

def analyze_batch(texts):
    return classifier(texts, truncation=True, max_length=512)

# 并行处理大数据 | Parallel processing for large data
def parallel_analyze(df, text_col, n_workers=None):
    if n_workers is None:
        n_workers = int(os.environ.get('SLURM_CPUS_PER_TASK', 4))

    texts = df[text_col].tolist()
    batch_size = 32
    batches = [texts[i:i+batch_size] for i in range(0, len(texts), batch_size)]

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        results = list(executor.map(analyze_batch, batches))

    flat_results = [item for batch in results for item in batch]
    return flat_results

# 使用示例 | Usage example
if __name__ == '__main__':
    df = pd.read_csv('social_media_posts.csv')
    results = parallel_analyze(df, 'text')
    df['sentiment'] = [r['label'] for r in results]
    df['confidence'] = [r['score'] for r in results]
    df.to_csv('analyzed_posts.csv', index=False)
```

### 2. 网络分析环境 | Network Analysis Environment

```bash
conda create -n network python=3.10 -y
source activate network

conda install -c conda-forge networkx igraph python-igraph
pip install graph-tool  # 需要特殊安装 | Requires special installation
pip install node2vec karateclub
pip install pyvis  # 可视化 | Visualization
```

**网络分析示例 | Network Analysis Example:**

```python
# network_analysis.py
import networkx as nx
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

def compute_centrality(G):
    """计算多种中心性指标 | Compute multiple centrality metrics"""
    return {
        'degree': nx.degree_centrality(G),
        'betweenness': nx.betweenness_centrality(G),
        'closeness': nx.closeness_centrality(G),
        'eigenvector': nx.eigenvector_centrality(G, max_iter=1000)
    }

def analyze_network(edge_file):
    # 读取边列表 | Read edge list
    edges = pd.read_csv(edge_file)
    G = nx.from_pandas_edgelist(edges, 'source', 'target')

    # 基本统计 | Basic statistics
    stats = {
        'nodes': G.number_of_nodes(),
        'edges': G.number_of_edges(),
        'density': nx.density(G),
        'clustering': nx.average_clustering(G)
    }

    # 中心性 | Centrality
    centrality = compute_centrality(G)

    # 社区检测 | Community detection
    from networkx.algorithms import community
    communities = community.louvain_communities(G)

    return stats, centrality, communities
```

### 3. 统计建模环境 (R) | Statistical Modeling Environment (R)

```bash
conda create -n r_stats r-base=4.3 r-essentials -c conda-forge -y
source activate r_stats

# 安装统计包 | Install statistical packages
conda install -c conda-forge \
    r-lme4 r-brms r-rstanarm \  # 多层次模型 | Multilevel models
    r-lavaan r-semtools \        # SEM
    r-marginaleffects \          # 边际效应 | Marginal effects
    r-modelsummary \             # 模型输出 | Model output
    r-fixest                     # 固定效应 | Fixed effects
```

**统计建模示例 | Statistical Modeling Example:**

```r
# statistical_modeling.R
library(tidyverse)
library(lme4)
library(brms)
library(marginaleffects)
library(modelsummary)
library(future)
library(furrr)

# 设置并行 | Setup parallel
n_cores <- as.integer(Sys.getenv("SLURM_CPUS_PER_TASK", unset = "4"))
plan(multisession, workers = n_cores)

# 读取数据 | Read data
data <- read_csv("survey_data.csv")

# 多层次模型 | Multilevel model
model_ml <- lmer(
  outcome ~ treatment + control1 + control2 + (1 | group),
  data = data
)

# 贝叶斯模型（使用多核）| Bayesian model (using multiple cores)
model_bayes <- brm(
  outcome ~ treatment + control1 + control2 + (1 | group),
  data = data,
  family = gaussian(),
  chains = 4,
  cores = n_cores,
  iter = 2000
)

# 边际效应 | Marginal effects
mfx <- marginaleffects(model_ml)

# 模型比较表 | Model comparison table
modelsummary(
  list("ML" = model_ml, "Bayes" = model_bayes),
  output = "results/model_comparison.html"
)
```

### 4. 机器学习工作流 | Machine Learning Workflow

```bash
conda create -n ml python=3.10 -y
source activate ml

# 核心 ML 包 | Core ML packages
conda install -c conda-forge \
    scikit-learn \
    xgboost \
    lightgbm \
    catboost

# 深度学习 | Deep learning
conda install pytorch torchvision pytorch-cuda=11.8 -c pytorch -c nvidia

# AutoML
pip install auto-sklearn  # 需要较多依赖 | Requires many dependencies
pip install optuna  # 超参数优化 | Hyperparameter optimization
```

**机器学习示例 | Machine Learning Example:**

```python
# ml_workflow.py
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier
import optuna
from joblib import parallel_backend
import os

# 获取可用 CPU 数 | Get available CPUs
n_jobs = int(os.environ.get('SLURM_CPUS_PER_TASK', -1))

def objective(trial):
    """Optuna 目标函数 | Optuna objective function"""
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'max_depth': trial.suggest_int('max_depth', 3, 20),
        'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
        'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
        'n_jobs': n_jobs
    }

    model = RandomForestClassifier(**params, random_state=42)
    scores = cross_val_score(model, X_train, y_train, cv=5, n_jobs=n_jobs)
    return scores.mean()

# 超参数搜索 | Hyperparameter search
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100, n_jobs=1)  # 外层串行，内层并行

print(f"Best params: {study.best_params}")
print(f"Best score: {study.best_value}")
```

### 5. 完整 SLURM 作业脚本 | Complete SLURM Job Scripts

**Python 作业 | Python Job:**

```bash
#!/bin/bash
#SBATCH --job-name=css_analysis
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

# 加载模块 | Load modules
module load miniconda3/4.10.3

# 激活环境 | Activate environment
source activate nlp

# 设置环境变量 | Set environment variables
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK

# 运行脚本 | Run script
python text_analysis.py --input data/corpus.csv --output results/

echo "Job completed at $(date)"
```

**R 作业 | R Job:**

```bash
#!/bin/bash
#SBATCH --job-name=r_analysis
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

# 加载模块 | Load modules
module load miniconda3/4.10.3

# 激活 R 环境 | Activate R environment
source activate r_stats

# 设置 R 并行 | Set R parallel
export MC_CORES=$SLURM_CPUS_PER_TASK

# 运行 R 脚本 | Run R script
Rscript statistical_modeling.R

echo "Job completed at $(date)"
```

**GPU 作业 | GPU Job:**

```bash
#!/bin/bash
#SBATCH --job-name=gpu_training
#SBATCH --partition=a100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=48:00:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

# 加载模块 | Load modules
module load miniconda3/4.10.3
module load cuda/11.8.0

# 激活环境 | Activate environment
source activate gpu_env

# 验证 GPU | Verify GPU
nvidia-smi
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"

# 运行训练 | Run training
python train_model.py \
    --data_dir data/ \
    --output_dir models/ \
    --batch_size 32 \
    --epochs 100

echo "Job completed at $(date)"
```

---

## 附录：快速参考 | Appendix: Quick Reference

### 模块加载 | Module Loading

| 集群 Cluster | Conda 模块 | CUDA 模块 |
|--------------|-----------|-----------|
| 思源一号 Siyuan-1 | `miniconda3/4.10.3` | `cuda/11.8.0`, `cuda/12.1.0` |
| Pi 2.0 | `miniconda3/4.8.2` | `cuda/11.0.3` |
| ARM | `conda4aarch64/1.0.0-gcc-4.8.5` | N/A |

### 常用环境变量 | Common Environment Variables

```bash
# SLURM 自动设置 | SLURM auto-set
$SLURM_CPUS_PER_TASK    # 分配的 CPU 核心数 | Allocated CPU cores
$SLURM_MEM_PER_NODE     # 分配的内存 | Allocated memory
$SLURM_JOB_ID           # 作业 ID | Job ID
$SLURM_SUBMIT_DIR       # 提交目录 | Submit directory

# 手动设置优化 | Manual optimization
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK
export NUMEXPR_MAX_THREADS=$SLURM_CPUS_PER_TASK
```

### 有用链接 | Useful Links

- SJTU HPC 文档 | SJTU HPC Docs: https://docs.hpc.sjtu.edu.cn
- HPC Studio: https://studio.hpc.sjtu.edu.cn
- Conda 文档 | Conda Docs: https://docs.conda.io
- SLURM 文档 | SLURM Docs: https://slurm.schedmd.com/documentation.html

---

*最后更新 | Last Updated: 2025-01*
