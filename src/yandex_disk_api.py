import os
import time
import logging
from typing import Optional, Dict, Any
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class YandexDiskAPI:

    BASE_URL = "https://cloud-api.yandex.net/v1/disk"

    def __init__(self, token: str):
        
        self.token = token
        self.headers = {
            "Authorization": f"OAuth {token}",
            "Content-Type": "application/json"
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[bytes] = None,
        timeout: int = 30,
        suppress_404_logging: bool = False,
        suppress_409_logging: bool = False
    ) -> requests.Response:
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        logger.debug(f"Выполняю запрос: {method} {url}")
        if params:
            logger.debug(f"   Параметры: {params}")
        if json_data:
            logger.debug(f"   JSON данные: {json_data}")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data,
                data=data,
                timeout=timeout
            )
            logger.debug(f"Ответ получен: {response.status_code} {response.reason}")
            
            if suppress_404_logging and response.status_code == 404:
                logger.debug(f"   Ресурс не найден (ожидаемо): {url}")
            elif suppress_409_logging and response.status_code == 409:
                logger.debug(f"   Конфликт (ожидаемо, ресурс уже существует): {url}")
            
            response.raise_for_status()
            return response
        except RequestException as e:
       
            error_str = str(e)
            if suppress_404_logging and "404" in error_str:
                logger.debug(f"   Ресурс не найден (ожидаемо): {url}")
            elif suppress_409_logging and "409" in error_str:
                logger.debug(f"  Конфликт (ожидаемо, ресурс уже существует): {url}")
            else:
                logger.error(f" Ошибка при выполнении запроса {method} {url}: {error_str}")
            
            raise RequestException(
                f"Ошибка при выполнении запроса {method} {url}: {str(e)}"
            ) from e

    def get_disk_info(self) -> Dict[str, Any]:

        response = self._make_request("GET", "/")
        result = response.json()

        logger.info(f"   Диск: {result.get('total_space', 0) / (1024**3):.2f} GB всего, "
                   f"{result.get('used_space', 0) / (1024**3):.2f} GB использовано")

        return result

    def get_meta_info(self, path: str, suppress_404_logging: bool = False) -> Dict[str, Any]:
        

        params = {"path": path}
        response = self._make_request("GET", "/resources", params=params, suppress_404_logging=suppress_404_logging)
        result = response.json()

        logger.debug(f"   Тип: {result.get('type')}, Размер: {result.get('size', 'N/A')} bytes")

        return result

    def get_files_list(self, path: str = "/", limit: int = 20) -> Dict[str, Any]:
    
        params = {"path": path, "limit": limit}
        response = self._make_request("GET", "/resources", params=params)

        return response.json()

    def create_folder(self, path: str, suppress_409_logging: bool = False) -> Dict[str, Any]:

        params = {"path": path}
        response = self._make_request("PUT", "/resources", params=params, suppress_409_logging=suppress_409_logging)
        result = response.json()

        logger.info(f"   Папка создана: {result.get('href', 'N/A')}")
        return result

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
      
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Файл не найден: {local_path}")

        file_size = os.path.getsize(local_path)
        logger.info(f" Загружаем файл: {local_path} -> {remote_path} ({file_size} bytes)")

        params = {
            "path": remote_path,
            "overwrite": str(overwrite).lower()
        }

        response = self._make_request("GET", "/resources/upload", params=params)
        upload_url = response.json()["href"]

        logger.debug(f"  URL для загрузки получен: {upload_url}")

        with open(local_path, "rb") as file:
            upload_response = requests.put(
                upload_url,
                data=file,
                timeout=30
            )
            upload_response.raise_for_status()
   
        max_wait_time = 5.0
        check_interval = 0.5
        elapsed_time = 0.0
        
        while elapsed_time < max_wait_time:
            try:

                meta_info = self.get_meta_info(remote_path, suppress_404_logging=True)
                return meta_info

            except RequestException:

                time.sleep(check_interval)
                elapsed_time += check_interval
        
        return self.get_meta_info(remote_path)

    def upload_file_from_url(
        self,
        file_url: str,
        remote_path: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:

        logger.info(f" Загружаем файл по URL: {file_url} -> {remote_path}")

        params = {
            "path": remote_path,
            "url": file_url,
            "overwrite": str(overwrite).lower()
        }

        response = self._make_request("POST", "/resources/upload", params=params)
        result = response.json()

        return result

    def delete_resource(
        self,
        path: str,
        permanently: bool = False,
        suppress_404_logging: bool = False
    ) -> Dict[str, Any]:
       
        params = {
            "path": path,
            "permanently": str(permanently).lower()
        }

        response = self._make_request("DELETE", "/resources", params=params, suppress_404_logging=suppress_404_logging)

        if permanently:
            max_wait_time = 5.0  
            check_interval = 0.5  
            elapsed_time = 0.0
            
            while elapsed_time < max_wait_time:
                try:

                    self.get_meta_info(path, suppress_404_logging=True)
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                except RequestException:
    
                    break

        if response.status_code == 204:
            return {"status": "success", "message": "Resource deleted"}

        return response.json()

    def clean_trash(self) -> Dict[str, Any]:
   
        response = self._make_request("DELETE", "/trash/resources")
        
        if response.status_code == 204:
            return {"status": "success", "message": "Trash cleaned"}
        
        return response.json()
