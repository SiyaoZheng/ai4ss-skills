# SSH Access — HPC & IDEKube

环境变量驱动的统一连接参考。所有敏感值从环境变量读取，不在文件中硬编码。

## 环境变量

在 `~/.zshrc` 或 `~/.zshenv` 中设置。不要把真实用户名、私钥路径、
证书路径或工作区 ID 提交到公共仓库；下面只使用占位符。

```bash
# === SJTU HPC ===
export SJTU_HPC_USER="YOUR_HPC_USERNAME"                         # HPC 用户名
export SJTU_HPC_KEY="$HOME/.ssh/sjtu_hpc_ed25519"                 # HPC SSH 私钥（思源一号）
export SJTU_HPC_CERT="$HOME/.ssh/sjtu_hpc_ed25519-cert.pub"       # HPC SSH 证书（思源一号）
export SJTU_HPC_PI_KEY="$HOME/.ssh/sjtu_pi_ed25519"               # HPC SSH 私钥（Pi 2.0）
export SJTU_HPC_PI_CERT="$HOME/.ssh/sjtu_pi_ed25519-cert.pub"     # HPC SSH 证书（Pi 2.0）

# === SJTU IDEKube ===
export SJTU_IDEKUBE_USER="YOUR_IDEKUBE_USERNAME"                 # IDEKube SSH 用户名
export SJTU_IDEKUBE_WS="YOUR_IDEKUBE_WORKSPACE_ID"               # IDEKube workspace short UUID
```

## SSH Config

`~/.ssh/config` 中的别名（引用环境变量对应的实际值）：

```ssh-config
# === 思源一号 ===
Host hpc sy
    HostName sylogin.hpc.sjtu.edu.cn
    User YOUR_HPC_USERNAME
    IdentityFile ~/.ssh/sjtu_hpc_ed25519
    CertificateFile ~/.ssh/sjtu_hpc_ed25519-cert.pub
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600

Host hpc-data sy-data
    HostName sydata.hpc.sjtu.edu.cn
    User YOUR_HPC_USERNAME
    IdentityFile ~/.ssh/sjtu_hpc_ed25519
    CertificateFile ~/.ssh/sjtu_hpc_ed25519-cert.pub
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600

# === Pi 2.0 ===
Host pi
    HostName pilogin.hpc.sjtu.edu.cn
    User YOUR_HPC_USERNAME
    IdentityFile ~/.ssh/sjtu_pi_ed25519
    CertificateFile ~/.ssh/sjtu_pi_ed25519-cert.pub

Host pi-data
    HostName data.hpc.sjtu.edu.cn
    User YOUR_HPC_USERNAME
    IdentityFile ~/.ssh/sjtu_pi_ed25519
    CertificateFile ~/.ssh/sjtu_pi_ed25519-cert.pub

# === IDEKube (交我算 AI Lab) ===
# 别名示例：idekube-ml
Host idekube-ml
    HostName YOUR_IDEKUBE_WORKSPACE_ID.ailab-api.sjtu.edu.cn
    ProxyCommand websocat --binary wss://YOUR_IDEKUBE_WORKSPACE_ID.ailab-api.sjtu.edu.cn/ssh/
    User YOUR_IDEKUBE_USERNAME

```

> **注意**: SSH config 不支持环境变量展开，所以别名中直接写实际值。环境变量供脚本和 Skill 逻辑使用。

## 快速命令

### HPC

| 操作 | 命令 |
|------|------|
| SSH 登录（思源一号） | `ssh hpc` |
| SSH 登录（Pi 2.0） | `ssh pi` |
| 数据传输（思源一号） | `ssh hpc-data` |
| 数据传输（Pi 2.0） | `ssh pi-data` |
| 交互式作业 | `srun -p 64c512g -n 4 --pty /bin/bash` |

### IDEKube

| 操作 | 命令 |
|------|------|
| SSH 登录 | `ssh idekube-ml` |
| OpenClaw TUI | `ssh -t idekube-ml "openclaw tui"` |
| OpenClaw health | `ssh idekube-ml "openclaw health"` |
| 单次命令 | `ssh idekube-ml "<cmd>"` |

## IDEKube 连接细节

- **认证方式**: 公钥认证（将你自己的公钥添加到容器 `~/.ssh/authorized_keys`）
- **隧道**: `websocat`（`brew install websocat`）通过 WebSocket (`wss://`) 到 `/ssh/` 端点
- **平台入口**: https://ailab.sjtu.edu.cn
- **课程/镜像/端口**: 以课程工作区或管理员提供的信息为准，不在公共 skill 中硬编码。

### 公钥配置（容器重建后需重新执行）

在 IDEKube Web Terminal 中**单行**执行：

```bash
mkdir -p ~/.ssh && echo '<公钥内容>' >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
```

> Web Terminal 的 xterm 遇到换行会拆成多条命令导致语法错误，必须单行粘贴。

## 安全规则

1. **fail2ban**: HPC 登录节点 3 次失败 → IP 封禁 1 小时。失败 2 次就停。
2. **SSH 证书**: HPC 证书有有效期，过期需重新签发。检查：`ssh-keygen -L -f "$SJTU_HPC_CERT"`
3. **IDEKube 容器重建**: 容器重建后 `authorized_keys` 丢失，需重新添加公钥。
4. **禁止在登录节点运行计算**: 必须 `sbatch` 或 `srun --pty`。
5. **SSH 连接复用**: 思源一号已配置 `ControlMaster`，首次连接后后续连接复用通道，避免重复认证。

## 构造 SSH 命令（脚本用）

使用环境变量构造命令：

```bash
# HPC
ssh -i "$SJTU_HPC_KEY" -o CertificateFile="$SJTU_HPC_CERT" \
    "$SJTU_HPC_USER@sylogin.hpc.sjtu.edu.cn"

# IDEKube
ssh -o ProxyCommand="websocat --binary wss://${SJTU_IDEKUBE_WS}.ailab-api.sjtu.edu.cn/ssh/" \
    "$SJTU_IDEKUBE_USER@${SJTU_IDEKUBE_WS}.ailab-api.sjtu.edu.cn"
```
