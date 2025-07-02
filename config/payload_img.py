import random


def random_13_digits():
    # Generate a random 13-digit number
    return random.randint(1000000000000, 9999999999999)


def get_payload(positive_prompt, width=720, height=1024):
    """Return the payload for image generation."""
    return {
        "client_id": "2d5ffcaee954433a9c742366e2206f86",
        "prompt": {
            "3": {
                "inputs": {
                    "seed": random_13_digits(),
                    "steps": 40,
                    "cfg": 7,
                    "sampler_name": "dpmpp_3m_sde",
                    "scheduler": "karras",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"},
            },
            "4": {
                "inputs": {"ckpt_name": "4T.safetensors"},
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"},
            },
            "5": {
                "inputs": {"width": width, "height": height, "batch_size": 1},
                "class_type": "EmptyLatentImage",
                "_meta": {"title": "Empty Latent Image"},
            },
            "6": {
                "inputs": {"text": positive_prompt, "clip": ["4", 1]},
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"},
            },
            "7": {
                "inputs": {
                    "text": "score_4,score_5,score_6,lowres,low quality,ugly,deformed,bad anatomy,extra fingers,username,text,logo,watermark,cross-eyed,censored,muscular,(chains:1.2),bad teeth,crooked teeth,discolored teeth,deformed teeth,bad feet,deformed feet,extra toes",
                    "clip": ["4", 1],
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"},
            },
            "8": {
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"},
            },
            "12": {
                "inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]},
                "class_type": "SaveImage",
                "_meta": {"title": "Save Image"},
            },
        },
        "extra_data": {
            "auth_token_comfy_org": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImE0YTEwZGVjZTk4MzY2ZDZmNjNlMTY3Mjg2YWU5YjYxMWQyYmFhMjciLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiVHJ1bmcgVsawxqFuZyIsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NKSHRhVzhnNjNmV0p1MUdyZ1VmQW1Kc2h1ZWJNcC11S205S0JmWDF0SXV4R0lHdGFjVD1zOTYtYyIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9kcmVhbWJvb3RoeSIsImF1ZCI6ImRyZWFtYm9vdGh5IiwiYXV0aF90aW1lIjoxNzQ5NjcwNzc1LCJ1c2VyX2lkIjoiT1NuU3B6QjBwamh5R0JwaDlSaE9jeG9qVzBCMiIsInN1YiI6Ik9TblNwekIwcGpoeUdCcGg5UmhPY3hvalcwQjIiLCJpYXQiOjE3NTAyMzA2NzMsImV4cCI6MTc1MDIzNDI3MywiZW1haWwiOiJ0cnVuZ3Z1b25nNTI4QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7Imdvb2dsZS5jb20iOlsiMTExNTg1NjAwOTA4MTkyMzk1MTMxIl0sImVtYWlsIjpbInRydW5ndnUvb25nNTI4QGdtYWlsLmNvbSJdfSwic2lnbi1pbl9wcm92aWRlciI6Imdvb2dsZS5jb20ifX0.DqGGy8_uTjLUnHRpZ3QEXP8oCOeV1s-PSQQuhf_Nl8lnJ6VGthpdSMZo7_V85oZlGLbGfPYMVkZn6s_MChyGLCFJGaAzFazgCNgWbBjWs8xqcg2J0_rgUk0FbDT_g0As5GKZ2ZeNgEbZLCC_bxidqxdEAdk6vFAt_hsvm20oCYj0hYibwfI2j6pPdiZ1zS9UWp_A7LHSE76JeWAufikH2m4EBN8DLAjnmTmebwG6E_ijY0qN_UFOTp3uQNv9lanDZzru6hjICpfq1BtCXEMFNueWl_LoiUxJMHX3JHmYiqfI41FKABUFFEtJiUKv2HmRhaXu0huxfahGiwKtrf8M_w",
            "extra_pnginfo": {
                "workflow": {
                    "id": "db111623-c664-47dc-9f7e-26e56ed3d83d",
                    "revision": 0,
                    "last_node_id": 12,
                    "last_link_id": 11,
                    "nodes": [
                        {
                            "id": 4,
                            "type": "CheckpointLoaderSimple",
                            "pos": [26, 474],
                            "size": [315, 98],
                            "flags": {},
                            "order": 0,
                            "mode": 0,
                            "inputs": [],
                            "outputs": [
                                {
                                    "label": "Mô hình",
                                    "name": "MODEL",
                                    "type": "MODEL",
                                    "slot_index": 0,
                                    "links": [1],
                                },
                                {
                                    "label": "CLIP",
                                    "name": "CLIP",
                                    "type": "CLIP",
                                    "slot_index": 1,
                                    "links": [3, 5],
                                },
                                {
                                    "label": "VAE",
                                    "name": "VAE",
                                    "type": "VAE",
                                    "slot_index": 2,
                                    "links": [8],
                                },
                            ],
                            "properties": {
                                "cnr_id": "comfy-core",
                                "ver": "0.3.18",
                                "Node name for S&R": "CheckpointLoaderSimple",
                            },
                            "widgets_values": ["4T.safetensors"],
                        },
                        {
                            "id": 7,
                            "type": "CLIPTextEncode",
                            "pos": [413, 389],
                            "size": [425.27801513671875, 180.6060791015625],
                            "flags": {},
                            "order": 3,
                            "mode": 0,
                            "inputs": [
                                {
                                    "label": "CLIP",
                                    "name": "clip",
                                    "type": "CLIP",
                                    "link": 5,
                                }
                            ],
                            "outputs": [
                                {
                                    "label": "Điều kiện",
                                    "name": "CONDITIONING",
                                    "type": "CONDITIONING",
                                    "slot_index": 0,
                                    "links": [6],
                                }
                            ],
                            "properties": {
                                "cnr_id": "comfy-core",
                                "ver": "0.3.18",
                                "Node name for S&R": "CLIPTextEncode",
                            },
                            "widgets_values": [
                                "score_4,score_5,score_6,lowres,low quality,ugly,deformed,bad anatomy,extra fingers,username,text,logo,watermark,cross-eyed,censored,muscular,(chains:1.2),bad teeth,crooked teeth,discolored teeth,deformed teeth,bad feet,deformed feet,extra toes"
                            ],
                        },
                        {
                            "id": 3,
                            "type": "KSampler",
                            "pos": [863, 186],
                            "size": [315, 262],
                            "flags": {},
                            "order": 4,
                            "mode": 0,
                            "inputs": [
                                {
                                    "label": "Mô hình",
                                    "name": "model",
                                    "type": "MODEL",
                                    "link": 1,
                                },
                                {
                                    "label": "Điều kiện tích cực",
                                    "name": "positive",
                                    "type": "CONDITIONING",
                                    "link": 4,
                                },
                                {
                                    "label": "Điều kiện tiêu cực",
                                    "name": "negative",
                                    "type": "CONDITIONING",
                                    "link": 6,
                                },
                                {
                                    "label": "Tiềm ẩn",
                                    "name": "latent_image",
                                    "type": "LATENT",
                                    "link": 2,
                                },
                            ],
                            "outputs": [
                                {
                                    "label": "Tiềm ẩn",
                                    "name": "LATENT",
                                    "type": "LATENT",
                                    "slot_index": 0,
                                    "links": [7],
                                }
                            ],
                            "properties": {
                                "cnr_id": "comfy-core",
                                "ver": "0.3.18",
                                "Node name for S&R": "KSampler",
                            },
                            "widgets_values": [
                                random_13_digits(),
                                "randomize",
                                40,
                                7,
                                "dpmpp_3m_sde",
                                "karras",
                                1,
                            ],
                        },
                        {
                            "id": 8,
                            "type": "VAEDecode",
                            "pos": [1209, 188],
                            "size": [210, 46],
                            "flags": {},
                            "order": 5,
                            "mode": 0,
                            "inputs": [
                                {
                                    "label": "Tiềm ẩn",
                                    "name": "samples",
                                    "type": "LATENT",
                                    "link": 7,
                                },
                                {
                                    "label": "VAE",
                                    "name": "vae",
                                    "type": "VAE",
                                    "link": 8,
                                },
                            ],
                            "outputs": [
                                {
                                    "label": "Hình ảnh",
                                    "name": "IMAGE",
                                    "type": "IMAGE",
                                    "slot_index": 0,
                                    "links": [11],
                                }
                            ],
                            "properties": {
                                "cnr_id": "comfy-core",
                                "ver": "0.3.18",
                                "Node name for S&R": "VAEDecode",
                            },
                            "widgets_values": [],
                        },
                        {
                            "id": 12,
                            "type": "SaveImage",
                            "pos": [1452.8531494140625, 185.96144104003906],
                            "size": [270, 58],
                            "flags": {},
                            "order": 6,
                            "mode": 0,
                            "inputs": [{"name": "images", "type": "IMAGE", "link": 11}],
                            "outputs": [],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40"},
                            "widgets_values": ["ComfyUI"],
                        },
                        {
                            "id": 6,
                            "type": "CLIPTextEncode",
                            "pos": [415, 186],
                            "size": [422.84503173828125, 164.31304931640625],
                            "flags": {},
                            "order": 2,
                            "mode": 0,
                            "inputs": [
                                {
                                    "label": "CLIP",
                                    "name": "clip",
                                    "type": "CLIP",
                                    "link": 3,
                                }
                            ],
                            "outputs": [
                                {
                                    "label": "Điều kiện",
                                    "name": "CONDITIONING",
                                    "type": "CONDITIONING",
                                    "slot_index": 0,
                                    "links": [4],
                                }
                            ],
                            "properties": {
                                "cnr_id": "comfy-core",
                                "ver": "0.3.18",
                                "Node name for S&R": "CLIPTextEncode",
                            },
                            "widgets_values": [positive_prompt],
                        },
                        {
                            "id": 5,
                            "type": "EmptyLatentImage",
                            "pos": [473, 609],
                            "size": [315, 106],
                            "flags": {},
                            "order": 1,
                            "mode": 0,
                            "inputs": [],
                            "outputs": [
                                {
                                    "label": "Tiềm ẩn",
                                    "name": "LATENT",
                                    "type": "LATENT",
                                    "slot_index": 0,
                                    "links": [2],
                                }
                            ],
                            "properties": {
                                "cnr_id": "comfy-core",
                                "ver": "0.3.18",
                                "Node name for S&R": "EmptyLatentImage",
                            },
                            "widgets_values": [width, height, 1],
                        },
                    ],
                    "links": [
                        [1, 4, 0, 3, 0, "MODEL"],
                        [2, 5, 0, 3, 3, "LATENT"],
                        [3, 4, 1, 6, 0, "CLIP"],
                        [4, 6, 0, 3, 1, "CONDITIONING"],
                        [5, 4, 1, 7, 0, "CLIP"],
                        [6, 7, 0, 3, 2, "CONDITIONING"],
                        [7, 3, 0, 8, 0, "LATENT"],
                        [8, 4, 2, 8, 1, "VAE"],
                        [11, 8, 0, 12, 0, "IMAGE"],
                    ],
                    "groups": [],
                    "config": {},
                    "extra": {
                        "ds": {
                            "scale": 0.9229599817706574,
                            "offset": [78.93082093649174, -78.77906810733931],
                        },
                        "VHS_latentpreview": False,
                        "VHS_latentpreviewrate": 0,
                        "VHS_MetadataImage": True,
                        "VHS_KeepIntermediate": True,
                        "frontendVersion": "1.21.7",
                    },
                    "version": 0.4,
                }
            },
        },
    }


def get_payload_img2img(positive_prompt, img_path):
    """Return the payload for img2img generation."""
    return {
        {
            "client_id": "6db042d14d874c3db129e19dc8c17801",
            "prompt": {
                "3": {
                    "inputs": {
                        "seed": random_13_digits(),
                        "steps": 40,
                        "cfg": 7,
                        "sampler_name": "dpmpp_3m_sde",
                        "scheduler": "karras",
                        "denoise": 0.8700000000000001,
                        "model": ["14", 0],
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "latent_image": ["12", 0],
                    },
                    "class_type": "KSampler",
                    "_meta": {"title": "KSampler"},
                },
                "6": {
                    "inputs": {"text": positive_prompt.strip(), "clip": ["14", 1]},
                    "class_type": "CLIPTextEncode",
                    "_meta": {"title": "CLIP Text Encode (Prompt)"},
                },
                "7": {
                    "inputs": {
                        "text": "score_4,score_5,score_6,lowres,low quality,ugly,deformed,bad anatomy,extra fingers,username,text,logo,watermark,cross-eyed,censored,muscular,(chains:1.2),bad teeth,crooked teeth,discolored teeth,deformed teeth,bad feet,deformed feet,extra toes",
                        "clip": ["14", 1],
                    },
                    "class_type": "CLIPTextEncode",
                    "_meta": {"title": "CLIP Text Encode (Prompt)"},
                },
                "8": {
                    "inputs": {"samples": ["3", 0], "vae": ["14", 2]},
                    "class_type": "VAEDecode",
                    "_meta": {"title": "VAE Decode"},
                },
                "10": {
                    "inputs": {"image": img_path.strip()},
                    "class_type": "LoadImage",
                    "_meta": {"title": "Load Image"},
                },
                "12": {
                    "inputs": {"pixels": ["10", 0], "vae": ["14", 2]},
                    "class_type": "VAEEncode",
                    "_meta": {"title": "VAE Encode"},
                },
                "14": {
                    "inputs": {"ckpt_name": "4T.safetensors"},
                    "class_type": "CheckpointLoaderSimple",
                    "_meta": {"title": "Load Checkpoint"},
                },
                "18": {
                    "inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]},
                    "class_type": "SaveImage",
                    "_meta": {"title": "Save Image"},
                },
            },
            "extra_data": {
                "auth_token_comfy_org": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjNiZjA1MzkxMzk2OTEzYTc4ZWM4MGY0MjcwMzM4NjM2NDA2MTBhZGMiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiVHJ1bmcgVsawxqFuZyIsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NKSHRhVzhnNjNmV0p1MUdyZ1VmQW1Kc2h1ZWJNcC11S205S0JmWDF0SXV4R0lHdGFjVD1zOTYtYyIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9kcmVhbWJvb3RoeSIsImF1ZCI6ImRyZWFtYm9vdGh5IiwiYXV0aF90aW1lIjoxNzQ5NjcwNzc1LCJ1c2VyX2lkIjoiT1NuU3B6QjBwamh5R0JwaDlSaE9jeG9qVzBCMiIsInN1YiI6Ik9TblNwekIwcGpoeUdCcGg5UmhPY3hvalcwQjIiLCJpYXQiOjE3NTEwNzQ3MjYsImV4cCI6MTc1MTA3ODMyNiwiZW1haWwiOiJ0cnVuZ3Z1b25nNTI4QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7Imdvb2dsZS5jb20iOlsiMTExNTg1NjAwOTA4MTkyMzk1MTMxIl0sImVtYWlsIjpbInRydW5ndnVvbmc1MjhAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.n7K0ZAHIzgOARAsi6hLGqhPzPM2KdlloZbL69FrDh2KqTi-EUtEw1bssPnxVvdtoZhOhOrtc37Yw6nVaKK2vOZCyXg5hewLcha0hyj4iNI9qdR2YesMau_PsIjAyfaYaq9I3G7NkRjH_eNW9EZ5tHooTOWbiP5CdTu2WeYDgJrQ8352V3PuBFzqh6ZBxDoFoBTUZRa63qxwzj6sOYQ_FodeSqJpLwfRpC86unx_-0e4ZXcyHBGWowc3bRYXdyiyNOCM3Bou5k7649I3bInYre9eS_YTJOZy36Jn1zqO2TuBQ-80iyJOCgyTAcYcxTjJBsse7IXNV2IgO-pHGppdjwg",
                "extra_pnginfo": {
                    "workflow": {
                        "id": "7cb6261d-3b03-4171-bbd1-a4b256b42404",
                        "revision": 0,
                        "last_node_id": 18,
                        "last_link_id": 19,
                        "nodes": [
                            {
                                "id": 8,
                                "type": "VAEDecode",
                                "pos": [1209, 188],
                                "size": [210, 46],
                                "flags": {},
                                "order": 7,
                                "mode": 0,
                                "inputs": [
                                    {"name": "samples", "type": "LATENT", "link": 7},
                                    {"name": "vae", "type": "VAE", "link": 17},
                                ],
                                "outputs": [
                                    {
                                        "name": "IMAGE",
                                        "type": "IMAGE",
                                        "slot_index": 0,
                                        "links": [19],
                                    }
                                ],
                                "properties": {
                                    "cnr_id": "comfy-core",
                                    "ver": "0.3.40",
                                    "Node name for S&R": "VAEDecode",
                                },
                                "widgets_values": [],
                            },
                            {
                                "id": 12,
                                "type": "VAEEncode",
                                "pos": [585.1956787109375, 685.038818359375],
                                "size": [210, 46],
                                "flags": {},
                                "order": 5,
                                "mode": 0,
                                "inputs": [
                                    {"name": "pixels", "type": "IMAGE", "link": 10},
                                    {"name": "vae", "type": "VAE", "link": 16},
                                ],
                                "outputs": [
                                    {
                                        "name": "LATENT",
                                        "type": "LATENT",
                                        "slot_index": 0,
                                        "links": [11],
                                    }
                                ],
                                "properties": {
                                    "cnr_id": "comfy-core",
                                    "ver": "0.3.40",
                                    "Node name for S&R": "VAEEncode",
                                },
                                "widgets_values": [],
                            },
                            {
                                "id": 16,
                                "type": "MarkdownNote",
                                "pos": [-290.15606689453125, 191.5925750732422],
                                "size": [314.95745849609375, 133.0336456298828],
                                "flags": {},
                                "order": 0,
                                "mode": 0,
                                "inputs": [],
                                "outputs": [],
                                "properties": {},
                                "widgets_values": [
                                    "[Tutorials](https://docs.comfy.org/tutorials/basic/text-to-image)|[教程](https://docs.comfy.org/zh-CN/tutorials/basic/text-to-image)\n\nDownload  [v1-5-pruned-emaonly-fp16.safetensors](https://huggingface.co/Comfy-Org/stable-diffusion-v1-5-archive/resolve/main/v1-5-pruned-emaonly-fp16.safetensors?download=true) and save it in  **ComfyUI/models/checkpoints** \n\n---\n\n下载 [v1-5-pruned-emaonly-fp16.safetensors](https://huggingface.co/Comfy-Org/stable-diffusion-v1-5-archive/resolve/main/v1-5-pruned-emaonly-fp16.safetensors?download=true) 并保存到 **ComfyUI/models/checkpoints** 文件夹下"
                                ],
                                "color": "#432",
                                "bgcolor": "#653",
                            },
                            {
                                "id": 14,
                                "type": "CheckpointLoaderSimple",
                                "pos": [53.31755065917969, 191.36024475097656],
                                "size": [315, 98],
                                "flags": {},
                                "order": 1,
                                "mode": 0,
                                "inputs": [],
                                "outputs": [
                                    {
                                        "name": "MODEL",
                                        "type": "MODEL",
                                        "slot_index": 0,
                                        "links": [13],
                                    },
                                    {
                                        "name": "CLIP",
                                        "type": "CLIP",
                                        "slot_index": 1,
                                        "links": [14, 15],
                                    },
                                    {
                                        "name": "VAE",
                                        "type": "VAE",
                                        "slot_index": 2,
                                        "links": [16, 17],
                                    },
                                ],
                                "properties": {
                                    "cnr_id": "comfy-core",
                                    "ver": "0.3.40",
                                    "Node name for S&R": "CheckpointLoaderSimple",
                                    "models": [
                                        {
                                            "name": "v1-5-pruned-emaonly-fp16.safetensors",
                                            "url": "https://huggingface.co/Comfy-Org/stable-diffusion-v1-5-archive/resolve/main/v1-5-pruned-emaonly-fp16.safetensors?download=true",
                                            "directory": "checkpoints",
                                        }
                                    ],
                                },
                                "widgets_values": ["4T.safetensors"],
                                "color": "#322",
                                "bgcolor": "#533",
                            },
                            {
                                "id": 7,
                                "type": "CLIPTextEncode",
                                "pos": [413, 389],
                                "size": [425.27801513671875, 180.6060791015625],
                                "flags": {},
                                "order": 4,
                                "mode": 0,
                                "inputs": [
                                    {"name": "clip", "type": "CLIP", "link": 15}
                                ],
                                "outputs": [
                                    {
                                        "name": "CONDITIONING",
                                        "type": "CONDITIONING",
                                        "slot_index": 0,
                                        "links": [6],
                                    }
                                ],
                                "properties": {
                                    "cnr_id": "comfy-core",
                                    "ver": "0.3.40",
                                    "Node name for S&R": "CLIPTextEncode",
                                },
                                "widgets_values": [
                                    "score_4,score_5,score_6,lowres,low quality,ugly,deformed,bad anatomy,extra fingers,username,text,logo,watermark,cross-eyed,censored,muscular,(chains:1.2),bad teeth,crooked teeth,discolored teeth,deformed teeth,bad feet,deformed feet,extra toes"
                                ],
                            },
                            {
                                "id": 3,
                                "type": "KSampler",
                                "pos": [863, 186],
                                "size": [315, 262],
                                "flags": {},
                                "order": 6,
                                "mode": 0,
                                "inputs": [
                                    {"name": "model", "type": "MODEL", "link": 13},
                                    {
                                        "name": "positive",
                                        "type": "CONDITIONING",
                                        "link": 4,
                                    },
                                    {
                                        "name": "negative",
                                        "type": "CONDITIONING",
                                        "link": 6,
                                    },
                                    {
                                        "name": "latent_image",
                                        "type": "LATENT",
                                        "link": 11,
                                    },
                                ],
                                "outputs": [
                                    {
                                        "name": "LATENT",
                                        "type": "LATENT",
                                        "slot_index": 0,
                                        "links": [7],
                                    }
                                ],
                                "properties": {
                                    "cnr_id": "comfy-core",
                                    "ver": "0.3.40",
                                    "Node name for S&R": "KSampler",
                                },
                                "widgets_values": [
                                    710512989952594,
                                    "randomize",
                                    40,
                                    7,
                                    "dpmpp_3m_sde",
                                    "karras",
                                    0.8700000000000001,
                                ],
                            },
                            {
                                "id": 10,
                                "type": "LoadImage",
                                "pos": [166.07955932617188, 678.5671997070312],
                                "size": [315, 314.0000305175781],
                                "flags": {},
                                "order": 2,
                                "mode": 0,
                                "inputs": [],
                                "outputs": [
                                    {
                                        "name": "IMAGE",
                                        "type": "IMAGE",
                                        "slot_index": 0,
                                        "links": [10],
                                    },
                                    {"name": "MASK", "type": "MASK", "links": null},
                                ],
                                "properties": {
                                    "cnr_id": "comfy-core",
                                    "ver": "0.3.40",
                                    "Node name for S&R": "LoadImage",
                                },
                                "widgets_values": ["2.jpg", "image"],
                                "color": "#322",
                                "bgcolor": "#533",
                            },
                            {
                                "id": 6,
                                "type": "CLIPTextEncode",
                                "pos": [415, 186],
                                "size": [422.84503173828125, 164.31304931640625],
                                "flags": {},
                                "order": 3,
                                "mode": 0,
                                "inputs": [
                                    {"name": "clip", "type": "CLIP", "link": 14}
                                ],
                                "outputs": [
                                    {
                                        "name": "CONDITIONING",
                                        "type": "CONDITIONING",
                                        "slot_index": 0,
                                        "links": [4],
                                    }
                                ],
                                "properties": {
                                    "cnr_id": "comfy-core",
                                    "ver": "0.3.40",
                                    "Node name for S&R": "CLIPTextEncode",
                                },
                                "widgets_values": ["Keep Face"],
                            },
                            {
                                "id": 18,
                                "type": "SaveImage",
                                "pos": [1421.4464111328125, 330.1094055175781],
                                "size": [620, 360],
                                "flags": {},
                                "order": 8,
                                "mode": 0,
                                "inputs": [
                                    {"name": "images", "type": "IMAGE", "link": 19}
                                ],
                                "outputs": [],
                                "properties": {"cnr_id": "comfy-core", "ver": "0.3.40"},
                                "widgets_values": ["ComfyUI"],
                            },
                        ],
                        "links": [
                            [4, 6, 0, 3, 1, "CONDITIONING"],
                            [6, 7, 0, 3, 2, "CONDITIONING"],
                            [7, 3, 0, 8, 0, "LATENT"],
                            [10, 10, 0, 12, 0, "IMAGE"],
                            [11, 12, 0, 3, 3, "LATENT"],
                            [13, 14, 0, 3, 0, "MODEL"],
                            [14, 14, 1, 6, 0, "CLIP"],
                            [15, 14, 1, 7, 0, "CLIP"],
                            [16, 14, 2, 12, 1, "VAE"],
                            [17, 14, 2, 8, 1, "VAE"],
                            [19, 8, 0, 18, 0, "IMAGE"],
                        ],
                        "groups": [
                            {
                                "id": 1,
                                "title": "Loading images",
                                "bounding": [
                                    124.6132583618164,
                                    595.794921875,
                                    700.1656494140625,
                                    414.9020080566406,
                                ],
                                "color": "#3f789e",
                                "font_size": 24,
                                "flags": {},
                            }
                        ],
                        "config": {},
                        "extra": {
                            "ds": {
                                "scale": 0.6209213230591554,
                                "offset": [-369.7833483035314, 53.19197650145743],
                            },
                            "frontendVersion": "1.21.7",
                        },
                        "version": 0.4,
                    }
                },
            },
        }
    }
