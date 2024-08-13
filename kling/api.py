import os
import threading
from kling import BaseGen, TaskStatus
from typing import Optional
from fake_useragent import UserAgent


browser_version = "edge101"
ua = UserAgent(browsers=["edge"])
base_url = "https://klingai.kuaishou.com/"
base_url_not_cn = "https://klingai.com/"

class VideoApi(BaseGen):

    def _get_video_with_payload(self, payload: dict):
        response = self.session.post(
            self.submit_url,
            json=payload,
        )
        if not response.ok:
            print(response.text)
            raise Exception(f"Error response {str(response)}")
        response_body = response.json()
        if response_body.get("data").get("status") == 7:
            message = response_body.get("data").get("message")
            raise Exception(f"Request failed message {message}")
        task_id = response_body.get("data", {}).get("task", {}).get("id")

        if not task_id:
            raise Exception("Could not get request ID")
        # store the video id list
        self.video_id_list.append(task_id)
        return task_id


    def get_task(self, task_id: str, output_dir: str = "./output/"):
      
        response, status = self.fetch_metadata(task_id)
        if status == TaskStatus.PENDING:
            return "", status
        elif status == TaskStatus.FAILED:
            print("Request failed")
            return "", status
        else:
            result = []
            works = response.get("works", [])
            if not works:
                print("No video found.")
                return "", TaskStatus.FAILED
            else:
                for work in works:
                    resource = work.get("resource", {}).get("resource")
                    if resource:
                        result.append(resource)
                if not result:
                    print("No video found.")
                    return "", TaskStatus.FAILED
                
                link = result[0]
                if not os.path.exists(os.path.join(output_dir, f"{task_id}.mp4")):
                    response = self.session.get(link)
                    if response.status_code != 200:
                        raise Exception("Could not download image")
                    # save response to file
                    if not os.path.isdir(output_dir):
                        os.makedirs(output_dir)
                    with open(os.path.join(output_dir, f"{task_id}.mp4"), "wb") as output_file:
                        output_file.write(response.content)

                return f"{output_dir}/{task_id}.mp4", status

    def create_task(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        aspect_ratio: Optional[str] = "16:9",
        duration: Optional[int] = 5,
        is_high_quality: bool = False,
        auto_extend: bool = False,
    ):
        self.session.headers["user-agent"] = ua.random
        if image_path or image_url:
            if image_path:
                image_payload_url = self.image_uploader(image_path)
            else:
                image_payload_url = image_url
            if is_high_quality:
                model_type = "m2v_img2video_hq"
            else:
                model_type = "m2v_img2video"
            payload = {
                "arguments": [
                    {"name": "prompt", "value": prompt},
                    {
                        "name": "negative_prompt",
                        "value": "",
                    },
                    {
                        "name": "cfg",
                        "value": "0.5",
                    },
                    {
                        "name": "duration",
                        "value": duration,
                    },
                    {
                        "name": "aspect_ratio",
                        "value": aspect_ratio,
                    },
                    {
                        "name": "tail_image_enabled",
                        "value": "false",
                    },
                    {
                        "name": "camera_json",
                        "value": '{"type":"empty","horizontal":0,"vertical":0,"zoom":0,"tilt":0,"pan":0,"roll":0}',
                    },
                    {
                        "name": "biz",
                        "value": "klingai",
                    },
                ],
                "inputs": [
                    {
                        "inputType": "URL",
                        "url": image_payload_url,
                        "name": "input",
                    },
                ],
                "type": model_type,
            }

        else:
            if is_high_quality:
                model_type = "m2v_txt2video_hq"
            else:
                model_type = "m2v_txt2video"
            payload = {
                "arguments": [
                    {"name": "prompt", "value": prompt},
                    {
                        "name": "negative_prompt",
                        "value": "",
                    },
                    {
                        "name": "cfg",
                        "value": "0.5",
                    },
                    {
                        "name": "duration",
                        "value": duration,
                    },
                    {
                        "name": "aspect_ratio",
                        "value": aspect_ratio,
                    },
                    {
                        "name": "camera_json",
                        "value": '{"type":"empty","horizontal":0,"vertical":0,"zoom":0,"tilt":0,"pan":0,"roll":0}',
                    },
                    {
                        "name": "biz",
                        "value": "klingai",
                    },
                ],
                "inputs": [],
                "type": model_type,
            }
            return self._get_video_with_payload(payload)
        

class ImageApi(BaseGen):

    def get_task(self, task_id: str, output_dir: str = "./output/"):
    
        image_data, status = self.fetch_metadata(task_id)
        if status == TaskStatus.PENDING:
           return [], status
        elif status == TaskStatus.FAILED:
            print("Request failed")
            return [], TaskStatus.FAILED
        else:
            links = []
            works = image_data.get("works", [])
            if not works:
                print("No images found.")
                return []
            else:
                for work in works:
                    resource = work.get("resource", {}).get("resource")
                    if resource:
                        links.append(resource)


            def download_image(link: str, output_dir: str, filename: str) -> None:
                response = self.session.get(link)
                if response.status_code != 200:
                    raise Exception("Could not download image")
                # save response to file
                if not os.path.isdir(output_dir):
                    os.makedirs(output_dir)
                with open(os.path.join(output_dir, filename), "wb") as output_file:
                    output_file.write(response.content)

            threads = []

            png_index = 0
            paths = []
            for link in links:
                filename = f"{task_id}-{png_index}.png"
                filepath = os.path.join(output_dir, filename)
                paths.append(filepath)
                if not os.path.exists(filepath):
                    print(link)
                    thread = threading.Thread(target=download_image, args=(link, output_dir, filename))
                    threads.append(thread)
                    thread.start()
                    png_index += 1
            # Wait for all threads to complete
            for thread in threads:
                thread.join()

        return paths, status

    def create_task(
        self,
        prompt: str,
        count: int = 4,
        aspect_ratio: str = "1:1",
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,    
    ):
        self.session.headers["user-agent"] = ua.random
        if image_path or image_url:
            if image_path:
                image_payload_url = self.image_uploader(image_path)
            else:
                image_payload_url = image_url
            payload = {
                "arguments": [
                    {"name": "prompt", "value": prompt},
                    {
                        "name": "style",
                        "value": "默认",
                    },
                    {
                        "name": "aspect_ratio",
                        "value": aspect_ratio,
                    },
                    {
                        "name": "imageCount",
                        "value": count,
                    },
                    {
                        "name": "fidelity",
                        "value": "0.5",
                    },
                    {
                        "name": "biz",
                        "value": "klingai",
                    },
                ],
                "type": "mmu_img2img_aiweb",
                "inputs": [
                    {
                        "inputType": "URL",
                        "url": image_payload_url,
                        "name": "input",
                    },
                ],
            }
        else:
            payload = {
                "arguments": [
                    {
                        "name": "prompt",
                        "value": prompt,
                    },
                    {
                        "name": "style",
                        "value": "默认",
                    },
                    {
                        "name": "aspect_ratio",
                        "value": aspect_ratio,
                    },
                    {
                        "name": "imageCount",
                        "value": count,
                    },
                    {
                        "name": "biz",
                        "value": "klingai",
                    },
                ],
                "type": "mmu_txt2img_aiweb",
                "inputs": [],
            }

        response = self.session.post(
            self.submit_url,
            json=payload,
        )
        if not response.ok:
            print(response.text)
            raise Exception(f"Error response {str(response)}")
        response_body = response.json()
        if response_body.get("data").get("status") == 7:
            message = response_body.get("data").get("message")
            raise Exception(f"Request failed message {message}")
        task_id = (response_body.get("data", {}).get("task") or {}).get("id")
        if not task_id:
            raise Exception("Could not get request ID")
        
        return task_id