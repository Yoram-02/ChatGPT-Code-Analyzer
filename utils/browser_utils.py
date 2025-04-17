import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

def setup_browser():
    """
    Configure et lance un navigateur Chrome en mode non détecté
    
    Returns:
        driver: Instance du navigateur ou None en cas d'échec
    """
    try:
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
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