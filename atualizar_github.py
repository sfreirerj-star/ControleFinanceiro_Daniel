import subprocess


def fazer_deploy_github():
  print("🚀 Iniciando o envio para o GitHub...")

  try:
    subprocess.run(["git", "add", "."], check=True)
    print("✔ Arquivos adicionados com sucesso.")

    mensagem = (
        input("Digite a mensagem do commit (ou ENTER para padrão): ") or "Atualização via script Python"
    )
    subprocess.run(["git", "commit", "-m", mensagem], check=True)
    print("✔ Commit realizado com sucesso.")

    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("🎉 Sucesso! Alterações enviadas para o GitHub e Streamlit Cloud.")

  except subprocess.CalledProcessError as e:
    print(f"❌ Erro durante o processo do Git: {e}")
  except Exception as ex:
    print(f"❌ Erro inesperado: {ex}")


if __name__ == "__main__":
  fazer_deploy_github()
