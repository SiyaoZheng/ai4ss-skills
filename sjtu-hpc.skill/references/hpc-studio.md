# HPC Studio Visual Platform Guide (可视化平台指南)

> **URL**: https://studio.hpc.sjtu.edu.cn
>
> HPC Studio is SJTU's web-based graphical interface for managing HPC resources, files, jobs, and interactive applications.
>
> HPC Studio 是交我算的网页图形界面，用于管理 HPC 资源、文件、作业和交互式应用。

---

## Table of Contents (目录)

1. [Login (登录方式)](#1-login-登录方式)
2. [File Management (文件管理)](#2-file-management-文件管理)
3. [Job Management (作业管理)](#3-job-management-作业管理)
4. [Web Shell (网页终端)](#4-web-shell-网页终端)
5. [Remote Desktop (远程桌面)](#5-remote-desktop-远程桌面)
6. [Built-in Applications (内置应用)](#6-built-in-applications-内置应用)
7. [Jupyter Usage (Jupyter 使用)](#7-jupyter-usage-jupyter-使用)
8. [RStudio Usage (RStudio 使用)](#8-rstudio-usage-rstudio-使用)
9. [Troubleshooting (常见问题)](#9-troubleshooting-常见问题)

---

## 1. Login (登录方式)

### Supported Browsers (支持的浏览器)

| Browser | Support |
|---------|---------|
| Google Chrome | Recommended (推荐) |
| Mozilla Firefox | Supported (支持) |
| Microsoft Edge | Supported (支持) |
| Safari | May have issues (可能有问题) |

### Login Steps (登录步骤)

1. **Open browser and navigate to HPC Studio**

   打开浏览器，访问 HPC Studio
   ```
   https://studio.hpc.sjtu.edu.cn
   ```

2. **Enter your credentials**

   输入交我算账号密码
   - **Username**: Your account name (e.g., `user-name`)
   - **Password**: Your HPC password

   使用与 SSH 登录相同的交我算账号密码

3. **Click "Login" button**

   点击"登录"按钮

> **Note**: Use the same credentials as SSH login. VPN connection is NOT required for HPC Studio access.
>
> **注意**: 使用与 SSH 登录相同的凭证。访问 HPC Studio 不需要 VPN 连接。

---

## 2. File Management (文件管理)

Access the file manager from the top menu: **Files** -> Select your home directory

从顶部菜单访问文件管理器：**Files** -> 选择您的主目录

### Available Storage Locations (可用存储位置)

| Location | Cluster | Path Pattern |
|----------|---------|--------------|
| Home Directory (Pi 2.0) | Pi 2.0 / AI / ARM | `/lustre/home/acct-XXX/username` |
| Home Directory (Siyuan-1) | Siyuan-1 | `/dssg/home/acct-XXX/username` |

### File Operations (文件操作)

#### View Files (查看文件)

1. Click on **Files** in the top navigation bar

   点击顶部导航栏的 **Files**

2. Select your home directory from the dropdown

   从下拉菜单选择您的主目录

3. Browse the file tree to find your files

   浏览文件树查找文件

#### Edit Files (编辑文件)

1. Navigate to the file you want to edit

   导航到要编辑的文件

2. Click on the file name to select it

   点击文件名选中文件

3. Click **Edit** button (or right-click -> Edit)

   点击 **Edit** 按钮（或右键 -> 编辑）

4. Make changes in the built-in text editor

   在内置文本编辑器中进行修改

5. Click **Save** to save changes

   点击 **Save** 保存修改

#### Rename Files (重命名文件)

1. Select the file or folder

   选中文件或文件夹

2. Click **Rename** button (or right-click -> Rename)

   点击 **Rename** 按钮（或右键 -> 重命名）

3. Enter the new name and press Enter

   输入新名称并按回车

#### Download Files (下载文件)

1. Select the file(s) you want to download

   选中要下载的文件

2. Click **Download** button

   点击 **Download** 按钮

3. For multiple files, they will be compressed into a zip archive

   多个文件会被压缩成 zip 包

#### Upload Files (上传文件)

1. Navigate to the destination folder

   导航到目标文件夹

2. Click **Upload** button

   点击 **Upload** 按钮

3. Select files from your local computer

   从本地电脑选择文件

4. Wait for the upload to complete

   等待上传完成

> **Tip**: For large files (> 1GB), use `scp` or `rsync` via command line instead.
>
> **提示**: 大文件（> 1GB）建议使用 `scp` 或 `rsync` 命令行传输。

#### Show Hidden Files (显示隐藏文件)

1. Click on the **Settings** icon (gear) in the file manager

   点击文件管理器中的 **Settings** 图标（齿轮）

2. Check **Show Dotfiles** option

   勾选 **Show Dotfiles** 选项

3. Hidden files (starting with `.`) will now be visible

   隐藏文件（以 `.` 开头）将会显示

#### Open Terminal (打开终端)

1. Navigate to your desired working directory

   导航到目标工作目录

2. Click **Open in Terminal** button

   点击 **Open in Terminal** 按钮

3. A new terminal tab will open in that directory

   新终端标签页会在该目录打开

---

## 3. Job Management (作业管理)

### View Active Jobs (查看作业)

1. Click **Jobs** in the top navigation bar

   点击顶部导航栏的 **Jobs**

2. Select **Active Jobs**

   选择 **Active Jobs**

3. View all your running and pending jobs

   查看所有运行中和排队中的作业

#### Job Status Indicators (作业状态指示)

| Status | Description | 描述 |
|--------|-------------|------|
| `PENDING (PD)` | Waiting in queue | 排队等待中 |
| `RUNNING (R)` | Currently executing | 正在运行 |
| `COMPLETED (CD)` | Finished successfully | 成功完成 |
| `FAILED (F)` | Terminated with error | 错误终止 |
| `CANCELLED (CA)` | Cancelled by user | 用户取消 |

#### Job Actions (作业操作)

- **View Details**: Click on job ID to see full information

  **查看详情**: 点击作业 ID 查看完整信息

- **Cancel Job**: Select job and click **Delete** button

  **取消作业**: 选中作业并点击 **Delete** 按钮

- **View Output**: Click on output file link to see results

  **查看输出**: 点击输出文件链接查看结果

### Submit Jobs (提交作业)

1. Click **Jobs** -> **Job Composer**

   点击 **Jobs** -> **Job Composer**

2. Click **New Job** -> **From Template** or **From Default Template**

   点击 **New Job** -> **From Template** 或 **From Default Template**

3. Configure your job:

   配置作业：

   | Field | Description | 描述 |
   |-------|-------------|------|
   | Job Name | Name for your job | 作业名称 |
   | Cluster | Select target cluster | 选择目标集群 |
   | Script | Path to your job script | 作业脚本路径 |

4. Click **Submit** to submit the job

   点击 **Submit** 提交作业

### Edit Job Scripts Online (在线编辑作业脚本)

1. In **Job Composer**, select your job

   在 **Job Composer** 中选择您的作业

2. Click **Edit Files** button

   点击 **Edit Files** 按钮

3. Modify the Slurm script directly in the browser

   直接在浏览器中修改 Slurm 脚本

4. Save your changes

   保存修改

#### Example Slurm Script Template (Slurm 脚本模板)

```bash
#!/bin/bash
#SBATCH --job-name=my_job
#SBATCH --partition=small
#SBATCH -n 4
#SBATCH --output=%j.out
#SBATCH --error=%j.err

# Load required modules
module load miniconda3
source activate myenv

# Run your program
python my_script.py
```

---

## 4. Web Shell (网页终端)

Access a command-line terminal directly in your browser.

直接在浏览器中访问命令行终端。

### Open Web Shell (打开网页终端)

1. Click **Clusters** in the top navigation bar

   点击顶部导航栏的 **Clusters**

2. Select **sjtu Shell Access**

   选择 **sjtu Shell Access**

3. A new terminal session will open

   新终端会话将会打开

### Features (功能特点)

- Full command-line access to login nodes

  完整的登录节点命令行访问

- Support for all standard Linux commands

  支持所有标准 Linux 命令

- Copy/paste functionality

  复制/粘贴功能

- Multiple terminal tabs

  多终端标签页

### Usage Tips (使用提示)

- **Copy**: Select text, right-click -> Copy (or Ctrl+Shift+C)

  **复制**: 选中文本，右键 -> 复制（或 Ctrl+Shift+C）

- **Paste**: Right-click -> Paste (or Ctrl+Shift+V)

  **粘贴**: 右键 -> 粘贴（或 Ctrl+Shift+V）

- **New Tab**: Click the **+** button to open additional terminals

  **新标签**: 点击 **+** 按钮打开更多终端

> **Note**: Web Shell connects to login nodes. Do NOT run compute-intensive tasks here.
>
> **注意**: 网页终端连接到登录节点。请勿在此运行计算密集型任务。

---

## 5. Remote Desktop (远程桌面)

Access a full graphical desktop environment on compute nodes.

在计算节点上访问完整的图形桌面环境。

### Launch Remote Desktop (启动远程桌面)

1. Click **Interactive Apps** in the top navigation bar

   点击顶部导航栏的 **Interactive Apps**

2. Select **Desktop**

   选择 **Desktop**

3. Configure your session:

   配置会话参数：

   | Parameter | Description | 推荐值 |
   |-----------|-------------|--------|
   | Number of cores | CPU cores to allocate | 4-8 |
   | Number of hours | Session duration | 2-8 hours |
   | Partition | Compute queue | `small` or `64c512g` |

4. Click **Launch** to submit the desktop job

   点击 **Launch** 提交桌面作业

5. Wait for the job to start (status changes from "Queued" to "Running")

   等待作业启动（状态从"排队"变为"运行"）

6. Click **Launch Desktop** button to connect

   点击 **Launch Desktop** 按钮连接

### Resource Billing (资源计费)

> **Important**: Remote Desktop sessions consume compute resources and will be billed.
>
> **重要**: 远程桌面会话消耗计算资源，会产生费用。

| Cores | Hours | Approximate Cost |
|-------|-------|------------------|
| 4 | 2 | ~8 core-hours |
| 8 | 4 | ~32 core-hours |

**Always remember to:**
- Delete the session when finished
- Don't leave sessions running overnight unnecessarily

**请务必：**
- 完成后删除会话
- 不要让会话不必要地过夜运行

### Desktop Features (桌面功能)

- Run GUI applications (MATLAB, Paraview, etc.)

  运行图形界面应用（MATLAB、Paraview 等）

- File browser with drag-and-drop

  支持拖放的文件浏览器

- Multiple virtual desktops

  多虚拟桌面

- Clipboard sharing with local machine

  与本地机器共享剪贴板

---

## 6. Built-in Applications (内置应用)

HPC Studio provides many pre-configured interactive applications.

HPC Studio 提供许多预配置的交互式应用。

### Application List (应用列表)

| Application | Description | Use Case |
|-------------|-------------|----------|
| **Jupyter Notebook** | Interactive Python/R notebooks | Data analysis, ML prototyping |
| **JupyterLab** | Modern Jupyter interface | Advanced notebook workflows |
| **RStudio Server** | R development environment | Statistical analysis |
| **MATLAB** | MATLAB GUI | Engineering, simulation |
| **DeepSeek Server** | AI model inference | LLM applications |
| **Paraview** | 3D visualization | CFD, scientific visualization |
| **TensorBoard** | ML experiment tracking | Deep learning monitoring |
| **CodeServer** | VS Code in browser | General development |
| **IGV** | Genome browser | Bioinformatics |
| **Octave** | MATLAB alternative | Numerical computing |

### Launching Applications (启动应用)

1. Click **Interactive Apps** in the navigation bar

   点击导航栏的 **Interactive Apps**

2. Select the desired application

   选择所需应用

3. Configure resources (cores, memory, time)

   配置资源（核数、内存、时长）

4. Click **Launch**

   点击 **Launch**

5. Wait for job to start, then click connection button

   等待作业启动，然后点击连接按钮

---

## 7. Jupyter Usage (Jupyter 使用)

### Pre-configured Environments (预置环境)

HPC Studio provides several pre-built Jupyter environments:

HPC Studio 提供多个预构建的 Jupyter 环境：

| Environment | Included Packages |
|-------------|-------------------|
| **PyTorch** | PyTorch, torchvision, CUDA support |
| **TensorFlow** | TensorFlow, Keras, CUDA support |
| **R** | R kernel with common packages |

### Launch Jupyter (启动 Jupyter)

1. Go to **Interactive Apps** -> **Jupyter Notebook** or **JupyterLab**

   进入 **Interactive Apps** -> **Jupyter Notebook** 或 **JupyterLab**

2. Select configuration:

   选择配置：

   | Parameter | Description | 建议值 |
   |-----------|-------------|--------|
   | Number of cores | CPU cores | 4 |
   | Number of GPUs | GPU cards (for deep learning) | 0-1 |
   | Partition | Compute queue | `small` or `a100` |
   | Python environment | Pre-built or custom | Select as needed |

3. Click **Launch** and wait

   点击 **Launch** 并等待

4. Click **Connect to Jupyter** when ready

   准备就绪后点击 **Connect to Jupyter**

### Register Custom Environment as Kernel (自定义环境注册为 Kernel)

To use your own conda environment in Jupyter:

将您自己的 conda 环境用于 Jupyter：

```bash
# Step 1: Load miniconda
# 步骤 1: 加载 miniconda
module load miniconda3

# Step 2: Create your environment
# 步骤 2: 创建环境
conda create -n myenv python=3.10

# Step 3: Activate environment
# 步骤 3: 激活环境
source activate myenv

# Step 4: Install ipykernel
# 步骤 4: 安装 ipykernel
conda install ipykernel

# Step 5: Register as Jupyter kernel
# 步骤 5: 注册为 Jupyter kernel
python -m ipykernel install --user --name myenv --display-name "My Environment"
```

After registration, your environment will appear in Jupyter's kernel list.

注册后，您的环境将出现在 Jupyter 的 kernel 列表中。

### Verify Kernel Installation (验证 Kernel 安装)

```bash
# List all installed kernels
# 列出所有已安装的 kernel
jupyter kernelspec list
```

### Remove a Kernel (移除 Kernel)

```bash
# Remove a specific kernel
# 移除指定 kernel
jupyter kernelspec uninstall myenv
```

---

## 8. RStudio Usage (RStudio 使用)

### Available R Versions (可用 R 版本)

| Version | Status |
|---------|--------|
| R 3.6.3 | Legacy |
| R 4.0.2 | Stable |
| R 4.1.3 | Recommended |
| R 4.2.2 | Latest |

### Launch RStudio (启动 RStudio)

1. Go to **Interactive Apps** -> **RStudio Server**

   进入 **Interactive Apps** -> **RStudio Server**

2. Configure your session:

   配置会话：

   | Parameter | Description | 建议值 |
   |-----------|-------------|--------|
   | R Version | Select R version | 4.2.2 |
   | Number of cores | CPU cores | 4-8 |
   | Number of hours | Session duration | 2-8 |
   | Partition | Compute queue | `small` |

3. Click **Launch** and wait for job allocation

   点击 **Launch** 等待作业分配

4. Click **Connect to RStudio Server** when ready

   准备就绪后点击 **Connect to RStudio Server**

### Data Storage Notice (数据存储注意事项)

> **Important**: Pi 2.0 and Siyuan-1 clusters have **separate** storage systems. Data is NOT shared between them.
>
> **重要**: Pi 2.0 和思源一号集群的存储系统是**独立的**。数据不互通。

| Cluster | Storage Path | Access |
|---------|--------------|--------|
| Pi 2.0 | `/lustre/home/acct-XXX/username` | Pi 2.0 RStudio only |
| Siyuan-1 | `/dssg/home/acct-XXX/username` | Siyuan-1 RStudio only |

If you need data on both clusters, you must transfer it manually.

如果需要在两个集群上使用相同数据，必须手动传输。

### Installing R Packages (安装 R 包)

In RStudio console:

在 RStudio 控制台：

```r
# Install from CRAN
install.packages("tidyverse")

# Install from GitHub
devtools::install_github("username/package")

# Set a local library path (if default is read-only)
.libPaths("~/R/library")
install.packages("mypackage")
```

---

## 9. Troubleshooting (常见问题)

### Proxy Error (代理错误)

**Symptom (症状):**
```
Proxy Error
The proxy server received an invalid response from an upstream server.
```

**Solutions (解决方案):**

1. **Disable VPN (关闭 VPN)**

   If you're connected to a VPN, disconnect it and try again.

   如果连接了 VPN，请断开后重试。

2. **Clear browser cache (清理浏览器缓存)**

   - Chrome: Settings -> Privacy -> Clear browsing data
   - Firefox: Settings -> Privacy -> Clear Data

   - Chrome: 设置 -> 隐私 -> 清除浏览数据
   - Firefox: 设置 -> 隐私 -> 清除数据

3. **Try a different browser (尝试其他浏览器)**

   Switch between Chrome, Firefox, and Edge.

   在 Chrome、Firefox、Edge 之间切换。

4. **Wait and retry (等待后重试)**

   The service may be temporarily overloaded. Wait a few minutes.

   服务可能暂时过载。等待几分钟后重试。

### Jupyter/RStudio Asks for Password (Jupyter/RStudio 要求密码)

**Symptom (症状):**
```
Password or token required
Enter password:
```

**Cause (原因):**

Conda's `base` environment auto-activation interferes with the server.

Conda 的 `base` 环境自动激活干扰了服务器。

**Solution (解决方案):**

```bash
# Disable auto-activation of conda base environment
# 禁用 conda base 环境自动激活
conda config --set auto_activate_base false
```

Then restart the Jupyter/RStudio session.

然后重启 Jupyter/RStudio 会话。

### Application Won't Start (应用无法启动)

**Symptom (症状):**

Job stays in "Queued" status for a long time.

作业长时间保持"排队"状态。

**Solutions (解决方案):**

1. **Check queue availability (检查队列可用性)**

   ```bash
   sinfo -p small
   ```

2. **Reduce resource request (减少资源请求)**

   Request fewer cores or shorter time.

   请求更少的核数或更短的时长。

3. **Try a different partition (尝试其他队列)**

   Some partitions may have shorter wait times.

   某些队列可能等待时间更短。

### Session Disconnected (会话断开)

**Symptom (症状):**

Browser shows "Connection lost" or page becomes unresponsive.

浏览器显示"连接丢失"或页面无响应。

**Solutions (解决方案):**

1. **Refresh the page (刷新页面)**

   Press F5 or click refresh.

   按 F5 或点击刷新。

2. **Go back to My Interactive Sessions (返回交互式会话列表)**

   Your session may still be running. Click **My Interactive Sessions** to reconnect.

   您的会话可能仍在运行。点击 **My Interactive Sessions** 重新连接。

3. **Check job status (检查作业状态)**

   ```bash
   squeue -u $USER
   ```

### File Upload Fails (文件上传失败)

**Symptom (症状):**

Upload progress stops or shows error.

上传进度停止或显示错误。

**Solutions (解决方案):**

1. **Check file size (检查文件大小)**

   For files > 100MB, use command-line transfer instead:

   对于 > 100MB 的文件，改用命令行传输：

   ```bash
   scp large_file.tar.gz username@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/username/
   ```

2. **Check storage quota (检查存储配额)**

   ```bash
   quota -s
   ```

3. **Use stable network (使用稳定网络)**

   Avoid uploading over unstable WiFi connections.

   避免在不稳定的 WiFi 连接上上传。

### Kernel Not Found in Jupyter (Jupyter 找不到 Kernel)

**Symptom (症状):**

Your custom environment doesn't appear in kernel list.

您的自定义环境没有出现在 kernel 列表中。

**Solution (解决方案):**

Re-register the kernel:

重新注册 kernel：

```bash
module load miniconda3
source activate myenv
python -m ipykernel install --user --name myenv --display-name "My Environment"
```

Then restart Jupyter session.

然后重启 Jupyter 会话。

---

## Quick Reference Card (快速参考卡)

| Task | Path |
|------|------|
| File Manager | Files -> Home Directory |
| Submit Job | Jobs -> Job Composer -> New Job |
| View Jobs | Jobs -> Active Jobs |
| Terminal | Clusters -> sjtu Shell Access |
| Desktop | Interactive Apps -> Desktop |
| Jupyter | Interactive Apps -> Jupyter Notebook |
| RStudio | Interactive Apps -> RStudio Server |
| My Sessions | My Interactive Sessions |

---

## External Resources (外部资源)

- **Full Documentation**: https://docs.hpc.sjtu.edu.cn
- **HPC Studio Portal**: https://studio.hpc.sjtu.edu.cn
- **Account Usage Monitor**: https://account.hpc.sjtu.edu.cn/top/
- **Support Email**: hpc@sjtu.edu.cn
