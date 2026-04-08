# 最优样本选择系统

本项目是一个用于人工智能课程的样本选择系统，可将 Python 程序打包为 Android APK 文件。系统支持通过参数配置，从样本集中选择最优的 k 元组组合，满足覆盖条件。

## 项目简介

本系统基于 BeeWare 框架开发，使用 Toga 作为 GUI 工具包。主要功能：

- 输入参数 m, n, k, j, s, t（详见参数说明）
- 支持随机生成样本或手动输入
- 贪心+模拟退火算法求解最优覆盖组合
- 保存历史记录，支持查看和删除
- 可打包为 Android APK，在手机上运行

## 一、开发环境配置

本项目在 **VMware 虚拟机 + Ubuntu 24.04** 环境下开发和测试。以下为完整配置步骤。

### 1. 系统要求

- Ubuntu 24.04（或 22.04/20.04）
- Python 3.8+

### 2. 更新系统包

```bash
sudo apt update
sudo apt upgrade -y
```

### 3. 安装 Python 虚拟环境支持

```bash
sudo apt install python3.12-venv python3.12-dev -y
```

### 4. 安装 Git

```bash
sudo apt install git -y
```

### 5. 安装系统依赖（Toga 和 Briefcase 需要）

```bash
sudo apt install -y \
libcairo2-dev \
libgirepository1.0-dev \
pkg-config \
python3-dev \
libgdk-pixbuf2.0-dev \
libglib2.0-dev \
libgtk-3-dev \
libpango1.0-dev \
libcairo-gobject2 \
gir1.2-gtk-3.0
```

### 6. 创建并激活 Python 虚拟环境

```bash
cd ~
python3 -m venv briefcase-env
source briefcase-env/bin/activate
```

> 每次新开终端都需要激活：`source ~/briefcase-env/bin/activate`

### 7. 安装 Briefcase

```bash
pip install --upgrade pip
pip install briefcase
```

验证安装：

```bash
briefcase --version
```

应显示 0.4.0 或更高版本。

## 二、本地部署与运行

### 1. 获取项目代码

克隆仓库：

```bash
git clone https://github.com/xyutong75-ux/Optimal-sample-selection.git
cd "Optimal-sample-selection/android_sample_selector"
```

### 2. 运行测试

确保在虚拟环境中：

```bash
briefcase dev
```

### 3. 生成 Android APK

```bash
briefcase create android
briefcase build android
briefcase package android -p debug-apk
```

## 常见问题

**Q1: briefcase 命令找不到？**  
A: 虚拟环境未激活，执行 `source ~/briefcase-env/bin/activate`

**Q2: 首次创建 Android 项目卡住？**  
A: 第一次会下载 Android SDK 和 Gradle，需等待 10-30 分钟，请保持网络畅通。

**Q3: APK 安装失败？**  
A: 在手机设置中开启“允许安装未知应用”。

**Q4: 窗口显示不全？**  
A: 代码已设置默认窗口大小 1300×900，若仍看不清可手动拖动窗口边缘。

## 算法说明

本项目使用**贪心+模拟退火算法**求解最优覆盖组合：

- **贪心初始化**：快速生成一个可行解
- **模拟退火优化**：通过随机添加、移除、交换操作，逐步优化解的质量
- **能量函数**：优先保证覆盖所有 j 元组，其次最小化 k 元组数量

该算法在保证运行速度的同时，能输出接近最优的解，适用于 n ≤ 25 的各类参数组合。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 贡献者

- [许彦熙]
- [夏雨桐]

## 项目地址

GitHub: [https://github.com/xyutong75-ux/Optimal-sample-selection](https://github.com/xyutong75-ux/Optimal-sample-selection)
