import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

def setup_browser():
    """
    Configure et lance un navigateur Chrome en mode non détecté
    
    Returns:
        driver: Instance du navigateur ou None en cas d'échec
    """
    try:
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-popup-blocking")

        driver = uc.Chrome(driver_executable_path=ChromeDriverManager().install(), options=options)
        driver.get("https://chat.openai.com/")
        return driver
    except Exception as e:
        print(f"Erreur lors du lancement du navigateur: {str(e)}")
        return None

def is_browser_alive(driver):
    """
    Vérifie si le navigateur est toujours actif
    
    Args:
        driver: L'instance du driver Selenium
        
    Returns:
        bool: True si le navigateur est toujours actif, False sinon
    """
    if driver is None:
        return False
        
    try:
        # Tenter d'accéder à une propriété du navigateur pour voir s'il est toujours actif
        current_window = driver.current_window_handle
        return True
    except WebDriverException:
        return False
    except Exception:
        return False
    
def open_new_tab(driver):
    """
    Ouvre un nouvel onglet dans le navigateur
    
    Args:
        driver: L'instance du driver Selenium
        
    Returns:
        str: Handle de l'onglet créé ou None en cas d'échec
    """
    try:
        # Mémoriser les onglets actuels
        original_window = driver.current_window_handle
        old_handles = driver.window_handles
        
        # Ouvrir un nouvel onglet (Ctrl+T)
        # body = driver.find_element(By.TAG_NAME, 'body')
        # body.send_keys(Keys.CONTROL + 't')
        driver.execute_script("window.open('about:blank', '_blank');")
        # Attendre que le nouvel onglet soit ouvert
        time.sleep(2)
        
        # Trouver le nouvel onglet
        new_handles = [handle for handle in driver.window_handles if handle not in old_handles]
        if new_handles:
            new_tab = new_handles[0]
            driver.switch_to.window(new_tab)
            driver.get("https://chat.openai.com/")
            return new_tab
            
        return None
    except Exception as e:
        print(f"Erreur lors de l'ouverture d'un nouvel onglet: {str(e)}")
        return None

def switch_to_tab(driver, tab_handle):
    """
    Bascule vers un onglet spécifique
    
    Args:
        driver: L'instance du driver Selenium
        tab_handle: Handle de l'onglet cible
        
    Returns:
        bool: True si la bascule a réussi, False sinon
    """
    try:
        if tab_handle in driver.window_handles:
            driver.switch_to.window(tab_handle)
            return True
        return False
    except Exception as e:
        print(f"Erreur lors du changement d'onglet: {str(e)}")
        return False