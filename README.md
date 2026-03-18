# DA-pet

This project uses a local Python virtual environment named `.venv`.

## Why `.venv` is not on GitHub

`.venv` is your local Python environment folder.
It is usually ignored by Git, so when someone downloads the project, they need to create their own `.venv`.

## How to create `.venv` on Windows

Open PowerShell in the project folder:

```powershell
cd C:\Users\jimmy\Desktop\DA-pet
```

Create the virtual environment:

```powershell
py -m venv .venv
```

If `py` does not work, try:

```powershell
python -m venv .venv
```

## How to activate `.venv`

In PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If activation is blocked, you can still run Python inside `.venv` directly:

```powershell
.\.venv\Scripts\python.exe run.py
```

## Install dependencies

Right now this project needs `pynput`:

```powershell
.\.venv\Scripts\python.exe -m pip install pynput
```

## Run the pet

After creating `.venv`, run:

```powershell
.\.venv\Scripts\python.exe run.py
```

## Important PowerShell note

In PowerShell, use:

```powershell
.\.venv\Scripts\python.exe
```

Do not use:

```powershell
.venv\Scripts\python.exe
```

The second form can be interpreted incorrectly by PowerShell.
