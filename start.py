import os
import uvicorn

if __name__ == "__main__":
    import subprocess
    print("🔄 Executando migrações antes de iniciar o servidor...")
    subprocess.run(["python", "migrate_scheduling.py"], check=True)

    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Iniciando na porta {port}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")