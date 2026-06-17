# SJTU HPC Troubleshooting Reference

SJTU HPC 常见问题排查指南

---

## Table of Contents

1. [Account Issues / 账户问题](#account-issues--账户问题)
2. [Login Issues / 登录问题](#login-issues--登录问题)
3. [Job Issues / 作业问题](#job-issues--作业问题)
4. [Software Issues / 软件问题](#software-issues--软件问题)
5. [Storage Issues / 存储问题](#storage-issues--存储问题)
6. [Billing Issues / 欠费问题](#billing-issues--欠费问题)
7. [Publication Acknowledgment / 论文致谢](#publication-acknowledgment--论文致谢)
8. [Getting Help / 获取帮助](#getting-help--获取帮助)

---

## Account Issues / 账户问题

### Account Application / 账户申请

**How to Apply / 如何申请:**

1. **Faculty/Staff accounts / 教职工账户:**
   - Apply via 交我办 (my.sjtu.edu.cn) → "高性能计算服务"
   - 通过交我办 (my.sjtu.edu.cn) 申请 → "高性能计算服务"
   - Account activated within 2 business days / 2个工作日内开通

2. **Student sub-accounts / 学生子账户:**
   - Students get FREE sub-accounts under faculty advisor accounts
   - 学生在导师账户下获得免费子账户
   - Account format / 账户格式: `advisor_username-student_name` (e.g., `advisor-user`)
   - Contact your advisor to create sub-account / 联系导师创建子账户

**Account Types / 账户类型:**

| Type / 类型 | Format / 格式 | Billing / 计费 |
|-------------|---------------|----------------|
| Faculty account / 教职工账户 | `username` | Independent / 独立计费 |
| Student sub-account / 学生子账户 | `advisor-student` | Under advisor account / 导师账户下 |

---

## Login Issues / 登录问题

### Connection Failed / 连接失败

**Symptoms / 症状:**
```
ssh: connect to host sylogin.hpc.sjtu.edu.cn port 22: Connection timed out
ssh: connect to host sylogin.hpc.sjtu.edu.cn port 22: Network is unreachable
```

**Diagnosis / 诊断:**
```bash
# Step 1: Check network connectivity / 检查网络连通性
ping sylogin.hpc.sjtu.edu.cn

# Step 2: Check if SSH port is reachable / 检查SSH端口是否可达
nc -zv sylogin.hpc.sjtu.edu.cn 22

# Step 3: Verbose SSH connection / SSH详细连接信息
ssh -vvv username@sylogin.hpc.sjtu.edu.cn
```

**Solutions / 解决方案:**

| Issue | Solution |
|-------|----------|
| Public network access / 公网访问 | Direct access, NO VPN required / 直接访问，无需VPN |
| Campus network issues / 校园网问题 | Try switching to mobile data / 尝试切换到移动数据 |
| System maintenance / 系统维护 | Check WeChat official account "交我算" for announcements / 查看公众号"交我算"是否有停机通知 |
| DNS resolution failure / DNS解析失败 | Try IP directly: `ssh username@202.120.58.229` |

**Login Nodes / 登录节点:**
- Siyuan-1 / 思源一号: `sylogin.hpc.sjtu.edu.cn`
- Pi 2.0: `login.hpc.sjtu.edu.cn`
- Data transfer / 数据传输: `data.hpc.sjtu.edu.cn` / `sydata.hpc.sjtu.edu.cn`

---

### Password Error & Account Blocked / 密码错误被封禁

**Symptoms / 症状:**
```
Permission denied (publickey,password).
Connection closed by 202.120.58.229 port 22
ssh_exchange_identification: Connection closed by remote host
```

**Cause / 原因:**
- fail2ban service blocks IP after multiple failed password attempts
- fail2ban 服务在多次密码错误后临时封禁IP

**Solutions / 解决方案:**

1. **Wait 1 hour / 等待1小时** - The ban automatically expires
   封禁自动解除

2. **Contact admin / 联系管理员**
   ```
   Email: hpc@sjtu.edu.cn
   Subject: Account blocked - request unblock / 账号封禁解除申请
   Content: Include your username and IP address / 包含用户名和IP地址
   ```

3. **Use SSH key authentication / 使用SSH密钥认证** (recommended / 推荐)
   ```bash
   # Generate SSH key / 生成SSH密钥
   ssh-keygen -t ed25519 -C "your_email@sjtu.edu.cn"

   # Copy to server / 复制到服务器
   ssh-copy-id username@sylogin.hpc.sjtu.edu.cn
   ```

---

### Blocked for Running Computation on Login Node / 登录节点运行计算被封

**Symptoms / 症状:**
```
Your account has been temporarily blocked due to resource abuse on login node.
Connection closed by remote host.
```

**Cause / 原因:**
- Running CPU/memory intensive tasks on login nodes triggers automatic blocking
- 在登录节点运行计算密集作业会被自动查杀
- Account added to blacklist for 30-120 minutes / 账号加入黑名单30-120分钟

**IMPORTANT / 重要:**
```
Login nodes are ONLY for:        登录节点仅用于:
- File editing                   - 文件编辑
- Job submission                 - 作业提交
- Small data transfers           - 小型数据传输
- Checking job status            - 查看作业状态

NOT for:                         不可用于:
- Running programs               - 运行程序
- Compiling large projects       - 编译大型项目
- Data processing                - 数据处理
```

**Solutions / 解决方案:**

1. **Wait for unblock / 等待解封** (30-120 minutes / 30-120分钟)

2. **Use sbatch for all computations / 使用sbatch提交所有计算:**
   ```bash
   # Example job script / 示例作业脚本
   #!/bin/bash
   #SBATCH --job-name=test
   #SBATCH --partition=64c512g
   #SBATCH --ntasks=1
   #SBATCH --cpus-per-task=4
   #SBATCH --time=01:00:00

   python my_script.py
   ```

3. **For interactive testing, use srun / 交互式测试使用srun:**
   ```bash
   srun -p 64c512g -n 1 --cpus-per-task=4 --pty bash
   ```

---

### Session Limit Exceeded / Session数量限制

**Symptoms / 症状:**
```
shell request failed on channel 0
PTY allocation request failed on channel 0
```

**Cause / 原因:**
- Maximum 8 sessions per account per login node / 每账号单个login节点最多8个session

**Solutions / 解决方案:**

1. **Close unused connections / 关闭不用的连接:**
   ```bash
   # On your local machine, find zombie SSH processes / 本地查找僵尸SSH进程
   ps aux | grep ssh
   kill <pid>
   ```

2. **Use SSH multiplexing / 使用SSH多路复用:**
   ```bash
   # ~/.ssh/config
   Host sjtu-hpc
       HostName sylogin.hpc.sjtu.edu.cn
       User your_username
       ControlMaster auto
       ControlPath ~/.ssh/sockets/%r@%h-%p
       ControlPersist 600
   ```
   ```bash
   mkdir -p ~/.ssh/sockets
   ```

3. **Use tmux/screen for session management / 使用tmux/screen管理会话:**
   ```bash
   # Start tmux session
   tmux new -s work

   # Detach: Ctrl+b, then d
   # Reattach
   tmux attach -t work
   ```

---

### SSH Connection Drops Frequently / SSH常掉线

**Symptoms / 症状:**
```
client_loop: send disconnect: Broken pipe
Connection to sylogin.hpc.sjtu.edu.cn closed by remote host.
packet_write_wait: Connection to 202.120.58.229 port 22: Broken pipe
```

**Solutions / 解决方案:**

**Client-side configuration / 客户端配置:**
```bash
# ~/.ssh/config
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes

Host sjtu-hpc
    HostName sylogin.hpc.sjtu.edu.cn
    User your_username
    ServerAliveInterval 240
    ServerAliveCountMax 5
```

**For VS Code Remote SSH / VS Code远程SSH:**
```json
// settings.json
{
    "remote.SSH.connectTimeout": 60,
    "remote.SSH.serverInstallPath": {
        "sjtu-hpc": "~/.vscode-server"
    }
}
```

---

## Job Issues / 作业问题

### Job Status: node_fail / 作业状态node_fail

**Symptoms / 症状:**
```bash
$ squeue -u $USER
JOBID  PARTITION  NAME  USER  ST  TIME  NODES  NODELIST(REASON)
12345  64c512g    test  user  NF  0:00  1      node_fail
```

**Cause / 原因:**
- Compute node hardware failure / 计算节点硬件故障
- Node became unreachable during job execution / 作业执行期间节点不可达

**Solutions / 解决方案:**

1. **Resubmit the job / 重新提交作业:**
   ```bash
   sbatch job.slurm
   ```

2. **Check job accounting / 检查机时使用:**
   ```bash
   sacct -j JOBID --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS
   ```
   - CPU time is automatically refunded for hardware failures
   - 硬件故障导致的失败，机时自动返还

3. **Exclude problematic nodes / 排除问题节点:**
   ```bash
   #SBATCH --exclude=node001,node002
   ```

---

### Missing Shared Library (.so) Files / 缺少动态链接库文件

**Symptoms / 症状:**
```
error while loading shared libraries: libxxx.so: cannot open shared object file
ImportError: libcudart.so.11.0: cannot open shared object file: No such file or directory
```

**Cause / 原因:**
- Running on login node instead of compute node / 在登录节点而非计算节点运行
- Required module not loaded / 未加载所需模块
- Software compiled on different node type / 软件在不同节点类型编译

**Solutions / 解决方案:**

1. **Ensure running on compute node / 确保在计算节点运行:**
   ```bash
   # Use sbatch or srun, NOT direct execution on login node
   # 使用sbatch或srun提交，不要在登录节点直接运行
   srun -p 64c512g -n 1 --pty bash
   ```

2. **Load required modules / 加载所需模块:**
   ```bash
   module load cuda/11.8
   module load gcc/11.2.0
   ```

3. **Check library path / 检查库路径:**
   ```bash
   echo $LD_LIBRARY_PATH
   ldd your_program
   ```

---

### Job Pending for Long Time / 作业长时间排队

**Symptoms / 症状:**
```bash
$ squeue -u $USER
JOBID  PARTITION  NAME  USER  ST  TIME  NODES  NODELIST(REASON)
12345  64c512g    test  user  PD  0:00  10     (Resources)
12346  64c512g    test  user  PD  0:00  10     (Priority)
12347  64c512g    test  user  PD  0:00  10     (QOSMaxJobsPerUserLimit)
```

**Diagnosis / 诊断:**
```bash
# Check cluster usage / 查看集群使用率
# Web: https://account.hpc.sjtu.edu.cn/top/

# Check available nodes / 查看空闲节点
sinfo -p 64c512g

# Check queue status / 查看队列状态
squeue -p 64c512g | head -20

# Check your job priority / 查看作业优先级
sprio -u $USER
```

**Common Reasons / 常见原因:**

| Reason | Meaning | Solution |
|--------|---------|----------|
| `(Resources)` | Waiting for resources / 等待资源 | Reduce resource request / 减少资源申请 |
| `(Priority)` | Lower priority / 优先级较低 | Wait or use different partition / 等待或换队列 |
| `(QOSMaxJobsPerUserLimit)` | Hit job limit / 达到作业数限制 | Wait for running jobs to finish / 等待运行中作业完成 |
| `(AssocGrpCPUMinutesLimit)` | CPU time quota exceeded / CPU时间配额用尽 | Contact admin / 联系管理员 |
| `(ReqNodeNotAvail)` | Requested node unavailable / 请求节点不可用 | Remove node constraint / 移除节点限制 |
| `(AssocGrpNodeLimit)` | Account node limit (see below) / 账户节点限制 | **Check cluster assignment** / 检查集群分配 |

---

### ⚠️ Critical: AssocGrpNodeLimit - Wrong Cluster / 关键: 集群配置错误

**Symptoms / 症状:**
```bash
$ squeue -u $USER
JOBID  PARTITION  NAME  USER  ST  TIME  NODES  NODELIST(REASON)
12345  64c512g    test  user  PD  0:00  1      (AssocGrpNodeLimit)
```

**IMPORTANT / 重要:** `AssocGrpNodeLimit` does NOT always mean you've exceeded your quota. It often means your account is configured on a **different cluster** than where you're submitting!

`AssocGrpNodeLimit` 并不一定意味着配额用尽。它经常意味着你的账户配置在**另一个集群**上！

**Diagnosis / 诊断:**
```bash
# Check which cluster your account is configured on
# 检查账户配置在哪个集群
sacctmgr show assoc where user=$USER format=Cluster,Account,User,MaxNodes

# Look at the "Cluster" column:
# - "sjtupi" = Pi 2.0 cluster (login.hpc.sjtu.edu.cn)
# - "siyuan" = Siyuan-1 cluster (sylogin.hpc.sjtu.edu.cn)
```

**Common Mistake / 常见错误:**
- User applies for account on Pi 2.0 (sjtupi)
- User tries to submit jobs to Siyuan-1 (siyuan)
- Jobs stuck with `AssocGrpNodeLimit` because account has no allocation on Siyuan-1

- 用户在 Pi 2.0 (sjtupi) 上申请账户
- 用户尝试向思源一号 (siyuan) 提交作业
- 作业卡在 `AssocGrpNodeLimit` 因为账户在思源一号上没有配额

**Solutions / 解决方案:**

1. **Identify correct cluster / 确认正确集群:**
   ```bash
   sacctmgr show assoc where user=$USER
   # If Cluster=sjtupi → Use Pi 2.0 (login.hpc.sjtu.edu.cn)
   # If Cluster=siyuan → Use Siyuan-1 (sylogin.hpc.sjtu.edu.cn)
   ```

2. **Use the correct login node / 使用正确登录节点:**

   | Cluster | Login Node | Data Node | Home Path |
   |---------|------------|-----------|-----------|
   | Pi 2.0 (sjtupi) | `login.hpc.sjtu.edu.cn` | `data.hpc.sjtu.edu.cn` | `/lustre/home/acct-xxx/user` |
   | Siyuan-1 (siyuan) | `sylogin.hpc.sjtu.edu.cn` | `sydata.hpc.sjtu.edu.cn` | `/dssg/home/acct-xxx/user` |

3. **If you need access to both clusters / 如需两个集群的访问权限:**
   ```
   Email: hpc@sjtu.edu.cn
   Subject: Request access to additional cluster / 申请其他集群访问权限
   Content: Explain your need for both clusters / 说明需要两个集群的原因
   ```

---

**Solutions / 解决方案:**

1. **Submit during off-peak hours / 错峰提交:**
   - Peak hours / 高峰期: 10:00-18:00 weekdays / 工作日
   - Off-peak / 低峰期: Night, weekends / 夜间、周末

2. **Reduce resource requests / 减少资源申请:**
   ```bash
   # Before / 修改前
   #SBATCH --nodes=10
   #SBATCH --ntasks-per-node=64

   # After / 修改后
   #SBATCH --nodes=4
   #SBATCH --ntasks-per-node=32
   ```

3. **Use less busy partitions / 使用空闲队列:**
   ```bash
   # Check all partitions / 查看所有队列
   sinfo -o "%P %a %D %T"
   ```

---

### Job Timeout / 作业超时

**Symptoms / 症状:**
```
slurmstepd: error: *** JOB 12345 ON node001 CANCELLED AT 2024-01-15T10:00:00 DUE TO TIME LIMIT ***
CANCELLED+
```

**Default Time Limits / 默认时间限制:**

| Partition / 队列 | Maximum Time / 最长时间 |
|------------------|------------------------|
| 64c512g, a100, cpu, small, dgx2, arm128c256g | 7 days / 7天 |
| huge, 192c6t | 2 days / 2天 |

**Check partition limits / 查看队列限制:**
```bash
# View detailed partition information / 查看队列详细信息
scontrol show partition

# View specific partition / 查看特定队列
scontrol show partition 64c512g
```

**Solutions / 解决方案:**

1. **Request appropriate time / 申请合适时间:**
   ```bash
   #SBATCH --time=3-00:00:00  # 3 days / 3天
   #SBATCH --time=72:00:00    # 72 hours / 72小时
   ```

2. **Request extension / 申请延长:**
   ```
   Email: hpc@sjtu.edu.cn
   Subject: Job time extension request / 作业延时申请

   Content / 内容:
   - Username / 用户名
   - Job ID / 作业ID
   - Estimated additional runtime needed / 预计需要的额外运行时间
   - Reason / 原因

   IMPORTANT / 重要:
   - Submit request AT LEAST 2 business days before timeout
   - 务必在作业超时前至少2个工作日发送申请
   - Maximum extension: 14 days / 最长可延期14天
   ```

3. **Implement checkpointing / 实现检查点:**
   ```python
   # Python example
   import pickle

   # Save checkpoint
   with open('checkpoint.pkl', 'wb') as f:
       pickle.dump({'epoch': epoch, 'model': model.state_dict()}, f)

   # Load checkpoint
   if os.path.exists('checkpoint.pkl'):
       with open('checkpoint.pkl', 'rb') as f:
           checkpoint = pickle.load(f)
   ```

---

### Out of Memory (OOM) / 内存不足

**Symptoms / 症状:**
```
slurmstepd: error: Detected 1 oom-kill event(s) in StepId=12345.0
Out of memory: Kill process 12345 (python) score 950 or sacrifice child
Killed
MemoryError
```

**Diagnosis / 诊断:**
```bash
# Check memory usage of completed job / 查看已完成作业内存使用
sacct --format="JobId,JobName,MaxRSS,MaxVMSize,AveRSS,State" -P -j JOBID

# Check memory usage of running job / 查看运行中作业内存
sstat -j JOBID --format=JobID,MaxRSS,MaxVMSize

# Monitor in real-time / 实时监控
srun --jobid=JOBID --pty top
```

**Solutions / 解决方案:**

1. **Increase memory request / 增加内存申请:**
   ```bash
   # Per node / 每节点
   #SBATCH --mem=128G

   # Per CPU / 每CPU
   #SBATCH --mem-per-cpu=8G
   ```

2. **Reduce parallelism / 减少并发数:**
   ```bash
   # Reduce threads/processes
   #SBATCH --cpus-per-task=4  # Instead of 16

   # In Python
   import os
   os.environ['OMP_NUM_THREADS'] = '4'
   os.environ['MKL_NUM_THREADS'] = '4'
   ```

3. **Use memory-efficient techniques / 使用内存高效技术:**
   ```python
   # Use generators instead of lists
   def data_generator():
       for chunk in pd.read_csv('large.csv', chunksize=10000):
           yield chunk

   # Use memory-mapped files
   import numpy as np
   arr = np.memmap('data.dat', dtype='float32', mode='r', shape=(1000000, 100))
   ```

4. **Choose appropriate partition / 选择合适队列:**
   ```bash
   # High memory partitions / 大内存队列
   #SBATCH --partition=huge      # 6TB memory nodes
   #SBATCH --partition=192c6t    # 6TB memory nodes
   ```

---

### Job Array Issues / 作业数组问题

**Symptoms / 症状:**
```
sbatch: error: Batch job submission failed: Invalid job array specification
```

**Solutions / 解决方案:**

```bash
# Correct array specification / 正确的数组规范
#SBATCH --array=0-99           # 0 to 99
#SBATCH --array=1,3,5,7        # Specific indices
#SBATCH --array=1-100:2        # Step of 2
#SBATCH --array=1-1000%50      # Max 50 concurrent / 最多50个同时运行

# Access array index in script / 脚本中访问数组索引
echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "Job ID: $SLURM_ARRAY_JOB_ID"
```

---

## Software Issues / 软件问题

### Software Installation / 软件安装

**IMPORTANT / 重要:**
- Regular users do NOT have sudo/root access / 普通用户没有sudo/root权限
- You CANNOT use `sudo apt install` or `sudo yum install` / 不能使用sudo安装系统软件

**Available Installation Methods / 可用安装方法:**

| Method / 方法 | Use Case / 适用场景 |
|---------------|---------------------|
| Conda | Python packages, bioinformatics tools / Python包、生信工具 |
| pip | Python packages / Python包 |
| Source compilation / 源码编译 | Custom software / 自定义软件 |
| Singularity/Apptainer containers / 容器 | Complex dependencies / 复杂依赖 |
| Module system / 模块系统 | Pre-installed software / 预装软件 |

**Installation Examples / 安装示例:**

```bash
# Method 1: Conda (recommended for most cases)
# 方法1: Conda (大多数情况推荐)
conda create -n myenv python=3.10
conda activate myenv
conda install numpy pandas

# Method 2: pip with user flag
# 方法2: pip用户安装
pip install --user package_name

# Method 3: Source compilation to home directory
# 方法3: 源码编译到用户目录
./configure --prefix=$HOME/software/package_name
make -j 8
make install
export PATH=$HOME/software/package_name/bin:$PATH

# Method 4: Singularity container
# 方法4: Singularity容器
singularity pull docker://ubuntu:22.04
singularity exec ubuntu_22.04.sif your_command
```

**Request System-wide Installation / 申请系统级安装:**
```
Email: hpc@sjtu.edu.cn
Subject: Software installation request / 软件安装申请

Content / 内容:
- Software name and version / 软件名称和版本
- Download URL / 下载地址
- Your use case / 使用场景
```

---

### Module Not Found / 模块未找到

**Symptoms / 症状:**
```
module: command not found
Lmod has detected the following error: The following module(s) are unknown: "xxx"
```

**Diagnosis / 诊断:**
```bash
# List all available modules / 列出所有可用模块
module avail

# Search for specific module / 搜索特定模块
module avail python
module spider cuda

# Check loaded modules / 查看已加载模块
module list
```

**Solutions / 解决方案:**

1. **Check spelling and version / 检查拼写和版本:**
   ```bash
   # Wrong
   module load Python/3.9

   # Correct (case-sensitive / 区分大小写)
   module load python/3.9.6
   ```

2. **Load dependencies first / 先加载依赖:**
   ```bash
   # Some modules require GCC
   module load gcc/11.2.0
   module load cuda/11.8
   ```

3. **Use module spider for details / 用spider查看详情:**
   ```bash
   module spider pytorch
   # Shows all versions and dependencies
   ```

---

### Conda Environment Issues / Conda环境问题

**Symptoms / 症状:**
```
CondaError: Downloaded bytes did not match Content-Length
Solving environment: failed with initial frozen solve. Retrying with flexible solve.
ResolvePackageNotFound:
PackagesNotFoundError:
```

**Solutions / 解决方案:**

1. **Disable auto-activation / 取消自动激活:**
   ```bash
   conda config --set auto_activate_base false
   ```

2. **Create isolated environment / 创建隔离环境:**
   ```bash
   # Create new environment for conflicting packages
   conda create -n myenv python=3.10
   conda activate myenv
   conda install package_name
   ```

3. **Use mamba for faster solving / 使用mamba加速:**
   ```bash
   conda install -n base -c conda-forge mamba
   mamba install package_name
   ```

4. **Clear cache and retry / 清除缓存重试:**
   ```bash
   conda clean --all
   conda install package_name
   ```

5. **Use pip as fallback / 使用pip作为备选:**
   ```bash
   pip install --no-cache-dir package_name
   ```

---

### Compute Nodes Cannot Access Network / 计算节点无法访问网络

**Symptoms / 症状:**
```
curl: (7) Failed to connect to github.com port 443: Connection timed out
pip install: Connection timed out
git clone: fatal: unable to access
requests.exceptions.ConnectionError: HTTPSConnectionPool
```

**IMPORTANT / 重要:** Compute nodes have NO direct internet access. Proxy is required.
计算节点无法直接访问外网，必须设置代理。

**Solutions / 解决方案:**

**1. Shell proxy settings / Shell代理设置:**

```bash
# Siyuan-1 / 思源一号
export http_proxy=http://proxy2.pi.sjtu.edu.cn:3128
export https_proxy=http://proxy2.pi.sjtu.edu.cn:3128
export HTTP_PROXY=http://proxy2.pi.sjtu.edu.cn:3128
export HTTPS_PROXY=http://proxy2.pi.sjtu.edu.cn:3128
export no_proxy=localhost,127.0.0.1,.sjtu.edu.cn

# Pi 2.0
export http_proxy=http://proxy.pi.sjtu.edu.cn:3004
export https_proxy=http://proxy.pi.sjtu.edu.cn:3004
export HTTP_PROXY=http://proxy.pi.sjtu.edu.cn:3004
export HTTPS_PROXY=http://proxy.pi.sjtu.edu.cn:3004
export no_proxy=localhost,127.0.0.1,.sjtu.edu.cn
```

**2. Add to job script / 添加到作业脚本:**
```bash
#!/bin/bash
#SBATCH --job-name=test
#SBATCH --partition=64c512g

# Set proxy / 设置代理
export http_proxy=http://proxy2.pi.sjtu.edu.cn:3128
export https_proxy=http://proxy2.pi.sjtu.edu.cn:3128

# Your commands
python download_data.py
```

**3. Python requests / Python requests库:**
```python
import requests

proxies = {
    'http': 'http://proxy2.pi.sjtu.edu.cn:3128',
    'https': 'http://proxy2.pi.sjtu.edu.cn:3128',
}

response = requests.get('https://example.com', proxies=proxies)
```

**4. Python urllib / Python urllib库:**
```python
import urllib.request

proxy = urllib.request.ProxyHandler({
    'http': 'http://proxy2.pi.sjtu.edu.cn:3128',
    'https': 'http://proxy2.pi.sjtu.edu.cn:3128',
})
opener = urllib.request.build_opener(proxy)
urllib.request.install_opener(opener)
```

**5. pip configuration / pip配置:**
```bash
# One-time use
pip install --proxy http://proxy2.pi.sjtu.edu.cn:3128 package_name

# Permanent configuration
pip config set global.proxy http://proxy2.pi.sjtu.edu.cn:3128
```

**6. conda configuration / conda配置:**
```bash
conda config --set proxy_servers.http http://proxy2.pi.sjtu.edu.cn:3128
conda config --set proxy_servers.https http://proxy2.pi.sjtu.edu.cn:3128
```

**7. git configuration / git配置:**
```bash
git config --global http.proxy http://proxy2.pi.sjtu.edu.cn:3128
git config --global https.proxy http://proxy2.pi.sjtu.edu.cn:3128
```

**8. wget configuration / wget配置:**
```bash
# ~/.wgetrc
http_proxy=http://proxy2.pi.sjtu.edu.cn:3128
https_proxy=http://proxy2.pi.sjtu.edu.cn:3128
```

**9. curl usage / curl使用:**
```bash
curl -x http://proxy2.pi.sjtu.edu.cn:3128 https://example.com
```

**10. R configuration / R配置:**
```r
Sys.setenv(http_proxy = "http://proxy2.pi.sjtu.edu.cn:3128")
Sys.setenv(https_proxy = "http://proxy2.pi.sjtu.edu.cn:3128")
```

---

### BLAS Thread Configuration / BLAS 线程配置

**Symptoms / 症状:**
- HPC runs slower than local machine for matrix-heavy workloads
- HPC 上矩阵运算比本地机器还慢
- Single-threaded performance is poor despite having many cores
- 单线程性能差，尽管有很多核心

**Cause / 原因:**
When running parallel workers (e.g., crew/future), BLAS threads are often limited to prevent oversubscription:
```bash
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
```

This causes individual matrix operations to be 2-3x slower than unlimited BLAS.
当运行并行 workers 时，BLAS 线程被限制以防止过度订阅，但这会导致单个矩阵运算慢 2-3 倍。

**Diagnosis / 诊断:**
```bash
# Benchmark matrix multiplication with different BLAS settings
# 用不同 BLAS 设置测试矩阵乘法
Rscript -e "
n <- 2000
A <- matrix(rnorm(n*n), n, n)
B <- matrix(rnorm(n*n), n, n)
cat('OPENBLAS_NUM_THREADS:', Sys.getenv('OPENBLAS_NUM_THREADS'), '\n')
t1 <- system.time(C <- A %*% B)[3]
cat('Time:', t1, 'seconds\n')
"
```

**Trade-off / 权衡:**

| Config | Workers | BLAS Threads | Total Threads | Best For |
|--------|---------|--------------|---------------|----------|
| High parallelism | 9 | 2 | 18 | Many small tasks / 多个小任务 |
| Balanced | 4 | 8 | 32 | Mixed workloads / 混合负载 |
| BLAS-heavy | 2 | 16 | 32 | Large matrix ops (IRT, regression) / 大矩阵运算 |

**Solutions / 解决方案:**

1. **For BLAS-heavy workloads (hIRT, mirt, lme4) / BLAS 密集型负载:**
   ```bash
   # In slurm script / 在 slurm 脚本中
   export OPENBLAS_NUM_THREADS=8
   export MKL_NUM_THREADS=8

   # Reduce workers accordingly / 相应减少 workers
   # n_workers = (total_cores - 1) / BLAS_THREADS
   ```

2. **Dynamic adjustment / 动态调整:**
   ```r
   # In R, adjust for specific heavy operations
   # 在 R 中为特定重负载操作调整
   RhpcBLASctl::blas_set_num_threads(8)  # Before heavy computation
   # ... run hIRT/mirt model ...
   RhpcBLASctl::blas_set_num_threads(2)  # Reset for parallel tasks
   ```

3. **Check current BLAS library / 检查当前 BLAS 库:**
   ```r
   sessionInfo()$BLAS
   # Should show OpenBLAS or MKL, not reference BLAS
   # 应该显示 OpenBLAS 或 MKL，不是 reference BLAS
   ```

**Example: Social Cleavages Project / 示例:**
- hIRT models are BLAS-heavy (EM algorithm with many matrix ops)
- With BLAS=2: nocov_F1 takes 28 min on HPC vs 10 min on Mac
- With BLAS=8: would be ~2x faster but fewer parallel workers
- hIRT 模型是 BLAS 密集型（EM 算法包含大量矩阵运算）
- BLAS=2 时：nocov_F1 在 HPC 上需要 28 分钟，Mac 上只需 10 分钟
- BLAS=8 时：会快约 2 倍，但并行 workers 更少

**Recommended Configuration (2026-02) / 推荐配置:**

```bash
# run_hpc.slurm - Optimized for hIRT/BLAS-heavy workloads
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
export OPENBLAS_NUM_THREADS=8

# MICE runs on main process, can use more cores when crew workers are idle
export MICE_N_CORE=8
```

```r
# _targets.R - Fewer workers with more BLAS threads each
if (is_hpc) {
  n_cores <- as.integer(Sys.getenv("SLURM_NTASKS", "20"))
  n_workers <- max(1, (n_cores - 1) %/% 8)  # 20核 → 2 workers
}
```

**Note on MICE Performance / MICE 性能说明:**
- MICE (PMM) is NOT BLAS-heavy; it's memory/IO intensive
- MICE runs faster on HPC than local Mac (9.5 min/m vs 12 min/m per imputation)
- futuremice uses its own `plan(multisession)`, independent of crew workers
- Increasing MICE_N_CORE improves throughput when crew workers are idle
- MICE (PMM) 不是 BLAS 密集型，而是内存/IO 密集型
- MICE 在 HPC 上比本地 Mac 更快（每次插补 9.5 分钟 vs 12 分钟）
- futuremice 使用自己的 `plan(multisession)`，与 crew workers 独立
- 增加 MICE_N_CORE 可以在 crew workers 空闲时提高吞吐量

---

### CUDA/GPU Issues / CUDA/GPU问题

**Symptoms / 症状:**
```
CUDA error: no CUDA-capable device is detected
RuntimeError: CUDA out of memory
CUDA_ERROR_NO_DEVICE
torch.cuda.is_available() returns False
```

**Diagnosis / 诊断:**
```bash
# Check GPU availability / 检查GPU可用性
nvidia-smi

# Check CUDA version / 检查CUDA版本
nvcc --version

# Check PyTorch CUDA / 检查PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"
python -c "import torch; print(torch.version.cuda)"
```

**Solutions / 解决方案:**

1. **Request GPU resources / 申请GPU资源:**
   ```bash
   #SBATCH --partition=a100
   #SBATCH --gres=gpu:1

   # Multiple GPUs / 多个GPU
   #SBATCH --gres=gpu:4
   ```

2. **Load correct CUDA module / 加载正确CUDA模块:**
   ```bash
   module load cuda/11.8
   module load cudnn/8.6.0_cuda11
   ```

3. **Match PyTorch/TensorFlow with CUDA version / 匹配版本:**
   ```bash
   # Check compatible versions
   # PyTorch: https://pytorch.org/get-started/previous-versions/

   pip install torch==2.0.1+cu118 -f https://download.pytorch.org/whl/torch_stable.html
   ```

4. **GPU memory management / GPU内存管理:**
   ```python
   import torch

   # Clear cache
   torch.cuda.empty_cache()

   # Use mixed precision
   from torch.cuda.amp import autocast
   with autocast():
       output = model(input)

   # Gradient checkpointing
   model.gradient_checkpointing_enable()
   ```

---

## Storage Issues / 存储问题

### Disk Quota Exceeded / 磁盘配额用尽

**Symptoms / 症状:**
```
Disk quota exceeded
OSError: [Errno 122] Disk quota exceeded
No space left on device
write error: No space left on device
```

**Diagnosis / 诊断:**
```bash
# Check quota (general) / 检查配额
quota -s

# Check Lustre quota / 检查Lustre配额
lfs quota -u $USER /lustre
lfs quota -u $USER /dssg

# Check disk usage / 检查磁盘使用
du -sh ~/*
du -sh ~/.[!.]* 2>/dev/null | sort -h

# Find large files / 查找大文件
find ~ -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k5 -h
```

**Storage Quotas / 存储配额:**

| Location | Quota | Purpose |
|----------|-------|---------|
| $HOME | 50GB-200GB | Code, configs / 代码、配置 |
| /lustre | Project-based | Active data / 活跃数据 |
| /dssg | Project-based | Large datasets / 大型数据集 |
| /scratch | Temporary | Temp files (auto-cleaned) / 临时文件 |

**Solutions / 解决方案:**

1. **Clean unnecessary files / 清理不必要文件:**
   ```bash
   # Remove conda cache / 清理conda缓存
   conda clean --all

   # Remove pip cache / 清理pip缓存
   pip cache purge

   # Remove old logs / 清理旧日志
   find ~/logs -mtime +30 -delete

   # Remove core dumps / 清理core dump
   find ~ -name "core.*" -delete
   ```

2. **Move data to appropriate storage / 迁移数据到合适位置:**
   ```bash
   # Move large datasets to Lustre
   mv ~/large_data /lustre/project/your_project/

   # Create symbolic link
   ln -s /lustre/project/your_project/large_data ~/large_data
   ```

3. **Compress inactive data / 压缩不活跃数据:**
   ```bash
   tar -czvf archive.tar.gz old_project/
   rm -rf old_project/
   ```

4. **Request quota increase / 申请增加配额:**
   ```
   Email: hpc@sjtu.edu.cn
   Subject: Storage quota increase request / 存储配额增加申请
   ```

---

### Slow Data Transfer / 数据传输慢

**Symptoms / 症状:**
- Transfer speed < 10 MB/s
- Transfer hangs or times out
- Extremely slow rsync/scp

**Solutions / 解决方案:**

1. **Use dedicated transfer nodes / 使用专用传输节点:**
   ```bash
   # Siyuan-1
   scp file user@sydata.hpc.sjtu.edu.cn:/path/
   rsync -avz file user@sydata.hpc.sjtu.edu.cn:/path/

   # Pi 2.0
   scp file user@data.hpc.sjtu.edu.cn:/path/
   ```

2. **Use parallel transfer / 并行传输:**
   ```bash
   # Using GNU parallel with scp
   ls *.dat | parallel -j 4 scp {} user@sydata.hpc.sjtu.edu.cn:/path/

   # Using rsync with parallel
   rsync -avz --progress -e "ssh" /local/path/ user@sydata.hpc.sjtu.edu.cn:/remote/path/
   ```

3. **Use rsync for incremental transfer / rsync增量传输:**
   ```bash
   rsync -avz --partial --progress source/ user@sydata.hpc.sjtu.edu.cn:/dest/

   # Resume interrupted transfer / 续传
   rsync -avz --partial --append source/ user@sydata.hpc.sjtu.edu.cn:/dest/
   ```

4. **Compress before transfer / 传输前压缩:**
   ```bash
   # Compress
   tar -czvf data.tar.gz data/

   # Transfer
   scp data.tar.gz user@sydata.hpc.sjtu.edu.cn:/path/

   # Extract on server
   ssh user@sydata.hpc.sjtu.edu.cn "tar -xzvf /path/data.tar.gz -C /path/"
   ```

5. **Use rclone for cloud storage / 使用rclone传输云存储:**
   ```bash
   module load rclone
   rclone copy local_dir remote:bucket/path --transfers 8
   ```

---

### File Permission Issues / 文件权限问题

**Symptoms / 症状:**
```
Permission denied
Operation not permitted
cannot open file: Permission denied
```

**Solutions / 解决方案:**

```bash
# Check file permissions / 检查文件权限
ls -la file

# Fix permissions / 修复权限
chmod 755 script.sh      # Executable script
chmod 644 data.txt       # Regular file
chmod -R 755 directory/  # Directory recursive

# Check group / 检查组
groups
ls -la | awk '{print $4}' | sort | uniq

# Change group / 更改组
chgrp -R project_group directory/
```

---

## Billing Issues / 欠费问题

### Account Arrears / 账户欠费

**Symptoms / 症状:**
```
WARNING: Your account balance is negative. Please recharge.
警告：您的账户余额为负，请及时充值。
You cannot submit new jobs due to insufficient balance.
```

**Impacts / 影响:**

| Status | Impact |
|--------|--------|
| Balance warning / 余额警告 | SSH login shows reminder / SSH登录显示提醒 |
| Negative balance / 负余额 | Cannot request new resources / 无法申请新计算资源 |
| Existing jobs / 已提交作业 | Continue running / 继续运行 |

**Solutions / 解决方案:**

1. **Check balance / 查看余额:**
   ```bash
   # Web portal
   https://account.hpc.sjtu.edu.cn/
   ```

2. **Recharge / 充值:**
   - Contact your PI / 联系课题组负责人
   - Follow institutional procedures / 按学校流程充值

3. **Contact support / 联系支持:**
   ```
   Email: hpc@sjtu.edu.cn
   Subject: Account balance inquiry / 账户余额咨询
   ```

### Fee Structure & Payment / 收费标准与缴费

**Check Fee Structure / 查询收费标准:**
- Contact: hpc@sjtu.edu.cn for detailed pricing
- 联系 hpc@sjtu.edu.cn 获取详细收费标准

**Payment Methods / 缴费方式:**

1. **我的数字交大 (校内支付)**
   - Login to my.sjtu.edu.cn → Search "高性能计算" → Payment
   - 登录 my.sjtu.edu.cn → 搜索"高性能计算" → 缴费

2. **交我算 App (Mobile payment / 移动端支付)**
   - Download "交我算" app → Account recharge
   - 下载"交我算"App → 账户充值

**Check Balance / 查询余额:**
- Web portal / 网页端: https://account.hpc.sjtu.edu.cn
- Login with HPC username / 使用HPC用户名登录

---

## Publication Acknowledgment / 论文致谢

**IMPORTANT / 重要:** When publishing research that used SJTU HPC resources, please include the following acknowledgment.
使用上海交通大学HPC资源发表论文时，请在致谢部分添加以下内容。

**Chinese Version / 中文版:**
> 本论文的计算结果得到了上海交通大学高性能计算中心的支持。

**English Version (for Pi 2.0 cluster):**
> Computations were supported by the π 2.0 cluster at the High Performance Computing Center of Shanghai Jiao Tong University.

**English Version (for Siyuan-1 cluster / 思源一号):**
> Computations were supported by the Siyuan-1 cluster at the High Performance Computing Center of Shanghai Jiao Tong University.

**Combined Version (if used both clusters / 如使用了两个集群):**
> Computations were supported by the π 2.0 and Siyuan-1 clusters at the High Performance Computing Center of Shanghai Jiao Tong University.

---

## Getting Help / 获取帮助

### Support Channels / 支持渠道

| Channel | Contact | Purpose |
|---------|---------|---------|
| Email / 邮箱 | hpc@sjtu.edu.cn | Primary support / 主要支持渠道 |
| Email (alt) / 备用邮箱 | computing@sjtu.edu.cn | Alternative contact / 备用联系 |
| WeChat Official / 微信公众号 | 交我算 | Announcements, maintenance notices / 通知、停机公告 |
| User WeChat Group / 用户微信群 | Email hpc@sjtu.edu.cn to join / 发邮件申请加入 | Community support, real-time notices / 社区支持、实时通知 |
| Documentation / 文档 | https://docs.hpc.sjtu.edu.cn | Self-service / 自助服务 |
| Account Portal / 账户门户 | https://account.hpc.sjtu.edu.cn | Balance, usage stats / 余额、使用统计 |

### Expected Response Times / 预期响应时间

| Request Type / 请求类型 | Response Time / 响应时间 |
|-------------------------|-------------------------|
| Account creation / 账户创建 | 1-2 business days / 1-2个工作日 |
| Script debugging / 脚本调试帮助 | 1-2 business days / 1-2个工作日 |
| Anomalous job investigation / 异常作业调查 | 2-3 business days / 2-3个工作日 |
| Custom software compilation / 定制软件编译 | 1-2 weeks / 1-2周 |
| Job time extension / 作业延时申请 | 1-2 business days / 1-2个工作日 |
| Quota increase / 配额增加 | 2-3 business days / 2-3个工作日 |

**Join WeChat User Group / 加入用户微信群:**
- Email hpc@sjtu.edu.cn with subject "申请加入用户微信群"
- Include your username and contact information
- 发送邮件至 hpc@sjtu.edu.cn，主题为"申请加入用户微信群"
- 包含您的用户名和联系方式

### Email Template / 邮件模板

```
To: hpc@sjtu.edu.cn
Subject: [Issue Type] Brief description / [问题类型] 简短描述

Dear HPC Support Team,
尊敬的HPC支持团队，

Issue Description / 问题描述:
[Describe the problem clearly / 清晰描述问题]

Error Message / 错误信息:
[Paste exact error message / 粘贴确切错误信息]

Environment / 环境:
- Cluster / 集群: Siyuan-1 / Pi 2.0
- Username / 用户名: xxx
- Job ID / 作业ID: xxx (if applicable / 如适用)
- Partition / 队列: xxx
- Software / 软件: xxx

Steps to Reproduce / 复现步骤:
1. ...
2. ...

What I have tried / 已尝试的方法:
- ...
- ...

Best regards,
[Your name / 您的姓名]
[Student/Staff ID / 学工号]
```

### Useful Commands Summary / 常用命令汇总

```bash
# System status / 系统状态
sinfo                          # Partition status / 队列状态
squeue -u $USER                # Your jobs / 您的作业
sacct -u $USER --starttime=today  # Today's jobs / 今日作业
quota -s                       # Storage quota / 存储配额

# Job management / 作业管理
sbatch job.slurm               # Submit job / 提交作业
scancel JOBID                  # Cancel job / 取消作业
scontrol show job JOBID        # Job details / 作业详情

# Module management / 模块管理
module avail                   # List modules / 列出模块
module load xxx                # Load module / 加载模块
module unload xxx              # Unload module / 卸载模块
module purge                   # Unload all / 卸载所有

# Account info / 账户信息
id                             # User/group info / 用户组信息
groups                         # Group membership / 组成员
```

---

## ⚠️ 核心原则：擦干净屁股

**每次会话结束前（无论正常还是异常），必须运行清理检查：**

```bash
hpc-cleanup              # 交互式检查并清理
# 或
hpc-cleanup --check      # 仅检查，不清理
```

**检查内容**：残留作业、SCRATCH 临时文件、screen/tmux 会话、登录节点进程

**违反后果**：残留作业持续计费、账号封禁、通报批评

---

## 故障恢复操作 / Recovery Procedures

> 相关文档：[storage.md](storage.md) | [data.md](data.md)

### 中断传输恢复 / Resume Interrupted Transfer

**场景**: rsync/scp 传输中途断开

```bash
# rsync 自动支持断点续传 (使用 --partial)
rsync -avP --partial source/ user@data.hpc.sjtu.edu.cn:/path/dest/

# 如果使用 scp 中断了，改用 rsync 续传
# rsync 会自动跳过已完成的文件
rsync -avP --checksum source/ user@data.hpc.sjtu.edu.cn:/path/dest/

# 验证传输完整性
cd source/
find . -type f -exec md5sum {} \; | sort > /tmp/source.md5
ssh user@data.hpc.sjtu.edu.cn "cd /path/dest && find . -type f -exec md5sum {} \;" | sort > /tmp/dest.md5
diff /tmp/source.md5 /tmp/dest.md5
```

### 配额紧急清理 / Emergency Quota Cleanup

**场景**: "Disk quota exceeded" 无法写入任何文件

```bash
# Step 1: 快速检查配额使用
quota -s

# Step 2: 定位大文件/目录 (不需要写入)
du -sh $HOME/* 2>/dev/null | sort -hr | head -20

# Step 3: 紧急清理 (按优先级)

# 3.1 清理缓存 (通常可以安全删除)
rm -rf ~/.cache/*
rm -rf ~/.local/share/Trash/*

# 3.2 清理 conda/pip 缓存
conda clean --all -y 2>/dev/null || true
pip cache purge 2>/dev/null || true

# 3.3 删除旧日志和临时文件
find $HOME -name "*.log" -mtime +7 -delete 2>/dev/null
find $HOME -name "slurm-*.out" -mtime +30 -delete 2>/dev/null
find $HOME -name "core.*" -delete 2>/dev/null
find $HOME -name "*.pyc" -delete 2>/dev/null
find $HOME -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# 3.4 清理 R 临时文件
rm -rf /tmp/Rtmp* 2>/dev/null
rm -rf $HOME/.Rhistory $HOME/.RData 2>/dev/null

# Step 4: 使用 scripts/quota_check.sh 脚本进行详细检查
```

### 误删数据恢复（科学大数据平台）/ Recover Deleted Data from Union

**场景**: 误删了 $UNION 中的重要数据

**重要**: 科学大数据平台 (/union) 支持快照恢复，其他存储 (/lustre, /dssg) 不支持！

```bash
# ⚠️ 立即停止写入！不要在同一位置创建新文件！

# Step 1: 记录删除信息
echo "删除时间: $(date)" > ~/recovery_request.txt
echo "文件路径: /union/home/acct-XXX/user/deleted_file_or_dir" >> ~/recovery_request.txt
echo "用户名: $USER" >> ~/recovery_request.txt

# Step 2: 发送恢复请求邮件
# To: hpc@sjtu.edu.cn
# Subject: 快照恢复请求 / Snapshot Recovery Request
# Content: 包含上述信息

# 注意事项:
# - 恢复成功率取决于快照保留策略
# - 通常保留最近 7-30 天的快照
# - 越早申请成功率越高
```

### 作业意外终止后的数据抢救 / Data Recovery After Job Failure

**场景**: 作业被 OOM kill / 超时终止 / 节点故障

```bash
# Step 1: 检查作业状态和退出原因
sacct -j JOBID --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList

# Step 2: 检查是否有残留数据在 $SCRATCH
ls -la $SCRATCH/job_${JOBID}/ 2>/dev/null || echo "Scratch 目录已清理或不存在"

# Step 3: 检查作业输出日志
cat $HOME/jobs/${JOBID}.out 2>/dev/null | tail -100
cat $HOME/jobs/${JOBID}.err 2>/dev/null | tail -100

# Step 4: 如果使用了检查点 (checkpoint)，找到最新的检查点
find $HOME -name "checkpoint*.pt" -o -name "*.ckpt" -o -name "*.rds" | xargs ls -lt | head -10

# Step 5: 对于 R targets 项目，检查 _targets/ 目录
ls -la $HOME/project/_targets/objects/ 2>/dev/null

# Step 6: 对于 Python 项目，检查是否有中间结果
find $HOME/project -name "*.pkl" -o -name "*.parquet" | xargs ls -lt | head -10

# 预防措施: 在作业脚本中添加定期保存检查点
# Python: torch.save(model.state_dict(), f'checkpoint_epoch_{epoch}.pt')
# R: saveRDS(results, file.path(checkpoint_dir, paste0('step_', step, '.rds')))
```

### 节点故障导致的作业失败处理 / Handle Node Failure

**场景**: 作业状态显示 `node_fail` 或 `NODE_FAIL`

```bash
# Step 1: 确认失败原因
sacct -j JOBID --format=JobID,State,ExitCode,NodeList

# Step 2: 检查机时是否自动返还
# 硬件故障导致的失败，机时自动返还，无需申请

# Step 3: 排除问题节点后重新提交
# 在作业脚本中添加:
#SBATCH --exclude=problematic_node1,problematic_node2

# 或者直接重新提交 (调度器会避免分配到故障节点)
sbatch job.slurm
```

---

## Quick Reference Card / 快速参考卡

### Emergency Contacts / 紧急联系

- **System Down / 系统故障**: hpc@sjtu.edu.cn
- **Account Locked / 账户锁定**: hpc@sjtu.edu.cn
- **Urgent Issues / 紧急问题**: Check WeChat group / 查看微信群

### Proxy Settings Quick Copy / 代理设置快速复制

**Siyuan-1 / 思源一号:**
```bash
export http_proxy=http://proxy2.pi.sjtu.edu.cn:3128
export https_proxy=http://proxy2.pi.sjtu.edu.cn:3128
```

**Pi 2.0:**
```bash
export http_proxy=http://proxy.pi.sjtu.edu.cn:3004
export https_proxy=http://proxy.pi.sjtu.edu.cn:3004
```

### Common Partition Quick Reference / 常用队列快速参考

| Partition | CPUs/Node | Memory | Time Limit | Use Case |
|-----------|-----------|--------|------------|----------|
| 64c512g | 64 | 512GB | 7 days | General / 通用 |
| small | 64 | 512GB | 7 days | Small jobs / 小作业 |
| cpu | 64 | 512GB | 7 days | CPU only / 纯CPU任务 |
| huge | 192 | 6TB | 2 days | High memory / 大内存 |
| 192c6t | 192 | 6TB | 2 days | High memory / 大内存 |
| a100 | 64 | 512GB | 7 days | GPU tasks / GPU任务 |
| dgx2 | varies | varies | 7 days | GPU tasks / GPU任务 |
| arm128c256g | 128 | 256GB | 7 days | ARM architecture / ARM架构 |

---

*Last updated: 2025-01*
*Document maintained by HPC Center, SJTU*
*Updated with additional FAQ content: 2025-01*
