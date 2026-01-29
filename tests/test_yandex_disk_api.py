"""
Тесты для YandexDiskAPI.

Покрывают все основные методы API: GET, POST, PUT, DELETE
"""

import pytest
import time
from src.yandex_disk_api import YandexDiskAPI


@pytest.mark.api
@pytest.mark.smoke
class TestGetMethods:

    @pytest.mark.get
    def test_get_disk_info(self, api_client: YandexDiskAPI):
     
        response = api_client.get_disk_info()

        assert response is not None
        assert isinstance(response, dict)
        assert "total_space" in response
        assert "used_space" in response
        assert "trash_size" in response
        assert response["total_space"] > 0

    @pytest.mark.get
    def test_get_meta_info_root(self, api_client: YandexDiskAPI):

        response = api_client.get_meta_info("/")

        assert response is not None
        assert isinstance(response, dict)
        assert response.get("type") == "dir"
        assert "path" in response
        assert "name" in response

    @pytest.mark.get
    def test_get_files_list_root(self, api_client: YandexDiskAPI):
        
        response = api_client.get_files_list("/", limit=10)

        assert response is not None
        assert isinstance(response, dict)
        assert "_embedded" in response
        assert "items" in response["_embedded"]
        assert isinstance(response["_embedded"]["items"], list)


@pytest.mark.api
class TestPostMethods:

    @pytest.mark.post
    def test_create_folder(
        self,
        api_client: YandexDiskAPI,
        test_folder_name: str,
        cleanup_resources
    ):

        folder_path = f"/{test_folder_name}"

        response = api_client.create_folder(folder_path)
        cleanup_resources(folder_path)

        assert response is not None
        assert isinstance(response, dict)
        assert response.get("href") is not None


        meta_info = api_client.get_meta_info(folder_path)
        assert meta_info["type"] == "dir"
        assert meta_info["name"] == test_folder_name

    @pytest.mark.post
    def test_create_nested_folder(
        self,
        api_client: YandexDiskAPI,
        test_folder_name: str,
        cleanup_resources
    ):

        parent_folder = f"/{test_folder_name}"
        nested_folder = f"/{test_folder_name}/nested_folder"

        api_client.create_folder(parent_folder)
        cleanup_resources(parent_folder)

        response = api_client.create_folder(nested_folder)
        cleanup_resources(nested_folder)

        assert response is not None
        assert isinstance(response, dict)

        nested_meta = api_client.get_meta_info(nested_folder)
        assert nested_meta["type"] == "dir"
        assert nested_meta["name"] == "nested_folder"

    @pytest.mark.post
    def test_create_folder_already_exists(
        self,
        api_client: YandexDiskAPI,
        test_folder_name: str,
        cleanup_resources
    ):
  
        folder_path = f"/{test_folder_name}"


        api_client.create_folder(folder_path)
        cleanup_resources(folder_path)

        with pytest.raises(Exception):
            api_client.create_folder(folder_path, suppress_409_logging=True)


@pytest.mark.api
class TestPutMethods:

    @pytest.mark.put
    def test_upload_file(
        self,
        api_client: YandexDiskAPI,
        temp_file: str,
        test_file_name: str,
        cleanup_resources
    ):

        remote_path = f"/{test_file_name}"

        response = api_client.upload_file(temp_file, remote_path)
        cleanup_resources(remote_path)

        assert response is not None
        assert isinstance(response, dict)
        assert response["type"] == "file"
        assert response["name"] == test_file_name

        meta_info = api_client.get_meta_info(remote_path)
        assert meta_info["type"] == "file"
        assert meta_info["size"] > 0

    @pytest.mark.put
    def test_upload_file_overwrite(
        self,
        api_client: YandexDiskAPI,
        temp_file: str,
        test_file_name: str,
        cleanup_resources
    ):
       
        remote_path = f"/{test_file_name}"
    
        api_client.upload_file(temp_file, remote_path, overwrite=False)
        cleanup_resources(remote_path)

        with open(temp_file, "w", encoding="utf-8") as f:
            f.write("Обновленное содержимое файла")

        response = api_client.upload_file(temp_file, remote_path, overwrite=True)

        assert response is not None
        assert response["type"] == "file"

    @pytest.mark.put
    def test_upload_file_to_folder(
        self,
        api_client: YandexDiskAPI,
        temp_file: str,
        test_folder_name: str,
        cleanup_resources
    ):

        folder_path = f"/{test_folder_name}"
        file_path = f"/{test_folder_name}/file_in_folder.txt"

        api_client.create_folder(folder_path)
        cleanup_resources(folder_path)

        response = api_client.upload_file(temp_file, file_path)
        cleanup_resources(file_path)

        assert response is not None
        assert response["type"] == "file"

        folder_content = api_client.get_files_list(folder_path)
        file_names = [item["name"] for item in folder_content["_embedded"]["items"]]
        assert "file_in_folder.txt" in file_names


@pytest.mark.api
class TestDeleteMethods:

    @pytest.mark.delete
    def test_delete_file(
        self,
        api_client: YandexDiskAPI,
        temp_file: str,
        test_file_name: str
    ):

        remote_path = f"/{test_file_name}"

        api_client.upload_file(temp_file, remote_path)

        response = api_client.delete_resource(remote_path, permanently=True)

        assert response is not None
        assert isinstance(response, dict)

        # Проверяем, что файл удален (ожидаем 404)
        # Используем suppress_404_logging=True, чтобы не логировать ожидаемую ошибку
        with pytest.raises(Exception):
            api_client.get_meta_info(remote_path, suppress_404_logging=True)

    @pytest.mark.delete
    def test_delete_folder(
        self,
        api_client: YandexDiskAPI,
        test_folder_name: str
    ):

        folder_path = f"/{test_folder_name}"

        api_client.create_folder(folder_path)

        response = api_client.delete_resource(folder_path, permanently=True)

        assert response is not None

        # Проверяем, что папка удалена (ожидаем 404)
        with pytest.raises(Exception):
            api_client.get_meta_info(folder_path, suppress_404_logging=True)

    @pytest.mark.delete
    def test_delete_folder_with_files(
        self,
        api_client: YandexDiskAPI,
        temp_file: str,
        test_folder_name: str
    ):

        folder_path = f"/{test_folder_name}"
        file_path = f"/{test_folder_name}/file.txt"

        api_client.create_folder(folder_path)
        api_client.upload_file(temp_file, file_path)

        response = api_client.delete_resource(folder_path, permanently=True)

        assert response is not None

        # Проверяем, что папка удалена (ожидаем 404)
        with pytest.raises(Exception):
            api_client.get_meta_info(folder_path, suppress_404_logging=True)

    @pytest.mark.delete
    def test_delete_move_to_trash(
        self,
        api_client: YandexDiskAPI,
        temp_file: str,
        test_file_name: str
    ):

        remote_path = f"/{test_file_name}"

        api_client.upload_file(temp_file, remote_path)

        response = api_client.delete_resource(remote_path, permanently=False)

        assert response is not None

        with pytest.raises(Exception):
            api_client.get_meta_info(remote_path, suppress_404_logging=True)


@pytest.mark.api
class TestIntegration:

    @pytest.mark.smoke
    def test_full_workflow(
        self,
        api_client: YandexDiskAPI,
        temp_file: str,
        test_folder_name: str,
        cleanup_resources
    ):
 
        folder_path = f"/{test_folder_name}"
        file_path = f"/{test_folder_name}/workflow_test.txt"

        #  Создаем папку
        api_client.create_folder(folder_path)
        cleanup_resources(folder_path)

        #  Проверяем, что папка создана
        folder_info = api_client.get_meta_info(folder_path)
        assert folder_info["type"] == "dir"

        #  Загружаем файл в папку
        api_client.upload_file(temp_file, file_path)
        cleanup_resources(file_path)

        #  Проверяем содержимое папки
        folder_content = api_client.get_files_list(folder_path)
        assert len(folder_content["_embedded"]["items"]) > 0

        # Проверяем метаинформацию файла
        file_info = api_client.get_meta_info(file_path)
        assert file_info["type"] == "file"

        #  Удаляем файл
        api_client.delete_resource(file_path, permanently=True)

        #  Проверяем, что файл удален
        folder_content_after = api_client.get_files_list(folder_path)
        file_names = [item["name"] for item in folder_content_after["_embedded"]["items"]]
        assert "workflow_test.txt" not in file_names

    def test_multiple_files_operations(
        self,
        api_client: YandexDiskAPI,
        temp_file: str,
        test_folder_name: str,
        cleanup_resources
    ):
        
        folder_path = f"/{test_folder_name}"
        file1_path = f"/{test_folder_name}/file1.txt"
        file2_path = f"/{test_folder_name}/file2.txt"
        file3_path = f"/{test_folder_name}/file3.txt"

        # Создаем папку
        api_client.create_folder(folder_path)
        cleanup_resources(folder_path)

        # Загружаем несколько файлов
        api_client.upload_file(temp_file, file1_path)
        cleanup_resources(file1_path)
        time.sleep(0.5)  # Небольшая задержка между загрузками

        api_client.upload_file(temp_file, file2_path)
        cleanup_resources(file2_path)
        time.sleep(0.5)

        api_client.upload_file(temp_file, file3_path)
        cleanup_resources(file3_path)

        # Проверяем список файлов
        folder_content = api_client.get_files_list(folder_path)
        file_names = [item["name"] for item in folder_content["_embedded"]["items"]]
        
        assert "file1.txt" in file_names
        assert "file2.txt" in file_names
        assert "file3.txt" in file_names
        assert len(folder_content["_embedded"]["items"]) >= 3
