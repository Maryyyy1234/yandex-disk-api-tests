import os
import logging
import pytest
from dotenv import load_dotenv
from src.yandex_disk_api import YandexDiskAPI

load_dotenv()


logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)


@pytest.fixture(scope="session")
def yandex_token() -> str:

    token = os.getenv("YANDEX_DISK_TOKEN")
    if not token:
        raise ValueError(
            "YANDEX_DISK_TOKEN не найден в переменных окружения. "
            "Создайте файл .env и добавьте токен."
        )
    return token


@pytest.fixture(scope="session")
def api_client(yandex_token: str) -> YandexDiskAPI:
   
    return YandexDiskAPI(yandex_token)


@pytest.fixture(scope="function")
def test_folder_name() -> str:

    import time
    return f"test_folder_{int(time.time())}"


@pytest.fixture(scope="function")
def test_file_name() -> str:

    import time
    return f"test_file_{int(time.time())}.txt"


@pytest.fixture(scope="function")
def cleanup_resources(api_client: YandexDiskAPI):

    resources_to_delete = []

    def register_for_cleanup(path: str):

        resources_to_delete.append(path)

    yield register_for_cleanup

   
    for resource_path in reversed(resources_to_delete):
        try:
        
            api_client.delete_resource(resource_path, permanently=True, suppress_404_logging=True)
        except Exception as e:
           
            error_str = str(e)
            if "404" not in error_str and "NOT FOUND" not in error_str:
       
                print(f"⚠️  Не удалось удалить ресурс {resource_path}: {e}")


@pytest.fixture(scope="function")
def temp_file(tmp_path):

    test_file = tmp_path / "test_upload.txt"
    test_file.write_text("Это тестовый файл для загрузки на Яндекс.Диск")
    return str(test_file)
