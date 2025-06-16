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

try:
    driver.get("http://localhost:8501")

    input_fields = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "input")))
    input_fields[0].send_keys("admin")
    input_fields[1].send_keys("admin")

    print("🔍 Procurando o botão 'Entrar'...")
    entrar_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Entrar')]"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", entrar_button)
    time.sleep(1)
    ActionChains(driver).move_to_element(entrar_button).click().perform()
    print("🖱️ Botão 'Entrar' clicado!")

    print("⏳ Aguardando aparecer o botão 'Receber Código MFA'...")
    mfa_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Receber Código MFA')]"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", mfa_button)
    time.sleep(1)
    ActionChains(driver).move_to_element(mfa_button).click().perform()
    print("📨 Botão 'Receber Código MFA' clicado!")

    print("⏳ Aguardando o código MFA ser exibido...")
    codigo_mfa = None

    for _ in range(5):
        try:
            codigo_element = wait.until(
                EC.presence_of_element_located((By.XPATH, "//h3[contains(text(), 'Seu código é:')]/code"))
            )
            codigo_mfa = codigo_element.text.strip()
            if codigo_mfa:
                print(f"🔐 Código MFA capturado: {codigo_mfa}")
                break
        except:
            time.sleep(1)
    else:
        raise Exception("❌ Tempo esgotado: Código MFA não foi encontrado!")

    codigo_input = wait.until(
        EC.visibility_of_element_located((By.ID, "text_input_3"))
    )
    codigo_input.send_keys(codigo_mfa)
    print("🔢 Código MFA preenchido!")


    print("⏳ Aguardando o botão 'Verificar Código' ficar clicável...")

    verificar_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[.//text()='✅ Verificar Código']"))
    )

    print("🖱️ Botão localizado. Indo até ele...")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", verificar_button)
    time.sleep(1)

    print("🖱️ Tentando clicar no botão...")
    try:
        # Tentativa 1: Clique normal com ActionChains
        ActionChains(driver).move_to_element(verificar_button).click().perform()
    except Exception as e:
        print("⚠️ Clique normal falhou. Usando clique via JavaScript...")
        # Tentativa 2: Clique via JavaScript
        driver.execute_script("arguments[0].click();", verificar_button)

    print("✅ Código verificado com sucesso!")
    time.sleep(2) 
    
    print("🔍 Aguardando mensagem de sucesso...")
    mensagem_sucesso = wait.until(
        EC.visibility_of_element_located((By.XPATH,
            "//div[@class='stAlert']//div[normalize-space()='✅ Código verificado com sucesso!']"))
    )

    assert mensagem_sucesso.is_displayed(), "❌ Mensagem de sucesso NÃO foi exibida!"
    print("✅ Mensagem validada com sucesso!")

except Exception as e:
    print("❌ Ocorreu um erro:", e)
    raise

finally:
    time.sleep(5)
    driver.quit()