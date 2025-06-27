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
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"}
            },
            "4": {
                "inputs": {
                    "ckpt_name": "4T.safetensors"
                },
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"}
            },
            "5": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage",
                "_meta": {"title": "Empty Latent Image"}
            },
            "6": {
                "inputs": {
                    "text": positive_prompt,
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"}
            },
            "7": {
                "inputs": {
                    "text": "score_4,score_5,score_6,lowres,low quality,ugly,deformed,bad anatomy,extra fingers,username,text,logo,watermark,cross-eyed,censored,muscular,(chains:1.2),bad teeth,crooked teeth,discolored teeth,deformed teeth,bad feet,deformed feet,extra toes",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"}
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"}
            },
            "12": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "_meta": {"title": "Save Image"}
            }
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
                                {"label": "Mô hình", "name": "MODEL", "type": "MODEL", "slot_index": 0, "links": [1]},
                                {"label": "CLIP", "name": "CLIP", "type": "CLIP", "slot_index": 1, "links": [3, 5]},
                                {"label": "VAE", "name": "VAE", "type": "VAE", "slot_index": 2, "links": [8]}
                            ],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.18", "Node name for S&R": "CheckpointLoaderSimple"},
                            "widgets_values": ["4T.safetensors"]
                        },
                        {
                            "id": 7,
                            "type": "CLIPTextEncode",
                            "pos": [413, 389],
                            "size": [425.27801513671875, 180.6060791015625],
                            "flags": {},
                            "order": 3,
                            "mode": 0,
                            "inputs": [{"label": "CLIP", "name": "clip", "type": "CLIP", "link": 5}],
                            "outputs": [{"label": "Điều kiện", "name": "CONDITIONING", "type": "CONDITIONING", "slot_index": 0, "links": [6]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.18", "Node name for S&R": "CLIPTextEncode"},
                            "widgets_values": [
                                "score_4,score_5,score_6,lowres,low quality,ugly,deformed,bad anatomy,extra fingers,username,text,logo,watermark,cross-eyed,censored,muscular,(chains:1.2),bad teeth,crooked teeth,discolored teeth,deformed teeth,bad feet,deformed feet,extra toes"
                            ]
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
                                {"label": "Mô hình", "name": "model", "type": "MODEL", "link": 1},
                                {"label": "Điều kiện tích cực", "name": "positive", "type": "CONDITIONING", "link": 4},
                                {"label": "Điều kiện tiêu cực", "name": "negative", "type": "CONDITIONING", "link": 6},
                                {"label": "Tiềm ẩn", "name": "latent_image", "type": "LATENT", "link": 2}
                            ],
                            "outputs": [{"label": "Tiềm ẩn", "name": "LATENT", "type": "LATENT", "slot_index": 0, "links": [7]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.18", "Node name for S&R": "KSampler"},
                            "widgets_values": [random_13_digits(), "randomize", 40, 7, "dpmpp_3m_sde", "karras", 1]
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
                                {"label": "Tiềm ẩn", "name": "samples", "type": "LATENT", "link": 7},
                                {"label": "VAE", "name": "vae", "type": "VAE", "link": 8}
                            ],
                            "outputs": [{"label": "Hình ảnh", "name": "IMAGE", "type": "IMAGE", "slot_index": 0, "links": [11]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.18", "Node name for S&R": "VAEDecode"},
                            "widgets_values": []
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
                            "widgets_values": ["ComfyUI"]
                        },
                        {
                            "id": 6,
                            "type": "CLIPTextEncode",
                            "pos": [415, 186],
                            "size": [422.84503173828125, 164.31304931640625],
                            "flags": {},
                            "order": 2,
                            "mode": 0,
                            "inputs": [{"label": "CLIP", "name": "clip", "type": "CLIP", "link": 3}],
                            "outputs": [{"label": "Điều kiện", "name": "CONDITIONING", "type": "CONDITIONING", "slot_index": 0, "links": [4]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.18", "Node name for S&R": "CLIPTextEncode"},
                            "widgets_values": [positive_prompt]
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
                            "outputs": [{"label": "Tiềm ẩn", "name": "LATENT", "type": "LATENT", "slot_index": 0, "links": [2]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.18", "Node name for S&R": "EmptyLatentImage"},
                            "widgets_values": [width, height, 1]
                        }
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
                        [11, 8, 0, 12, 0, "IMAGE"]
                    ],
                    "groups": [],
                    "config": {},
                    "extra": {
                        "ds": {
                            "scale": 0.9229599817706574,
                            "offset": [78.93082093649174, -78.77906810733931]
                        },
                        "VHS_latentpreview": False,
                        "VHS_latentpreviewrate": 0,
                        "VHS_MetadataImage": True,
                        "VHS_KeepIntermediate": True,
                        "frontendVersion": "1.21.7"
                    },
                    "version": 0.4
                }
            }
        }
    }
