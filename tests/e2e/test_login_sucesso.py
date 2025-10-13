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

    success_message = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Login realizado com sucesso')]"))
    )
    assert success_message.is_displayed(), "Mensagem de sucesso não encontrada!"
    print("✅ Login realizado com sucesso!")

except Exception as e:
    print("❌ Erro durante o teste:", e)
    raise
finally:
    time.sleep(3)
    driver.quit()