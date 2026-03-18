# DA-pet

DA-pet 是一个用 Python 开发的桌面宠物系统。第一版专注在最小可运行体验：

- 右下角显示一个常驻的小角色
- 侦测全域滑鼠点击
- 每次点击任何地方都会增加 EXP
- 累积 EXP 后自动升级，并在特定等级切换成长形态
- 将成长进度存到本地 `data/pet_state.json`

## 第一版功能

- 角色固定显示在 Windows 画面右下角
- 角色视窗会保持在最上层
- 点击桌面、浏览器、应用程式时都能累积经验
- 等级会随经验成长，角色外观也会跟着变化

## 技术选型

- `tkinter`: 桌面 GUI
- `pynput`: 全域滑鼠点击侦测
- `json`: 本地资料储存

## 目录结构

```text
DA-pet/
|- data/
|  \- pet_state.json
|- src/
|  \- da_pet/
|     |- app.py
|     |- listener.py
|     |- pet_window.py
|     |- state.py
|     \- storage.py
|- requirements.txt
\- run.py
```

## 安装与执行

这台电脑目前还没有安装 Python，所以这里先把执行步骤写好。安装完成后可以直接运行。

1. 安装 Python 3.11 或更新版本
2. 安装时勾选 `Add Python to PATH`
3. 在项目目录打开 PowerShell
4. 建立虚拟环境：

```powershell
py -m venv .venv
```

5. 启动虚拟环境：

```powershell
.venv\Scripts\Activate.ps1
```

6. 安装依赖：

```powershell
pip install -r requirements.txt
```

7. 启动桌面宠物：

```powershell
py run.py
```

## 操作说明

- 启动后角色会出现在右下角
- 全域滑鼠左键、右键、中键按下都会加 EXP
- 右上角的 `X` 可以关闭角色
- 也可以按 `Esc` 结束程式

## 目前成长规则

- 每次滑鼠点击 +1 EXP
- 升级门槛会随等级逐步提高
- 形态切换：
  - Level 1-2: Seed
  - Level 3-4: Bud
  - Level 5+: Bloom

后续版本可以继续加入：

- 开启应用程式加经验
- 视窗切换加经验
- 更完整的进化分支
- 动画与角色素材
