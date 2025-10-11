import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager


# Configurar o navegador
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)


def recarregar_pagina():
    print("\n🔁 Recarregando página...")
    driver.get("http://localhost:8501")
    time.sleep(2) 

# 1. Campos de login e senha vazios
def teste_campos_vazios():
    driver.get("http://localhost:8501")
    print("\n🧪 Cenário 1: Login com campos vazios")

    entrar_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[.//text()='➡️ Entrar']"))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", entrar_button)
    time.sleep(1)

    ActionChains(driver).move_to_element(entrar_button).click().perform()
    print("🖱️ Botão 'Entrar' clicado!")

    mensagem_erro = wait.until(
        EC.visibility_of_element_located((By.XPATH, "//p[text()='❌ Usuário ou senha inválidos.']"))
    )

    texto_encontrado = mensagem_erro.text.strip()
    texto_esperado = "❌ Usuário ou senha inválidos."

    assert texto_encontrado == texto_esperado, (
        f"\n❌ Mensagem incorreta!\n"
        f"Esperado: '{texto_esperado}'\n"
        f"Encontrado: '{texto_encontrado}'"
    )

    print(f"✅ Mensagem correta: '{texto_encontrado}'")

# 2. Campos de login e senha com dados inválidos
def teste_credenciais_incorretas():
    print("\n🧪 Cenário 2: Login com credenciais incorretas")

    input_fields = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "input")))
    input_fields[0].send_keys("teste")
    input_fields[1].send_keys("teste")

    entrar_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[.//text()='➡️ Entrar']"))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", entrar_button)
    time.sleep(1)

    ActionChains(driver).move_to_element(entrar_button).click().perform()
    print("🖱️ Botão 'Entrar' clicado!")

    mensagem_erro = wait.until(
        EC.visibility_of_element_located((By.XPATH, "//p[text()='❌ Usuário ou senha inválidos.']"))
    )

    texto_encontrado = mensagem_erro.text.strip()
    texto_esperado = "❌ Usuário ou senha inválidos."

    assert texto_encontrado == texto_esperado, (
        f"\n❌ Mensagem incorreta!\n"
        f"Esperado: '{texto_esperado}'\n"
        f"Encontrado: '{texto_encontrado}'"
    )

    print(f"✅ Mensagem correta: '{texto_encontrado}'")

# 3. Código MFA incorreto
# def teste_codigo_mfa_incorreto():
#     print("\n🧪 Cenário 3: Verificação MFA com código incorreto")

#     input_fields = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "input")))
#     input_fields[0].send_keys("admin")
#     input_fields[1].send_keys("admin")

#     entrar_button = wait.until(
#         EC.element_to_be_clickable((By.XPATH, "//button[.//text()='➡️ Entrar']"))
#     )
#     driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", entrar_button)
#     time.sleep(1)

#     ActionChains(driver).move_to_element(entrar_button).click().perform()
#     print("🖱️ Botão 'Entrar' clicado!")

#     receber_codigo = wait.until(
#         EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Receber Código MFA')]"))
#     )
#     receber_codigo.click()

#     codigo_input = wait.until(
#         EC.visibility_of_element_located((By.ID, "text_input_3"))
#     )
#     codigo_input.send_keys("000000") 
#     print("🔢 Código MFA preenchido!")

#     verificar_button = wait.until(
#         EC.element_to_be_clickable((By.XPATH, "//button[.//text()='✅ Verificar Código']"))
#     )
#     verificar_button.click()

#     mensagem_erro = wait.until(
#         EC.visibility_of_element_located((By.XPATH, "//p[text()='❌ Código incorreto. Tente novamente.']"))
#     )

#     texto_encontrado = mensagem_erro.text.strip()
#     texto_esperado = "❌ Código incorreto. Tente novamente."

#     assert texto_encontrado == texto_esperado, (
#         f"\n❌ Mensagem incorreta!\n"
#         f"Esperado: '{texto_esperado}'\n"
#         f"Encontrado: '{texto_encontrado}'"
#     )

#     print(f"✅ Mensagem correta: '{texto_encontrado}'")


try:
    # Teste 1: Campos vazios
    teste_campos_vazios()
    recarregar_pagina()

    # Teste 2: Credenciais incorretas
    teste_credenciais_incorretas()
    recarregar_pagina()

    # Teste 3: Código MFA incorreto
    # teste_codigo_mfa_incorreto()

except Exception as e:
    print(f"\n❌ Erro durante a execução dos testes: {e}")
    raise

finally:
    time.sleep(3)
    driver.quit()